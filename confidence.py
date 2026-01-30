import json
from openai import OpenAI

CONF_SYSTEM = """
You are a strict technical auditor. Grade the following analytics response on a scale of 0.0 to 1.0.

User Question: {question}
AI Response: {output}

Scoring Rubric:
- 1.0: Perfect, definitive answer using actual data/SQL (no placeholders).
- 0.9: Strong answer but relies on general strategic frameworks (AARRR, etc.).
- 0.8: Good answer, but explicitly lists "Missing Information" or "Assumptions".
- 0.5: Vague, generic advice that applies to any company (e.g., "Check churn metrics").
- 0.1: Refusal to answer or completely unrelated.

Rules:
- If the response contains "Missing Information Needed" or similar bullet points, MAX SCORE is 0.85.
- If the user asked for SQL but the response is just text (no code), MAX SCORE is 0.3.
- Be harsh. Do not give 1.0 easily.

Return STRICT JSON:
{{"confidence": 0.0, "rationale": "One sentence explanation"}}
""".strip()

def get_confidence(client: OpenAI, question: str, output: str) -> dict:
    # We inject the specific Q and A into the system prompt structure
    formatted_system_prompt = CONF_SYSTEM.format(
        question=question, 
        output=output[:4000] # Truncate to save tokens
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a strict evaluator. Output JSON only."},
            {"role": "user", "content": formatted_system_prompt},
        ],
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "").strip()
    
    # Handle markdown code blocks if the LLM wraps JSON in ```json ... ```
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        obj = json.loads(raw)
        c = float(obj.get("confidence", 0.5))
        r = obj.get("rationale", "No rationale provided.")
        return {"score": max(0.0, min(1.0, c)), "rationale": r}
    except Exception:
        return {"score": 0.5, "rationale": "Confidence scoring failed to parse."}