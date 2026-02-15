import streamlit as st
from openai import OpenAI
import pandas as pd
import plotly.express as px
import traceback

from config import OPENAI_MODEL, CONFIDENCE_THRESHOLD
from models import BUSINESS_STRATEGY, PRODUCT_ANALYTICS, SQL_INVESTIGATION, VISUALIZATION
from router import classify_intent
from clarifier import get_clarification
from confidence import get_confidence
from data_utils import load_csv, summarize_df

from prompts.business import build_business_prompt
from prompts.product import build_product_prompt
from prompts.sql import build_sql_prompt
from prompts.viz import build_viz_prompt

from validators.business_validator import validate_business
from validators.product_validator import validate_product
from validators.sql_validator import validate_sql

# --- Page Config ---
st.set_page_config(page_title="Analytics Copilot P2", layout="wide", page_icon="📊")

# --- Styling ---
st.markdown("""
    <style>
    .stProgress > div > div > div > div { background-image: linear-gradient(to right, #4facfe 0%, #00f2fe 100%); }
    div[data-testid="stExpander"] { border: 1px solid #e6e9ef; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Control Panel")
    api_key = st.secrets.get("OPENAI_API_KEY") or st.text_input("OpenAI API Key", type="password")
    uploaded_file = st.file_uploader("Upload Dataset (CSV)", type="csv")
    
    schema = None
    df = None
    if uploaded_file:
        df = load_csv(uploaded_file)
        schema = summarize_df(df)
        st.success(f"✅ Data Active: {uploaded_file.name}")
        with st.expander("Inspect Schema"):
            st.json(schema)
            
    if st.button("🗑️ Reset Session"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

if not api_key:
    st.info("Please enter your API Key to unlock the Copilot.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- Session State Management ---
if "step" not in st.session_state: st.session_state.step = "input"
if "question" not in st.session_state: st.session_state.question = ""
if "context" not in st.session_state: st.session_state.context = ""

# --- Workflow Steps ---

# Step 1: Input & Intent
if st.session_state.step == "input":
    st.title("🧠 Analytics Copilot – Phase 2")
    q = st.text_area("What is your inquiry?", placeholder="e.g., Show me the correlation between price and churn, then write SQL for the raw data.")
    
    if st.button("Initialize Analysis", type="primary"):
        if not q.strip(): st.warning("Please enter a question."); st.stop()
        
        st.session_state.question = q
        intents = classify_intent(client, q)
        
        if "OUT_OF_SCOPE" in intents:
            st.error("Request is outside of analytics scope.")
        else:
            st.session_state.intents = intents
            gate = get_clarification(client, q, intents, schema)
            if gate.get("needs_clarification"):
                st.session_state.questions = gate.get("questions")
                st.session_state.step = "clarify"
            else:
                st.session_state.step = "generate"
            st.rerun()

# Step 2: Clarification
elif st.session_state.step == "clarify":
    st.header("🔍 Clarifying Context")
    with st.form("clarify_form"):
        answers = []
        for i, cq in enumerate(st.session_state.questions):
            answers.append(st.text_input(cq, key=f"ans_{i}"))
        
        if st.form_submit_button("Proceed"):
            st.session_state.context = " | ".join(answers)
            st.session_state.step = "generate"
            st.rerun()

# Step 3: Generation (The Engine)
elif st.session_state.step == "generate":
    st.subheader(f"Analysis: {st.session_state.question}")
    
    tabs = st.tabs([i.replace("_", " ").title() for i in st.session_state.intents])
    
    for idx, intent in enumerate(st.session_state.intents):
        with tabs[idx]:
            if intent == BUSINESS_STRATEGY:
                prompt = build_business_prompt(st.session_state.question, schema, st.session_state.context)
                val_fn = validate_business
            elif intent == PRODUCT_ANALYTICS:
                prompt = build_product_prompt(st.session_state.question, schema, st.session_state.context)
                val_fn = validate_product
            elif intent == SQL_INVESTIGATION:
                if not schema: st.warning("Upload CSV for SQL."); continue
                prompt = build_sql_prompt(st.session_state.question, schema, st.session_state.context)
                val_fn = validate_sql
            elif intent == VISUALIZATION:
                if df is None: st.warning("Upload CSV to visualize."); continue
                prompt = build_viz_prompt(st.session_state.question, schema, df.head(3).to_dict())
                val_fn = None # Handled by code execution
            
            with st.spinner(f"Processing {intent}..."):
                response = client.chat.completions.create(model=OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0)
                content = response.choices[0].message.content

                # Special Handling for Visualization
                if intent == VISUALIZATION:
                    try:
                        code = content.split("```python")[1].split("```")[0].strip()
                        st.code(code, language="python")
                        # EXECUTION SANDBOX
                        local_vars = {"df": df, "px": px, "st": st}
                        exec(code, {}, local_vars)
                        if "fig" in local_vars:
                            st.plotly_chart(local_vars["fig"], use_container_width=True)
                    except Exception as e:
                        st.error(f"Visualization Error: {e}")
                else:
                    conf = get_confidence(client, content)
                    st.metric("Confidence Score", f"{int(conf*100)}%")
                    st.markdown(content)
                    if val_fn:
                        is_valid, msg = val_fn(content)
                        if not is_valid: st.caption(f"💡 Recommendation: {msg}")

    if st.button("Start New Inquiry"):
        st.session_state.step = "input"
        st.rerun()