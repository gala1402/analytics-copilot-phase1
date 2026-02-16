import json
from openai import OpenAI
from models import SQL_INVESTIGATION

CLARIFIER_SYSTEM_PROMPT = """
You decide whether clarification is required BEFORE analysis.

Inputs:
- user_question
- detected_intents
- dataset_schema (may be null)

Rules:
- If SQL_INVESTIGATION is present and dataset_schema is null, MUST require clarification.
- If time windows are vague ("last quarter", "recent", "this month"), ask for exact definition.
- If key metrics are undefined ("churn", "engagement", "conversion"), ask how they are defined.

Output STRICT JSON only:
{
  "needs_clarification": true/false,
  "questions": ["...", "..."]
}
No markdown. No extra text.
""".strip()

def get_clarification(client: OpenAI, question: str, intents: list[str], schema):
    payload = {
        "user_question": question,
        "detected_intents": intents,
        "dataset_schema": schema,
    }

    resp = client.chat.completions.create(
        model="gpt-4.0-mini",
        messages=[
            {"role": "system", "content": CLARIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload)},
        ],
        temperature=0,
    )

    raw = (resp.choices[0].message.content or "").strip()

    try:
        result = json.loads(raw)
        needs = bool(result.get("needs_clarification", False))
        questions = result.get("questions", [])
        if not isinstance(questions, list):
            questions = []

        # enforce server-side rule too
        if (SQL_INVESTIGATION in intents) and (schema is None):
            needs = True
            if not questions:
                questions = [
                    "You asked for SQL—please upload a CSV dataset (or provide the schema: tables + columns) so I can generate grounded SQL."
                ]

        return {"needs_clarification": needs, "questions": questions[:3]}
    except Exception:
        fallback = []
        if (SQL_INVESTIGATION in intents) and (schema is None):
            fallback.append("You asked for SQL—please upload a CSV dataset (or provide tables + columns) so I can generate grounded SQL.")
        fallback.extend([
            "How is the key metric defined in your context (e.g., churn/engagement/conversion)—which column or rule should be used?",
            "What exact time window should I use (exact start/end dates or calendar vs fiscal definition)?",
        ])
        return {"needs_clarification": True, "questions": fallback[:3]}