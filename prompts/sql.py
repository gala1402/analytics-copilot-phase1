def build_sql_prompt(question, schema, user_context=None):
    ctx_txt = f"\nUser Clarifications:\n{user_context}" if user_context else ""

    return f"""
You are a senior analytics engineer.

Dataset Schema:
{schema}
{ctx_txt}

Task:
Write SQL to answer:
{question}

Requirements:
- Use CTEs where helpful
- Do NOT hallucinate tables/columns not present in schema
- Include brief validation notes at the end
Return only SQL + short validation notes (no long prose).
""".strip()