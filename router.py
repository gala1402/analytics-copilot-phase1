from openai import OpenAI
from models import ALL_INTENTS, PRODUCT_ANALYTICS

SYSTEM_PROMPT = f"""
You are the gatekeeper for a Senior Analytics Copilot. 
Classify the user's question into one or more: {", ".join(ALL_INTENTS)}.

If the user is:
1. Asking for help with analytics, data, SQL, or business strategy -> Categorize it.
2. Asking what you can do/capabilities -> Return 'CAPABILITIES'.
3. Asking about unrelated topics (cooking, travel, general chat, etc.) -> Return 'OUT_OF_SCOPE'.

Return ONLY a comma-separated list of labels.
"""

def classify_intent(client: OpenAI, question: str):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": question}],
        temperature=0,
    )
    raw = (resp.choices[0].message.content or "").strip().upper()
    
    if "OUT_OF_SCOPE" in raw:
        return ["OUT_OF_SCOPE"]
    if "CAPABILITIES" in raw:
        return ["CAPABILITIES"]
        
    intents = [i.strip() for i in raw.split(",") if i.strip() in ALL_INTENTS]
    return intents or [PRODUCT_ANALYTICS]