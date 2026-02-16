ROUTER_SYSTEM = """Classify which intents are present in the user's request.
Return JSON only.
Allowed labels: BUSINESS_STRATEGY, PRODUCT_ANALYTICS, SQL_INVESTIGATION, PANDAS_TRANSFORM.
"""

def router_user_prompt(user_input: str, df_summary: str | None = None) -> str:
    return f"""User input:
{user_input}

Dataset summary (optional):
{df_summary or "None"}
"""
