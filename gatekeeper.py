from openai import OpenAI
import json

SYSTEM_PROMPT = """
You are a strict Gatekeeper for an Enterprise Data Analytics AI.
Your job is to filter user queries.

Classify the user input into one of three statuses.

1. **VALID**: Data analytics, SQL, business strategy, Python for data, or CSV analysis.
   - Message: null

2. **AMBIGUOUS**: Relevant but vague (e.g., "It's broken", "Revenue is down").
   - Message: Ask a specific clarifying question.

3. **OFF_TOPIC**: Creative writing, general coding (games, app dev), personal advice, or general knowledge.
   - Message: **MUST BE SPECIFIC.** Do NOT say "I cannot help with that."
     - If user asks for a poem -> Say "I cannot generate creative writing or poetry."
     - If user asks for game code -> Say "I cannot generate game development code."
     - If user asks for general automation -> Say "I only write Python for data analysis, not general automation."

Output Format (JSON):
{
    "status": "VALID" | "AMBIGUOUS" | "OFF_TOPIC",
    "message": "The specific explanation string."
}
"""

def check_ambiguity(client: OpenAI, question: str):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"status": "VALID", "message": None}