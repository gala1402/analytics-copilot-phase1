import json
from config import OPENAI_MODEL

SYSTEM_PROMPT = """
You are an expert Auditor of AI responses. 
Your job is to grade the 'Confidence' of an AI's answer from 0.0 to 1.0 based on the INTENT.

### RUBRIC BY INTENT:

**1. FOR INTENT: "business_strategy" OR "product_analytics"**
- **1.0 (High)**: The analysis references SPECIFIC data values or columns from the schema (e.g., mentioning "Pro Plan" or "Status column"). It gives tailored advice. **(NOTE: It does NOT need to write SQL code to get a 1.0).**
- **0.5 (Medium)**: The advice is relevant but generic (e.g., "Improve onboarding") and doesn't explicitly reference the specific dataset provided.
- **0.1 (Low)**: Hallucination or off-topic.

**2. FOR INTENT: "sql_investigation"**
- **1.0 (High)**: Generates valid SQL using EXACT column names and values from the schema.
- **0.5 (Medium)**: Generates SQL but hedges ("Assuming you have a table...").
- **0.1 (Low)**: Uses incorrect syntax or hallucinated columns.

### INPUT DATA:
- **User Question**: The full user query.
- **Intent**: The specific job this agent was assigned (e.g., "business_strategy").
- **Agent Output**: The response to grade.
- **Schema Context**: The available data structure.

**IMPORTANT:** Do NOT penalize a Strategy agent for missing SQL, or a SQL agent for missing Strategy. Grade them only on their assigned Intent.

Output JSON: {"score": float, "rationale": "Short explanation"}
"""

def get_confidence(client, question, output, intent, schema=None):
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
        return {"score": 0.5, "rationale": f"Error calculating confidence: {e}"}