from openai import OpenAI
from models import ALL_INTENTS, PRODUCT_ANALYTICS

SYSTEM_PROMPT = f"""
Classify the user's analytics question into one or more intents from:
{", ".join(ALL_INTENTS)}.

Return ONLY a comma-separated list of labels.
No extra text.

Guidance:
- BUSINESS_STRATEGY: business decision framing, unit economics, KPI tradeoffs, strategy/ROI
- PRODUCT_ANALYTICS: funnels, cohorts, segmentation, experimentation, product metrics
- SQL_INVESTIGATION: request for SQL, queries, table-level computations

If unsure, return {PRODUCT_ANALYTICS}.
""".strip()

def classify_intent(client: OpenAI, question: str):
    resp = client.chat.completions.create(
        model="gpt-4.0-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question.strip()},
        ],
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "").strip()
    intents = [i.strip().upper() for i in raw.split(",") if i.strip()]
    filtered = [i for i in intents if i in ALL_INTENTS]
    return filtered or [PRODUCT_ANALYTICS]