import json
from config import OPENAI_MODEL  # <--- Ensure this import exists
from models import BUSINESS_STRATEGY, PRODUCT_ANALYTICS, SQL_INVESTIGATION

ROUTER_PROMPT = """
You are the Intent Classifier for an Analytics AI. 
...
"""

def classify_intent(client, question: str):
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,  # <--- Uses the variable from config.py
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": question}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("intents", [])
    except Exception as e:
        print(f"Router Error: {e}")
        return [BUSINESS_STRATEGY]