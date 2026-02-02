import json
from openai import OpenAI
from config import OPENAI_MODEL

SYSTEM_PROMPT = """
You are an expert Auditor of AI responses. 
Your job is to grade the 'Confidence' of an AI's answer from 0.0 to 1.0.

### SCORING CRITERIA:
1. **1.0 (Certainty)**: The answer uses SPECIFIC column names AND SPECIFIC data values found in the provided schema (e.g., using "WHERE status = 'churned'" when 'churned' is in the schema examples).
2. **0.8 (High)**: Good logic and valid SQL, but might be slightly generic.
3. **0.5 (Medium)**: The answer is generic "Standard Advice" or hedges ("Assuming you have a column...").
4. **0.1 (Low)**: Hallucinated columns, wrong logic, or refuses to answer.

### INPUT DATA:
- **User Question**: The user's query.
- **Agent Output**: The response to grade.
- **Intent**: The agent type (SQL, Strategy, Product).
- **Schema Context**: The actual database structure and sample values.

Output JSON: {"score": float, "rationale": "Short explanation"}
"""

def get_confidence(client, question, output, intent, schema=None):
    """
    Calculates confidence. 
    Crucially, it now takes 'schema' as an input so it can verify facts.
    """
    try:
        # Convert schema to string for the prompt
        schema_str = json.dumps(schema, indent=2) if schema else "No Schema Provided"

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"""
                User Question: {question}
                Intent: {intent}
                Schema Context: {schema_str}
                
                Agent Output: {output}
                """}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        return {"score": 0.5, "rationale": "Error calculating confidence."}