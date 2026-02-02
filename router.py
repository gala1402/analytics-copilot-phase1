import json
from config import OPENAI_MODEL
from models import BUSINESS_STRATEGY, PRODUCT_ANALYTICS, SQL_INVESTIGATION

ROUTER_PROMPT = """
You are the Intent Classifier for an Analytics AI. 
Your job is to map a user's request to one or more specialized agents.

### AVAILABLE AGENTS:
1. **SQL_INVESTIGATION**: 
   - Keywords: "calculate", "count", "list", "show", "query", "pull", "how many", "average", "sum".
   - Trigger: ANY request that requires retrieving or aggregating raw numbers from a database. 
   - **CRITICAL:** If the user asks for a number (e.g. "Calculate MRR"), you MUST include this intent, even if they also ask for strategy.

2. **PRODUCT_ANALYTICS**:
   - Keywords: "churn", "retention", "behavior", "usage", "funnel", "cohort", "engagement".
   - Trigger: Questions about user behavior, product performance, or specific metrics.

3. **BUSINESS_STRATEGY**:
   - Keywords: "impact", "why", "suggest", "plan", "campaign", "revenue", "advice".
   - Trigger: High-level business questions, marketing ideas, or requests for qualitative advice.

### INSTRUCTIONS:
- You can and SHOULD return multiple intents.
- Example: "Calculate churn and give me a marketing plan" -> ["SQL_INVESTIGATION", "PRODUCT_ANALYTICS", "BUSINESS_STRATEGY"]
- **Priority:** Never miss a SQL_INVESTIGATION intent if data extraction is implied.

Output JSON: {"intents": ["INTENT_NAME", ...]}
"""

def classify_intent(client, question: str):
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": ROUTER_PROMPT},
                {"role": "user", "content": question}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        return data.get("intents", [])
    except Exception:
        # Default fallback
        return [BUSINESS_STRATEGY]