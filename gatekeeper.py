from openai import OpenAI
import json

SYSTEM_PROMPT = """
You are a strict Gatekeeper for an Enterprise Data Analytics AI.
Your job is to filter user queries.

Classify the user input into one of three statuses:

1. **VALID**: 
   - Criteria: Questions about data analytics, SQL, business strategy, metrics, Python for data, or CSV analysis.
   - Message: null

2. **AMBIGUOUS**:
   - Criteria: Relevant business keywords but too vague (e.g., "It's broken", "Why is it down?", "Fix it").
   - Message: "Please provide specific details about the metric, report, or table you are referring to."

3. **OFF_TOPIC**:
   - Criteria: ANYTHING not related to Data Analytics or Business Strategy.
   - **Instruction for Message**: You MUST return a specific refusal string based on the category:
     - **Creative Writing**: "I cannot generate creative writing, poetry, songs, or fiction."
     - **General Coding**: "I only write Python for data analysis, not general application development or games."
     - **General Knowledge**: "I am specialized in Data Analytics. I cannot answer general trivia or history questions."
     - **Personal/Medical/Legal**: "I cannot provide personal, medical, or legal advice."
     - **Gibberish/Noise**: "This input appears to be unintelligible. Please ask a valid data analytics question."
     - **Everything Else**: "I am designed strictly for Business Data Analytics / SQL Investigation and cannot assist with this request."

Output Format (JSON):
{
    "status": "VALID" | "AMBIGUOUS" | "OFF_TOPIC",
    "message": "The specific refusal string."
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
        
        # --- SAFETY NET ---
        # If the LLM marks it OFF_TOPIC but forgets the message, force a default.
        if result.get("status") == "OFF_TOPIC":
            if not result.get("message") or result["message"].strip() == "":
                result["message"] = "I am designed strictly for Business Data Analytics and cannot assist with this request."
        
        return result
        
    except Exception:
        # Fallback if JSON breaks: Allow it through (Better to allow than block valid queries on error)
        return {"status": "VALID", "message": None}