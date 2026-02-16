def product_missing_context_questions(question: str) -> list[str]:
    qs = []
    if "adoption" in question.lower():
        qs.append("What is the definition of adoption (first use, weekly active use, % accounts using feature, etc.)?")
    if "retention" in question.lower() or "churn" in question.lower():
        qs.append("Which user/entity are we measuring (users, accounts, merchants) and what is the activity event?")
    return qs

def build_product_prompt(question: str) -> str:
    return f"""Answer as a product analytics lead.
Provide:
1) framing & hypotheses
2) metrics to compute
3) recommended cuts/segments
4) next actions
Be concrete and structured.

Question:
{question}
"""

def build_pandas_prompt(question: str, df_summary: str | None = None) -> str:
    return f"""Write pandas code to solve the task.

Rules:
- Prefer vectorized operations (avoid iterrows)
- Use clear variable names
- Use groupby/merge/transform as needed
- If df_summary is missing, write code with TODOs (expected column names)

df_summary:
{df_summary or "None"}

Task:
{question}

Return ONLY python code (no explanation).
"""
