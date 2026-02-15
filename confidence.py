import json
import re
from config import OPENAI_MODEL

SYSTEM_PROMPT = """
You are an expert Auditor of AI responses. 
Your job is to evaluate the 'Confidence' of an AI's answer.

### PHILOSOPHY:
**Confidence** = **Certainty in Truth**, not just "Success".
If the AI correctly refuses a request because data is missing, that is **HIGH CONFIDENCE (High)**.

### SCORING TIERS:

**1.0 (High Confidence - Green)**
- **Verified Truth:** The answer uses proven facts from the Schema.
- **Verified Refusal:** The agent explicitly states "I cannot analyze X because column Y is missing" (and Y is indeed missing).
- **Pinpoint:** "Verified against schema."

**0.5 (Medium Confidence - Yellow)**
- **Generalization:** Valid advice, but not linked to specific data columns.
- **Assumptions:** "Assuming you have a date column..."
- **Pinpoint:** "Advice is generic; no specific columns referenced."

**0.1 (Low Confidence - Red)**
- **Hallucination:** claims to use columns that do not exist.
- **Pinpoint:** "Hallucinated column 'device_type' which does not exist."

### INPUT DATA:
- **User Question**: {question}
- **Intent**: {intent}
- **Schema Context**: {schema}
- **Agent Output**: {output}

### OUTPUT FORMAT:
Return JSON with:
1. `score`: float (1.0, 0.5, or 0.1)
2. `rationale`: string. **CRITICAL:** If score < 1.0, pinpoint the EXACT missing data or vague term that caused the drop. (e.g., "Missing 'referral_source' column.").

Output JSON: {{"score": float, "rationale": "Pinpoint explanation"}}
"""

def clean_json_string(json_str: str) -> str:
    """Removes markdown backticks if present."""
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
        
        content = response.choices[0].message.content
        cleaned_content = clean_json_string(content)
        return json.loads(cleaned_content)
        
    except Exception as e:
        print(f"Confidence Error: {e}")
        return {
            "score": 0.5, 
            "rationale": "Auditor failed to verify response."
        }