import re

def validate_product(output: str):
    low = output.lower()
    # Block strategy leakage
    if re.search(r"\b(budget|market share|ceo|board of directors)\b", low):
        return False, "Product output contains corporate strategy language. Keep it feature-focused."
    if not re.search(r"\b(funnel|cohort|segment|experiment)\b", low):
        return False, "Missing core product artifacts (Funnels or Cohorts)."
    return True, "Valid"