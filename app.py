import streamlit as st
from openai import OpenAI
import pandas as pd
import time

from config import OPENAI_MODEL, CONFIDENCE_THRESHOLD
from models import BUSINESS_STRATEGY, PRODUCT_ANALYTICS, SQL_INVESTIGATION
from router import classify_intent
from clarifier import get_clarification
from confidence import get_confidence
from data_utils import load_csv, summarize_df

from prompts.business import build_business_prompt
from prompts.product import build_product_prompt
from prompts.sql import build_sql_prompt

from validators.business_validator import validate_business
from validators.product_validator import validate_product
from validators.sql_validator import validate_sql


# ----------------------------
# Helpers
# ----------------------------
def confidence_color(conf: float) -> str:
    if conf >= 0.85:
        return "green"
    if conf >= 0.70:
        return "orange"
    return "red"

def confidence_label(conf: float) -> str:
    if conf >= 0.85:
        return "High Confidence"
    if conf >= 0.70:
        return "Medium Confidence"
    return "Low Confidence"


# ----------------------------
# Page config (Wide Mode)
# ----------------------------
st.set_page_config(
    page_title="Analytics Copilot", 
    page_icon="🧠",
    layout="wide"
)

# Custom CSS for cleaner look (FIXED SYNTAX HERE)
st.markdown("""
    <style>
    .stTextArea textarea {
        font-size: 16px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)


# ----------------------------
# Sidebar: Setup & Data
# ----------------------------
with st.sidebar:
    st.title("🧠 Copilot Settings")
    
    # API Key Handling
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = st.text_input("OpenAI API Key", type="password")
            if not api_key:
                st.warning("Please enter an API Key to proceed.")
                st.stop()
    
    client = OpenAI(api_key=api_key)

    st.divider()
    
    # File Uploader
    st.subheader("📂 Data Context")
    uploaded_file = st.file_uploader("Upload CSV (Optional)", type=["csv"])
    
    schema = None
    df = None

    if uploaded_file:
        try:
            df = load_csv(uploaded_file)
            schema = summarize_df(df)
            st.success(f"Loaded {len(df)} rows")
            
            with st.expander("View Data Preview"):
                st.dataframe(df.head())
            
            with