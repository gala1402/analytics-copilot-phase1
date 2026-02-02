import pandas as pd
import streamlit as st

@st.cache_data
def load_csv(uploaded_file):
    """Loads a CSV file into a Pandas DataFrame."""
    try:
        return pd.read_csv(uploaded_file)
    except Exception as e:
        return None

def summarize_df(df: pd.DataFrame) -> dict:
    """
    Generates a rich schema summary including data types and SAMPLE VALUES.
    This gives the AI 'eyes' to see that 'Pro' and 'churned' are real values.
    """
    summary = {}
    for col in df.columns:
        # Get data type
        dtype = str(df[col].dtype)
        
        # Get unique values (Smart Sampling)
        try:
            if df[col].nunique() < 20:
                # For categorical columns (like 'plan_type'), get all values
                examples = df[col].unique().tolist()
            else:
                # For high-cardinality columns, get a random sample of 5
                examples = df[col].dropna().sample(min(5, len(df))).tolist()
        except:
            examples = []

        summary[col] = {
            "dtype": dtype,
            "unique_count": int(df[col].nunique()),
            "examples": examples # <--- The AI can now see your specific data
        }
    return summary