import pandas as pd

def summarize_df(df):
    summary = []
    summary.append(f"Rows: {len(df)}")
    summary.append("Columns:")
    for col in df.columns:
        summary.append(f"- {col}")
    return "\n".join(summary)
