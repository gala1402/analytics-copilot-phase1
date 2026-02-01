import streamlit as st
from openai import OpenAI
import pandas as pd
import time

# --- Configuration & Imports ---
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
# Page Config
# ----------------------------
st.set_page_config(
    page_title="Analytics Copilot", 
    page_icon="🧠",
    layout="wide"
)

# Custom CSS
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
# Helper Functions
# ----------------------------
def confidence_label(conf: float) -> str:
    if conf >= 0.85:
        return "High Confidence"
    if conf >= 0.70:
        return "Medium Confidence"
    return "Low Confidence"

# ----------------------------
# Sidebar
# ----------------------------
with st.sidebar:
    st.title("🧠 Copilot Settings")
    
    api_key = st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            api_key = st.text_input("OpenAI API Key", type="password")
            if not api_key:
                st.warning("Enter API Key to proceed.")
                st.stop()
    
    client = OpenAI(api_key=api_key)

    st.divider()
    
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
            with st.expander("View Schema Summary"):
                st.json(schema)
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            st.stop()
    else:
        st.info("Upload CSV for grounded analysis.")

    st.divider()
    if st.button("🔄 Reset Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ----------------------------
# Session State
# ----------------------------
if "clarification_answers" not in st.session_state:
    st.session_state.clarification_answers = ""
if "proceed_with_answers" not in st.session_state:
    st.session_state.proceed_with_answers = False
if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""
if "run_pipeline_next" not in st.session_state:
    st.session_state.run_pipeline_next = False
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None

# ----------------------------
# Main Input
# ----------------------------
st.title("Analytics Copilot")
st.caption("A multi-intent, schema-aware AI partner.")

col1, col2 = st.columns([4, 1])
with col1:
    question = st.text_area(
        "What would you like to analyze?", 
        value=st.session_state.pending_question,
        placeholder="e.g., 'Why is retention dropping?'",
        height=100
    )
with col2:
    st.write("") 
    st.write("") 
    run_pressed = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

# ----------------------------
# Core Logic
# ----------------------------
def run_pipeline(user_question: str):
    with st.status("Thinking...", expanded=True) as status:
    
        # 0. Gatekeeper Check
        if not st.session_state.clarification_answers: 
            from gatekeeper import check_ambiguity
            gate_check = check_ambiguity(client, user_question)
            
            if gate_check.get("is_ambiguous"):
                return "AMBIGUOUS", gate_check["clarifying_question"], {}

        # 1. Routing
        status.write("📍 Routing request...")
        intents = classify_intent(client, user_question)
        time.sleep(0.5)
        status.write(f"✅ Detected intents: **{', '.join(intents)}**")
        
        # 2. Clarification
        status.write("🤔 Checking for ambiguity...")
        gate = get_clarification(client, user_question, intents, schema)
        
        if gate.get("needs_clarification", False) and not st.session_state.proceed_with_answers:
            status.update(label="Clarification Required", state="error", expanded=True)
            return "CLARIFICATION_NEEDED", gate, intents
            
        user_context = st.session_state.clarification_answers.strip() or None
        if user_context:
            status.write("📝 Incorporating user context...")
            # Schema detection
            sql_triggers = ["table", "column", "schema", "database", ".csv", "dataset"]
            if any(trigger in user_context.lower() for trigger in sql_triggers):
                from models import SQL_INVESTIGATION
                if SQL_INVESTIGATION not in intents:
                    status.write("💡 Detected schema details -> Activating SQL Agent.")
                    intents.append(SQL_INVESTIGATION)

        # 3. Execution
        results = {}
        intent_conf_map = {}
        
        for intent in intents:
            status.write(f"⚡ Generating: {intent.replace('_', ' ')}...")
            
            if intent == BUSINESS_STRATEGY:
                prompt = build_business_prompt(user_question, schema=schema, user_context=user_context)
                validator = validate_business
            elif intent == PRODUCT_ANALYTICS:
                prompt = build_product_prompt(user_question, schema=schema, user_context=user_context)
                validator = validate_product
            elif intent == SQL_INVESTIGATION:
                # Allow SQL if user provided text schema context
                if schema is None and not user_context:
                    results[intent] = {
                        "output": "⚠️ **SQL skipped**: No dataset uploaded and no schema description provided.",
                        "score": 0.0,
                        "rationale": "Missing schema.",
                        "valid": False,
                        "feedback": "Upload CSV or describe your table schema."
                    }
                    continue
                prompt = build_sql_prompt(user_question, schema=schema, user_context=user_context)
                validator = validate_sql
            else:
                continue

            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
            )
            output = resp.choices[0].message.content or ""
            
            # Confidence Scoring
            conf_result = get_confidence(client, user_question, output, intent)
            
            is_valid, feedback = validator(output)
            
            results[intent] = {
                "output": output,
                "score": conf_result["score"],
                "rationale": conf_result["rationale"],
                "valid": is_valid,
                "feedback": feedback
            }
            intent_conf_map[intent] = conf_result["score"]
        
        status.update(label="Analysis Complete", state="complete", expanded=False)
        return "SUCCESS", results, intent_conf_map

# ----------------------------
# Execution Flow
# ----------------------------
if run_pressed and question.strip():
    st.session_state.pending_question = question.strip()
    st.session_state.run_pipeline_next = True
    st.session_state.proceed_with_answers = False
    st.session_state.clarification_answers = ""
    st.session_state.analysis_results = None

if st.session_state.run_pipeline_next and st.session_state.pending_question:
    status_code, data, extra = run_pipeline(st.session_state.pending_question)
    
    if status_code == "AMBIGUOUS":
        st.warning(f"⚠️ Clarification Needed: {data}")
        st.write("The AI needs more context to give a high-quality answer.")
        with st.form("gatekeeper_form"):
            clarification = st.text_input("Please provide details (e.g. table name, goal):")
            if st.form_submit_button("Submit Context"):
                st.session_state.clarification_answers = clarification
                st.session_state.proceed_with_answers = True
                st.session_state.run_pipeline_next = True
                st.rerun()
        st.stop()

    elif status_code == "CLARIFICATION_NEEDED":
        gate = data
        st.warning("I need a few details before I can give a high-quality answer.")
        col_q, col_a = st.columns([1, 1])
        with col_q:
            st.markdown("### ❓ Missing Context")
            for q in gate.get("questions", []):
                st.info(f"{q}")
        with col_a:
            st.markdown("### ✍️ Your Answer")
            st.session_state.clarification_answers = st.text_area(
                "Provide details here:",
                value=st.session_state.clarification_answers,
                height=150,
                key="clarification_input"
            )
            if st.button("Run with Clarifications", type="primary"):
                st.session_state.proceed_with_answers = True
                st.session_state.run_pipeline_next = True
                st.rerun()

    elif status_code == "SUCCESS":
        st.session_state.analysis_results = data
        st.session_state.run_pipeline_next = False

# ----------------------------
# Results Display
# ----------------------------
if st.session_state.analysis_results:
    results = st.session_state.analysis_results
    st.divider()
    
    # Capitalize tab names
    tab_names = [k.replace("_", " ").title() for k in results.keys()]
    tabs = st.tabs(tab_names)
    
    for i, intent in enumerate(results.keys()):
        res = results[intent]
        with tabs[i]:
            c1, c2 = st.columns([3, 1])
            with c1:
                score = res["score"]
                label = confidence_label(score)
                st.caption(f"Confidence Score: **{score:.2f} / 1.00** • {label}")
                st.progress(score)
                
                if score < CONFIDENCE_THRESHOLD:
                    st.warning(f"⚠️ Low Confidence: {res['rationale']}")
                else:
                    with st.expander("Why this score?"):
                        st.write(res["rationale"])

            with c2:
                if res["valid"]:
                    st.success("✅ Scope Validated")
                else:
                    st.error("⚠️ Scope Warning")
                    st.caption(res["feedback"])

            st.divider()
            st.markdown(res["output"])