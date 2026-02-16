import re

def validate_business(output: str):
    low = output.lower()

    # Ignore notes/disclaimer sections
    split = re.split(r"\n\s*(note:|notes:|disclaimer:)\s*", low, maxsplit=1)
    core = split[0]

    # Product analytics leakage
    # Don't ban "segment" entirely; ban specific technical artifacts
    if re.search(r"\b(funnel breakdown|conversion funnel|cohort table|retention cohort|technical segmentation)\b", core):
        return False, "Business Strategy should not include technical funnels or cohort tables. Keep it strategy-focused."

    if "funnel" in core and "dropoff" in core:
         return False, "Business Strategy should not include specific funnel dropoff analysis."

    # SQL leakage (Fixed: Removed common words like 'from', 'where', 'join')
    # Now looks for explicit SQL phrases
    if re.search(r"\b(select\s+\*|select\s+top|group\s+by|order\s+by|inner\s+join|left\s+join|right\s+join)\b", core):
        return False, "Business Strategy should not include SQL or pseudo-SQL."

    # Ensure it includes measurable metrics
    if "metric" not in core and "metrics" not in core:
        return False, "Add at least 2–3 explicit metrics to track."

    return True, "Valid"