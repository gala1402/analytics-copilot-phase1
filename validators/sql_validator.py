def validate_sql(output: str):
    if "SELECT" not in output.upper():
        return False, "Output must contain a valid SQL SELECT statement."
    return True, "Valid"