from openai import OpenAI

SYSTEM_PROMPT = """
You are a Gatekeeper for a Data Analytics Copilot.
Your job is to determine if the user's request is **Specific Enough** to be answered immediately, or if it requires clarification.

Criteria for "Specific Enough":
1. Mentions specific data (columns, tables, or a CSV file).
2. OR Mentions a specific business context (e.g., "SaaS churn", "Retail margins").
3. OR Mentions a specific constraint (e.g., "I have no data, give me a theoretical framework").

Criteria for "Ambiguous" (Needs Clarification):
1. Vague one-liners: "Why is revenue down?", "How do I grow?", "Show me the data."
2. No context on *what* business or *what* metric.

Output Format (JSON):
{
    "is_ambiguous": true/false,
    "clarifying_question": "The question to ask the user (if ambiguous)"
}
"""

def check_ambiguity(client: OpenAI, question: str):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    import json
    return json.loads(resp.choices[0].message.content)