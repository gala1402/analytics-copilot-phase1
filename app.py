import streamlit as st
from openai import OpenAI
import pandas as pd
import plotly.express as px

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

st.set_page_config(page_title="Analytics Copilot P2", layout="wide", page_icon="📊")

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

    if st.button("🗑️ Reset Session"):
        for key in list(st.session_state.keys()): del st.session_state[key]
        st.rerun()

if not api_key:
    st.info("Please enter your API Key to unlock the Copilot.")
    st.stop()

client = OpenAI(api_key=api_key)

if "step" not in st.session_state: st.session_state.step = "input"
if "question" not in st.session_state: st.session_state.question = ""
if "context" not in st.session_state: st.session_state.context = ""

# --- Workflow ---

if st.session_state.step == "input":
    st.title("🧠 Analytics Copilot – Phase 2")
    q = st.text_area("What is your inquiry?")
    if st.button("Initialize Analysis", type="primary"):
        st.session_state.question = q
        intents = classify_intent(client, q)
        if "OUT_OF_SCOPE" in intents:
            st.error("Out of scope.")
        else:
            st.session_state.intents = intents
            gate = get_clarification(client, q, intents, schema)
            if gate.get("needs_clarification"):
                st.session_state.questions = gate.get("questions")
                st.session_state.step = "clarify"
            else:
                st.session_state.step = "generate"
            st.rerun()

elif st.session_state.step == "clarify":
    st.header("🔍 Clarifying Context")
    with st.form("clarify_form"):
        ans_list = [st.text_input(cq) for cq in st.session_state.questions]
        if st.form_submit_button("Proceed"):
            st.session_state.context = " | ".join(ans_list)
            st.session_state.step = "generate"
            st.rerun()

elif st.session_state.step == "generate":
    st.subheader(f"Analysis: {st.session_state.question}")
    tabs = st.tabs([i.replace("_", " ").title() for i in st.session_state.intents])
    
    for idx, intent in enumerate(st.session_state.intents):
        with tabs[idx]:
            # Prompt Selection Logic
            if intent == BUSINESS_STRATEGY:
                p, v = build_business_prompt(st.session_state.question, schema, st.session_state.context), validate_business
            elif intent == PRODUCT_ANALYTICS:
                p, v = build_product_prompt(st.session_state.question, schema, st.session_state.context), validate_product
            elif intent == SQL_INVESTIGATION:
                if not schema: st.warning("Upload CSV for SQL."); continue
                p, v = build_sql_prompt(st.session_state.question, schema, st.session_state.context), validate_sql
            elif intent == VISUALIZATION:
                if df is None: st.warning("Upload CSV to visualize."); continue
                p, v = build_viz_prompt(st.session_state.question, schema, df.head(3).to_dict()), None
            
            with st.spinner(f"Processing {intent}..."):
                resp = client.chat.completions.create(model=OPENAI_MODEL, messages=[{"role": "user", "content": p}], temperature=0)
                content = resp.choices[0].message.content

                # FIX: Ensure content exists before proceeding
                if content:
                    if intent == VISUALIZATION:
                        # --- Inside the VISUALIZATION intent block in app.py ---
                                try:
                                    # Remove fig.show() if the LLM adds it, as it breaks Streamlit flow
                                    code = content.split("```python")[1].split("```")[0].strip()
                                    code = code.replace("fig.show()", "# fig.show() handled by streamlit")
                                    
                                    st.code(code, language="python")
                                    
                                    # Pre-processing: Ensure dates are datetime objects for better plotting
                                    if 'Date' in df.columns:
                                        df['Date'] = pd.to_datetime(df['Date'])

                                    local_vars = {"df": df, "px": px, "pd": pd, "st": st}
                                    exec(code, {}, local_vars)
                                    
                                    # Intelligent Capture: find any plotly figure object created in the code
                                    fig = local_vars.get("fig")
                                    if fig:
                                        st.plotly_chart(fig, use_container_width=True)
                                    else:
                                        st.warning("Code executed but no 'fig' object was found to display.")
                                        
                                except Exception as e:
                                    st.error(f"Visualization Error: {e}")
                    else:
                        # FIX: This is where line 142 was crashing
                        conf = get_confidence(client, content)
                        st.metric("Confidence Score", f"{int(conf*100)}%")
                        st.markdown(content)
                        if v:
                            is_valid, msg = v(content)
                            if not is_valid: st.caption(f"💡 Recommendation: {msg}")
                else:
                    st.error("No content generated by the model.")

    if st.button("Start New Inquiry"):
        st.session_state.step = "input"
        st.rerun()