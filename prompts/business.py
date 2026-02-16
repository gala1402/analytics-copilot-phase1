def build_business_prompt(question: str) -> str:
    return f"""You are a business strategy advisor.
Return:
- Decision framing
- Options + tradeoffs
- KPIs to watch
- Recommendation + rationale
Keep it crisp and actionable.

Question:
{question}
"""
