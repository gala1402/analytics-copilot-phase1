import re

def validate_business(output: str):
    low = output.lower()
    # Block technical leakage
    if re.search(r"\b(funnel|cohort|select|join|from)\b", low):
        return False, "Strategy output contains technical/product jargon. Keep it high-level."
    if "metric" not in low:
        return False, "Please include specific business metrics (e.g., LTV, CAC)."
    return True, "Valid"