from openai import OpenAI
from models import ALL_INTENTS, PRODUCT_ANALYTICS

SYSTEM_PROMPT = f"""
Classify the user's analytics question into one or more intents from:
{", ".join(ALL_INTENTS)}.

If the request is unrelated to business, data, or analytics, return 'OUT_OF_SCOPE'.

Guidance:
- BUSINESS_STRATEGY: Strategy, ROI, unit economics, KPI tradeoffs.
- PRODUCT_ANALYTICS: Funnels, cohorts, segmentation, experiment design.
- SQL_INVESTIGATION: Specific requests for database queries/code.
- VISUALIZATION: Requests for charts, graphs, or visual trends.

Return ONLY a comma-separated list of labels. No extra text.
""".strip()

def classify_intent(client: OpenAI, question: str):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question.strip()},
        ],
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "").strip().upper()
    if "OUT_OF_SCOPE" in raw:
        return ["OUT_OF_SCOPE"]
        
    intents = [i.strip() for i in raw.split(",") if i.strip() in ALL_INTENTS]
    return intents or [PRODUCT_ANALYTICS]