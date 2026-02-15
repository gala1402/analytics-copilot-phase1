import json
from openai import OpenAI

CONF_SYSTEM = """
You are a strict evaluator of analytics answer quality.
Score confidence from 0.0 to 1.0 based on grounding and completeness.
Return STRICT JSON only: {"confidence": 0.0, "rationale": "reason"}
""".strip()

def get_confidence(client: OpenAI, output: str) -> float:
    # BUG FIX: Handle empty or non-string input
    if not output or not isinstance(output, str):
        return 0.0
    
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": CONF_SYSTEM},
                {"role": "user", "content": output[:5000]}, # Protect against token limits
            ],
            temperature=0,
        )
        raw = (resp.choices[0].message.content or "").strip()
        
        # Robust JSON extraction
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        
        obj = json.loads(raw)
        c = float(obj.get("confidence", 0.5))
        return max(0.0, min(1.0, c))
    except Exception as e:
        print(f"Confidence calculation error: {e}")
        return 0.5 # Safe fallback