import json
import re
from config import OPENAI_MODEL

SYSTEM_PROMPT = """
You are an expert Auditor of AI responses. 
Your job is to grade the 'Confidence' of an AI's answer on a scale from 0.0 to 1.0.

### SCORING RUBRIC:

**1.0 (Perfect / Certain)**
- The answer is **Flawless**. It uses exact column names and values from the schema.
- For Code: The SQL is syntactically perfect and runs against the schema.
- For Strategy: The advice is highly specific to the business context provided.

**0.9 (Excellent - Safe Partial Success)**
- **CRITICAL USE CASE:** If the user asks for two things (e.g., "Calculate MRR" AND "Analyze iOS"), and the Agent correctly answers the possible part (MRR) while safely refusing the impossible part (iOS), **this is a 0.9**.
- The Agent correctly identified a limitation in the data and did not hallucinate. This is "High Confidence" behavior.

**0.7 (Good - Generic but Valid)**
- The answer is correct but generic.
- Example: "To improve retention, try email campaigns" (Valid advice, but not specific to the dataset).
- Example: "I assume you have a 'date' column" (Reasonable assumption, but not grounded in schema).

**0.5 (Caution - Hedging)**
- The answer is mostly hedging ("It depends...", "I'm not sure...").
- The SQL looks plausible but uses columns that might not exist.

**0.1 (Fail - Hallucination)**
- The answer uses columns that definitively DO NOT exist.
- The logic is completely flawed or off-topic.

### INPUT DATA:
- **User Question**: {question}
- **Intent**: {intent}
- **Schema Context**: {schema}
- **Agent Output**: {output}

Output JSON: {{"score": float, "rationale": "One sentence explanation"}}
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
        
        # Safe Prompting
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
            "rationale": "Auditor failed to grade response (Fallback)."
        }