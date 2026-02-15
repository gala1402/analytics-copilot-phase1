# data_utils.py
import pandas as pd
import streamlit as st

@st.cache_data
def load_csv(uploaded_file):
    try:
        return pd.read_csv(uploaded_file)
    except:
        return None

def summarize_df(df: pd.DataFrame) -> dict:
    summary = {}
    for col in df.columns:
        dtype = str(df[col].dtype)
        try:
            if df[col].nunique() < 20:
                examples = df[col].unique().tolist()
            else:
                examples = df[col].dropna().sample(min(5, len(df))).tolist()
        except:
            examples = []

        summary[col] = {
            "dtype": dtype,
            "unique_count": int(df[col].nunique()),
            "examples": examples
        }
    return summary