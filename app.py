# app.py
import streamlit as st
from openai import OpenAI
import time
import json
import os

from config import OPENAI_MODEL
from models import BUSINESS_STRATEGY, PRODUCT_ANALYTICS, SQL_INVESTIGATION
from router import classify_intent
from clarifier import get_clarification
from confidence import get_confidence
from data_utils import load_csv, summarize_df

# Imports for prompts/validators (Assuming these files exist in subfolders)
from prompts.business import build_business_prompt
from prompts.product import build_product_prompt
from prompts.sql import build_sql_prompt
from validators.business_validator import validate_business
from validators.product_validator import validate_product
from validators.sql_validator import validate_sql

# Page Config
st.set_page_config(page_title="Analytics Copilot", page_icon="🧠", layout="wide")

# Helpers
def get_confidence_meta(conf: float):
    if conf >= 0.9: return "High Confidence", "#e6ffe6", "🟢", "green"
    if conf >= 0.7: return "Medium Confidence", "#fff8e6", "🟡", "#b38600"
    return "Low Confidence", "#ffe6e6", "🔴", "red"

# Sidebar
with st.sidebar:
    st.title("🧠 Settings")
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = st.text_input("OpenAI API Key", type="password")
        if not api_key: st.stop()
    
    client = OpenAI(api_key=api_key)
    st.divider()
    
    with st.expander("📊 Confidence Legend", expanded=True):
        st.markdown("""
        🟢 **High:** Verified Truth / Correct Refusal.
        🟡 **Medium:** General Advice / Assumptions.
        🔴 **Low:** Hallucination Risk.
        """)
    
    st.divider()
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    schema, df = None, None
    if uploaded_file:
        df = load_csv(uploaded_file)
        schema = summarize_df(df)
        st.success(f"Loaded {len(df)} rows")

    if st.button("Reset"):
        st.session_state.clear()
        st.rerun()

# Logic
def run_pipeline(user_question, schema_context):
    from gatekeeper import check_ambiguity
    with st.status("Thinking...", expanded=True) as status:
        
        # 1. Gatekeeper
        if not st.session_state.clarification_answers:
            check = check_ambiguity(client, user_question)
            if check["status"] != "VALID": return check["status"], check["message"], {}
        
        # 2. Router
        status.write("📍 Routing...")
        intents = classify_intent(client, user_question)
        
        # 3. Clarifier
        status.write("🤔 Clarifying...")
        gate = get_clarification(client, user_question, intents, schema_context)
        if gate.get("needs_clarification") and not st.session_state.proceed_with_answers:
            return "CLARIFICATION_NEEDED", gate, intents
        
        # 4. Execution
        results = {}
        user_context = st.session_state.clarification_answers
        
        for intent in intents:
            status.write(f"⚡ Running {intent}...")
            
            # Select Prompt
            if intent == BUSINESS_STRATEGY:
                prompt = build_business_prompt(user_question, schema_context, user_context)
                val_func = validate_business
            elif intent == PRODUCT_ANALYTICS:
                prompt = build_product_prompt(user_question, schema_context, user_context)
                val_func = validate_product
            elif intent == SQL_INVESTIGATION:
                if not schema_context and not user_context:
                    results[intent] = {"output": "Missing Dataset", "score": 0.0, "rationale": "No CSV", "valid": False}
                    continue
                prompt = build_sql_prompt(user_question, schema_context, user_context)
                val_func = validate_sql
            else: continue

            # Call LLM
            resp = client.chat.completions.create(
                model=OPENAI_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.0
            )
            output = resp.choices[0].message.content
            
            # Confidence & Validation
            conf = get_confidence(client, user_question, output, intent, schema_context)
            valid, feedback = val_func(output)
            
            results[intent] = {
                "output": output, "score": conf["score"], "rationale": conf["rationale"],
                "valid": valid, "feedback": feedback
            }
        
        return "SUCCESS", results, {}

# UI Flow
st.title("Analytics Copilot")
if "clarification_answers" not in st.session_state: st.session_state.clarification_answers = ""
if "proceed_with_answers" not in st.session_state: st.session_state.proceed_with_answers = False

q = st.text_area("Question", placeholder="e.g. Calculate MRR for Pro users")
if st.button("Run Analysis"):
    st.session_state.pending_question = q
    st.session_state.proceed_with_answers = False
    st.session_state.analysis_results = None
    st.rerun()

if st.session_state.get("pending_question"):
    code, data, _ = run_pipeline(st.session_state.pending_question, schema)
    
    if code == "SUCCESS":
        st.session_state.analysis_results = data
        st.session_state.pending_question = None # Clear after run
    elif code == "CLARIFICATION_NEEDED":
        st.warning("Clarification Needed")
        for q in data.get("questions", []): st.info(q)
        ans = st.text_input("Answer:")
        if st.button("Submit"):
            st.session_state.clarification_answers = ans
            st.session_state.proceed_with_answers = True
            st.rerun()
    elif code in ["OFF_TOPIC", "AMBIGUOUS"]:
        st.error(data)
        st.session_state.pending_question = None

if st.session_state.get("analysis_results"):
    tabs = st.tabs([k.replace("_", " ").title() for k in st.session_state.analysis_results.keys()])
    for i, (key, res) in enumerate(st.session_state.analysis_results.items()):
        with tabs[i]:
            label, bg, emoji, txt = get_confidence_meta(res["score"])
            st.markdown(f"<div style='background:{bg};padding:10px;border-radius:5px;margin-bottom:10px'>"
                        f"<span style='font-size:20px'>{emoji}</span> <b style='color:{txt}'>{label}</b></div>", 
                        unsafe_allow_html=True)
            if res["score"] < 0.9: st.info(f"**Diagnosis:** {res['rationale']}")
            st.markdown(res["output"])