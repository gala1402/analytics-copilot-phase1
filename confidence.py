import json
from openai import OpenAI

# 1. SCOPE DEFINITIONS (The "Job Descriptions")
SCOPE_DEFINITIONS = {
    "BUSINESS_STRATEGY": """
    JOB: Provide decision framing, unit economics, KPI tradeoffs, and high-level strategy.
    CONSTRAINT: Must NOT write SQL code. Must NOT do deep technical product work (funnels).
    SUCCESS: A great answer is strategic, logical, and identifies the right levers (e.g., Pricing, Market Fit).
    """,
    
    "PRODUCT_ANALYTICS": """
    JOB: Provide hypotheses, define metrics, design funnels, and suggest experiments (A/B tests).
    CONSTRAINT: Must NOT write SQL code. Must NOT discuss high-level budget strategy.
    SUCCESS: A great answer defines concrete metrics (e.g., 'Day-7 Retention') and specific user journey steps.
    """,
    
    "SQL_INVESTIGATION": """
    JOB: Write accurate, executable SQL code based on the user's schema.
    CONSTRAINT: Must NOT write long essays on business strategy.
    SUCCESS: A great answer is VALID SQL that uses the correct table/column names.
    """
}

# 2. THE SYSTEM PROMPT
SYSTEM_TEMPLATE = """
You are a specialized Quality Assurance Auditor. Your goal is to grade the AI's response based STRICTLY on its assigned role.

CURRENT ROLE: {intent}
{scope_definition}

User Question: {question}
AI Response: {output}

SCORING RULES:
1. **Stay in Lane:** Do NOT penalize the AI for missing parts that belong to other roles.
   - Example: If the role is BUSINESS_STRATEGY, do *not* deduct points for missing SQL.
   - Example: If the role is SQL_INVESTIGATION, do *not* deduct points for missing business advice.

2. **Grade the Content:**
   - 1.0 (Perfect): Perfect execution of the specific role. High specificity.
   - 0.8 (Good): Solid answer, maybe slightly generic but accurate.
   - 0.5 (Weak): Vague advice or generic SQL (e.g., SELECT *).
   - 0.1 (Fail): Hallucinated data or refusal to answer.

3. **Missing Info:**
   - If the AI correctly identifies that critical data is missing (e.g., "I need a 'revenue' column to calculate ROI"), this is a POSITIVE feature. Give it a high score (0.9+).

Return STRICT JSON only:
{{"confidence": 0.0, "rationale": "One sentence explanation focused on the specific role."}}
"""

def get_confidence(client: OpenAI, question: str, output: str, intent: str) -> dict:
    
    # Get the specific job description for this intent
    scope_def = SCOPE_DEFINITIONS.get(intent, "JOB: Answer the analytics question.")

    formatted_prompt = SYSTEM_TEMPLATE.format(
        question=question,
        intent=intent,
        scope_definition=scope_def,
        output=output[:4000]
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a strict evaluator. Output JSON only."},
            {"role": "user", "content": formatted_prompt},
        ],
        temperature=0,
    )
    
    raw = (resp.choices[0].message.content or "").strip()
    
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        obj = json.loads(raw)
        c = float(obj.get("confidence", 0.5))
        r = obj.get("rationale", "No rationale provided.")
        return {"score": max(0.0, min(1.0, c)), "rationale": r}
    except Exception:
        return {"score": 0.5, "rationale": "Confidence scoring failed to parse."}