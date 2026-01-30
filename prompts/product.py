def build_product_prompt(question, schema=None, user_context=None):
    schema_txt = f"\nDataset Schema:\n{schema}" if schema else ""
    ctx_txt = f"\nUser Clarifications:\n{user_context}" if user_context else ""

    return f"""
You are a PRODUCT ANALYTICS analyst.

SCOPE (very important):
- Provide ONLY product analytics: hypotheses, metrics, funnel definition, cohorts, segmentation, experiments.
- DO NOT provide budgeting/strategy recommendations (e.g., “invest in acquisition vs retention”).
- DO NOT write SQL or pseudo-SQL.
- DO NOT mention conflicts between tasks or comment on instructions.
- If key information is missing, explicitly list what’s missing instead of guessing.

{schema_txt}
{ctx_txt}

Question:
{question}

Output format:
- Hypotheses (3–5 bullets)
- Metrics (bullets)
- Funnel definition (stages + how measured)
- Cohort + segmentation plan
- Experiments / next steps
- Missing information needed (bullets, if any)
""".strip()