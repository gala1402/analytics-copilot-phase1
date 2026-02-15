# clarifier.py
import json
from config import OPENAI_MODEL

CLARIFIER_PROMPT = """
You are a "Clarification Engine".
Your job is to decide if a request is clear enough to proceed.

### CRITICAL RULES:

1. **THE "NO DATA" GATE**
   - IF `Schema` is "No Schema Provided" AND the intent implies data analysis:
   - **RETURN `needs_clarification: true`.**
   - Question: "I cannot run an analysis because no dataset has been uploaded. Please upload a CSV file."

2. **SMART INFERENCE (Do Not Ask)**
   - IF the user mentions "churn" and you see `status='churned'` in the schema -> **Proceed.**
   - IF the user asks for "Pro users" and you see `plan_type='Pro'` -> **Proceed.**

3. **GENUINE AMBIGUITY (Ask)**
   - Only ask if a term has NO matching column or value.

### INPUT DATA:
- Question: {question}
- Schema: {schema}

Output JSON: {{"needs_clarification": boolean, "questions": ["String"]}}
"""

def get_clarification(client, question, intents, schema=None):
    try:
        schema_str = json.dumps(schema, indent=2) if schema else "No Schema Provided"
        
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": CLARIFIER_PROMPT.format(
                    question=question, 
                    intents=str(intents), 
                    schema=schema_str
                )}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception:
        return {"needs_clarification": False}