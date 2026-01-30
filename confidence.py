import json
from openai import OpenAI

# 1. SQL RUBRIC: Strict on correctness, lenient on style
SQL_RUBRIC = """
Evaluate the SQL code quality.
- 1.0 (Perfect): Syntax is correct, uses actual table/column names from the prompt (if provided), and logic perfectly matches the question.
- 0.8 (Good): Logically correct but might assume a column name if schema wasn't fully clear.
- 0.5 (Weak): Generic SQL (e.g., SELECT * FROM table) that doesn't target the specific question.
- 0.1 (Fail): Not SQL, or completely hallucinated schema when a schema was provided.
"""

# 2. ANALYSIS RUBRIC: Rewards specificity, punishes fluff
ANALYSIS_RUBRIC = """
Evaluate the analytical advice.
- 1.0 (Excellent): Highly specific to the user's question. Defines exact metrics, segments, or hypothesis tests. If data is missing, it precisely identifies *what* data is needed to proceed.
- 0.8 (Strong): Good strategic thinking (e.g., AARRR framework), but some recommendations are slightly generic.
- 0.5 (Average): "Consultant Fluff" — generic advice like "improve retention" or "optimize marketing" without saying HOW.
- 0.1 (Poor): Irrelevant to the specific question asked.
"""

SYSTEM_TEMPLATE = """
You are an impartial technical judge. Score the AI's response based on how well it answers the User's Question.

User Question: {question}
Intent: {intent}
AI Response: {output}

SCORING STANDARDS:
{rubric}

INSTRUCTIONS:
- **Be Unbiased:** Do not artificially cap scores. If an answer is the best possible answer given the limited context, it deserves a 0.9 or 1.0.
- **Reward Honesty:** If the AI correctly lists "Missing Information" that is crucial for the answer, treat that as a POSITIVE (high quality), not a negative.
- **Penalize Hallucination:** If the AI makes up data or column names that don't exist, score < 0.4.

Return STRICT JSON only:
{{"confidence": 0.0, "rationale": "One specific reason for this score."}}
"""

def get_confidence(client: OpenAI, question: str, output: str, intent: str) -> dict:
    
    # Select the rubric based on intent
    if intent == "SQL_INVESTIGATION":
        selected_rubric = SQL_RUBRIC
    else:
        # Business and Product share the "Analysis" rubric
        selected_rubric = ANALYSIS_RUBRIC

    formatted_prompt = SYSTEM_TEMPLATE.format(
        question=question,
        intent=intent,
        output=output[:4000],
        rubric=selected_rubric
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
    
    # Strip markdown if present
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        obj = json.loads(raw)
        c = float(obj.get("confidence", 0.5))
        r = obj.get("rationale", "No rationale provided.")
        return {"score": max(0.0, min(1.0, c)), "rationale": r}
    except Exception:
        return {"score": 0.5, "rationale": "Confidence scoring failed to parse."}