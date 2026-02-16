def validate_pandas_code(code: str) -> tuple[bool, list[str]]:
    issues = []
    if "iterrows" in code:
        issues.append("Avoid iterrows; prefer vectorized ops.")
    return (len(issues) == 0), issues
