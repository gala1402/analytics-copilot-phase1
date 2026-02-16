import re

def validate_sql(sql, df_summary):
    if not df_summary:
        return sql

    columns = []
    for line in df_summary.splitlines():
        if line.startswith("- "):
            columns.append(line.split()[1].lower())

    tokens = re.findall(r"\b[a-zA-Z_]+\b", sql.lower())

    unknown = [t for t in tokens if t not in columns and t not in {"select","from","where","group","by","and","or","as","join"}]

    if len(unknown) > 5:
        return sql + "\n\n-- WARNING: Possible schema mismatch detected."

    return sql
