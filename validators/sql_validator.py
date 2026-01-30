def validate_sql(output: str):
    low = output.lower()
    if "select" not in low:
        return False, "SQL output must include a SELECT statement."
    return True, "Valid"