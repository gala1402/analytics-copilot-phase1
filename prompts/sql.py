def sql_missing_context_questions(question: str, df_summary: str | None = None) -> list[str]:
    qs = []
    # If no schema, we need schema
    if not df_summary:
        qs.append("For SQL: what are the table names and key columns (or paste schema / upload CSV)?")
    # Common missing definitions
    if "churn" in question.lower():
        qs.append("How do you define churn (e.g., no activity for 30 days, subscription canceled, last_seen cutoff)?")
    if "cohort" in question.lower():
        qs.append("What should the cohort be based on (signup month, first purchase month, first active date)?")
    if "last month" in question.lower() or "this month" in question.lower():
        qs.append("What date column should I use for time filtering (event_date, created_at, etc.)?")
    return qs

def build_sql_prompt(question: str, df_summary: str | None = None) -> str:
    return f"""Write a single SQL query using CTEs where helpful.

Requirements:
- Use explicit column names (no SELECT *)
- Add comments for major steps
- Make it readable
- Do NOT invent tables/columns; only use what is in the schema summary if provided.
- If the schema summary is missing, write a best-guess SQL skeleton and include TODO comments where schema is needed.

Schema summary:
{df_summary or "None provided"}

Question:
{question}
"""
