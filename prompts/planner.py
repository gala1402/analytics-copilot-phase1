SYSTEM_PROMPT = """
You are a task decomposition engine.

Break the message into atomic tasks.

Allowed intents:
- BUSINESS_STRATEGY
- PRODUCT_ANALYTICS
- SQL_INVESTIGATION
- PANDAS_TRANSFORM
- UNSUPPORTED

If mixed intent, create multiple tasks.
Be literal and precise.
Return JSON only.
"""

def build_prompt(user_input, df_summary):
    return f"""
User message:
{user_input}

Dataset summary:
{df_summary or "None"}
"""
