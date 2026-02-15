# gatekeeper.py
import json
from config import OPENAI_MODEL

GATEKEEPER_PROMPT = """
You are a Content Safety Filter.
Your job is to screen user inputs for OFF_TOPIC or AMBIGUOUS content.

1. **OFF_TOPIC**: Requests unrelated to data analytics, business, SQL, or python. (e.g. "Write a poem", "Code snake game").
2. **AMBIGUOUS**: Single words like "Why?" or "How?" with no context.
3. **VALID**: Any data-related request.

Output JSON: {"status": "VALID" | "OFF_TOPIC" | "AMBIGUOUS", "message": "Reason"}
"""

def check_ambiguity(client, question: str):
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": GATEKEEPER_PROMPT},
                {"role": "user", "content": question}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except:
        return {"status": "VALID"}