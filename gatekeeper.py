from openai import OpenAI
import json

SYSTEM_PROMPT = """
You are a strict Gatekeeper for an Enterprise Data Analytics AI.
Your job is to filter user queries.

Classify the user input into one of three statuses and provide a message:

1. **VALID**: The user is asking about data analytics, business strategy, SQL, metrics, CSV files, or python code for analysis.
   - Message: null

2. **AMBIGUOUS**: The user is asking a relevant business question, but it is too vague.
   - Message: "A specific question asking for the missing details (e.g. 'Which table?')."

3. **OFF_TOPIC**: The user is asking about general knowledge, creative writing, coding unrelated to data, or gibberish.
   - Message: "A polite but firm explanation of why this is rejected. Mention that you only handle Data Analytics."

Output Format (JSON):
{
    "status": "VALID" | "AMBIGUOUS" | "OFF_TOPIC",
    "message": "The string explanation (Required for AMBIGUOUS and OFF_TOPIC)"
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
        result = json.loads(resp.choices[0].message.content)
        
        # Fail-safe: Ensure message exists if status is OFF_TOPIC
        if result.get("status") == "OFF_TOPIC" and not result.get("message"):
            result["message"] = "I am specialized in Data Analytics. I cannot answer general questions."
            
        return result
        
    except Exception:
        # Fail-safe if JSON breaks
        return {"status": "VALID", "message": None}