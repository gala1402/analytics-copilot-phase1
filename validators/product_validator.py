import re

def validate_product(output: str):
    low = output.lower()

    split = re.split(r"\n\s*(note:|notes:|disclaimer:)\s*", low, maxsplit=1)
    core = split[0]

    # No strategy/budgeting language
    if re.search(r"\b(allocate budget|budget allocation|invest in acquisition|invest in retention|go-to-market|gtm)\b", core):
        return False, "Product Analytics should not include budget/strategy recommendations. Keep it analytics-only."

    # No SQL leakage (Fixed: Removed common words like 'from', 'where', 'join')
    if re.search(r"\b(select\s+\*|select\s+top|group\s+by|order\s+by|inner\s+join|left\s+join|right\s+join)\b", core):
        return False, "Product Analytics should not include SQL or pseudo-SQL."

    # Must include product artifacts
    if not re.search(r"\b(funnel|cohort|segment|segmentation)\b", core):
        return False, "Add a funnel, cohort, or segmentation approach."

    return True, "Valid"