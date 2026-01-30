import json
from openai import OpenAI

CONF_SYSTEM = """
You are a strict evaluator of analytics answer quality.

Score confidence from 0.0 to 1.0 based on:
- Grounding: uses provided schema/definitions vs guessing
- Completeness: addresses the question with actionable specifics
- Assumptions: penalize missing key inputs and vague claims

Rules:
- If the answer lists "missing information needed", confidence must be <= 0.85.
- If SQL is requested but schema is missing/blocked, confidence must be <= 0.75.
- Do NOT return 1.0 unless there are no meaningful assumptions.

Return STRICT JSON only:
{"confidence": 0.0, "rationale": "short reason"}
""".strip()

def get_confidence(client: OpenAI, output: str) -> dict:
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": CONF_SYSTEM},
            {"role": "user", "content": output[:7000]},
        ],
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "").strip()
    try:
        obj = json.loads(raw)
        c = float(obj.get("confidence", 0.5))
        r = obj.get("rationale", "No rationale provided.")
        return {"score": max(0.0, min(1.0, c)), "rationale": r}
    except Exception:
        return {"score": 0.5, "rationale": "Parsing error in confidence scoring."}