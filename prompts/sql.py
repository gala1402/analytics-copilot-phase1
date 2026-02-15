import json
def build_sql_prompt(q, s, c):
    schema_str = json.dumps(s) if s else "No Schema"
    return f"Generate standard SQL for: {q}. Schema: {schema_str}. Return ONLY SQL code block."