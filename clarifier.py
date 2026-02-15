import json
from openai import OpenAI
from models import SQL_INVESTIGATION, VISUALIZATION

CLARIFIER_SYSTEM_PROMPT = """
Decide if clarification is needed BEFORE analysis.
Rules:
1. If SQL_INVESTIGATION or VISUALIZATION is requested but schema is null, MUST ask for data.
2. If metrics like "churn" or "engagement" are used without definition, ask for the rule.
3. If the time window is vague, ask for specific dates.

Output STRICT JSON:
{"needs_clarification": true/false, "questions": ["...", "..."]}
"""

def get_clarification(client: OpenAI, question: str, intents: list[str], schema):
    payload = {"user_question": question, "intents": intents, "schema": schema}
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": CLARIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload)},
        ],
        temperature=0,
    )
    try:
        result = json.loads(resp.choices[0].message.content)
        # Force clarification if data-dependent intents are present without a schema
        if (SQL_INVESTIGATION in intents or VISUALIZATION in intents) and schema is None:
            result["needs_clarification"] = True
            result["questions"].append("Please upload a CSV file so I can access the data columns.")
        return result
    except:
        return {"needs_clarification": False, "questions": []}