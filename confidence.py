# confidence.py
import json
from config import OPENAI_MODEL

SYSTEM_PROMPT = """
You are an expert Auditor of AI responses. 
Your job is to evaluate the 'Confidence' of an AI's answer.

### PHILOSOPHY:
**Confidence** = **Certainty in Truth**.
If the AI correctly refuses a request because data is missing, that is **HIGH CONFIDENCE (High)**.

### SCORING TIERS:

**1.0 (High Confidence)**
- **Verified Truth:** Uses proven facts from the Schema.
- **Verified Refusal:** Explicitly states "I cannot analyze X because column Y is missing" (and Y is indeed missing).

**0.5 (Medium Confidence)**
- **Generalization:** Valid advice, but not linked to specific data columns.
- **Assumptions:** "Assuming you have a date column..."

**0.1 (Low Confidence)**
- **Hallucination:** Claims to use columns that do not exist.

### OUTPUT FORMAT:
Return JSON with:
1. `score`: float (1.0, 0.5, or 0.1)
2. `rationale`: string. **CRITICAL:** If score < 1.0, pinpoint the EXACT missing data or vague term. (e.g., "Missing 'device' column.").

Output JSON: {{"score": float, "rationale": "Pinpoint explanation"}}
"""

def clean_json_string(json_str: str) -> str:
    if "```json" in json_str:
        json_str = json_str.split("```json")[1].split("```")[0]
    elif "```" in json_str:
        json_str = json_str.split("```")[1].split("```")[0]
    return json_str.strip()

def get_confidence(client, question, output, intent, schema=None):
    try:
        schema_str = json.dumps(schema, indent=2) if schema else "No Schema Provided"
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(
                    question=question, 
                    intent=intent, 
                    schema=schema_str, 
                    output=output
                )}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        content = clean_json_string(response.choices[0].message.content)
        return json.loads(content)
    except Exception as e:
        print(f"Confidence Error: {e}")
        return {"score": 0.5, "rationale": "Auditor failed to verify response."}