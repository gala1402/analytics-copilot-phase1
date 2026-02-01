import json
from openai import OpenAI

# 1. SCOPE DEFINITIONS
SCOPE_DEFINITIONS = {
    "BUSINESS_STRATEGY": """
    JOB: Provide specific strategic advice based on the user's stated constraints.
    CONSTRAINT: Must NOT write SQL.
    SUCCESS: Advice must be tailored to the specific industry/problem. 
    FAIL: Generic advice (e.g., "reduce costs", "improve marketing") is a FAILURE, even if formatted nicely.
    """,
    
    "PRODUCT_ANALYTICS": """
    JOB: Define specific metrics and experiments.
    SUCCESS: Mentions concrete metrics (e.g., 'Day-30 Retention').
    FAIL: Vague terms like "measure engagement" without definition.
    """,
    
    "SQL_INVESTIGATION": """
    JOB: Write executable SQL.
    SUCCESS: Valid syntax, correct columns.
    FAIL: Hallucinated columns or invalid syntax.
    """
}

# 2. THE SYSTEM PROMPT
SYSTEM_TEMPLATE = """
You are a strict specialized Auditor. Grade the response 0.0 to 1.0.

CURRENT ROLE: {intent}
{scope_definition}

User Question: {question}
AI Response: {output}

SCORING RULES:
1. **The "Consultant Fluff" Penalty:**
   - If the advice is generic (e.g., "Analyze customer feedback", "Optimize pricing") and could apply to ANY company, the **MAXIMUM SCORE is 0.5**.
   - This applies **EVEN IF** the AI lists "Missing Information". Honesty does not excuse lack of substance.

2. **The "Specifics" Reward:**
   - Score > 0.8 ONLY if the answer contains *specific* numbers, distinct table names, or industry-specific tactics (e.g., "Penetration Pricing" for a startup).

3. **Hallucination Check:**
   - If the AI invents data or columns that weren't provided -> Score 0.1.

Return STRICT JSON only:
{{"confidence": 0.0, "rationale": "One sentence explaining why it is specific or generic."}}
"""

def get_confidence(client: OpenAI, question: str, output: str, intent: str) -> dict:
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
        return {"score": 0.5, "rationale": "Confidence scoring failed."}