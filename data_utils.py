import pandas as pd

def load_csv(file):
    # Try different encodings if default fails
    try:
        return pd.read_csv(file)
    except UnicodeDecodeError:
        return pd.read_csv(file, encoding='latin1')

def summarize_df(df, max_cols=50):
    summary = {
        "rows": int(len(df)),
        "total_columns": len(df.columns),
        "columns": []
    }
    
    # Truncate if too many columns to prevent token overflow
    cols_to_summarize = df.columns[:max_cols]
    
    summary["columns"] = [
        {
            "name": col,
            "dtype": str(df[col].dtype),
            "non_null_pct": round(float(df[col].notnull().mean()) * 100, 1),
            "unique": int(df[col].nunique(dropna=True)),
            # Sample values help the LLM understand what the data looks like
            "sample_values": df[col].dropna().astype(str).head(3).tolist()
        }
        for col in cols_to_summarize
    ]
    
    if len(df.columns) > max_cols:
        summary["warning"] = f"Schema truncated. Only first {max_cols} columns shown."
        
    return summary