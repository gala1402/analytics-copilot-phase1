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
    layout="wide"  # Use the full screen width
)

# Custom CSS for cleaner look
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
        padding-bottom: 10px