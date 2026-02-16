import streamlit as st
from openai import OpenAI

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
def confidence_label(conf: float) -> str:
    if conf >= 0.85:
        return "High"
    if conf >= 0.70:
        return "Medium"
    return "Low"


# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="Analytics Copilot – Phase 1", layout="centered")
st.title("🧠 Analytics Copilot – Phase 1")
st.caption("Multi-intent, schema-aware analytics copilot with clarification gating + per-intent confidence.")


# ----------------------------
# API key resolution (secrets first, then env)
# ----------------------------
api_key = None
try:
    api_key = st.secrets.get("OPENAI_API_KEY")
except Exception:
    api_key = None

if not api_key:
    import os
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("Missing OPENAI_API_KEY. Add it to .streamlit/secrets.toml or set env var OPENAI_API_KEY.")
    st.stop()

client = OpenAI(api_key=api_key)


# ----------------------------
# Session state
# ----------------------------
if "clarification_answers" not in st.session_state:
    st.session_state.clarification_answers = ""
if "proceed_with_answers" not in st.session_state:
    st.session_state.proceed_with_answers = False
if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""
if "run_pipeline_next" not in st.session_state:
    st.session_state.run_pipeline_next = False


# ----------------------------
# Reset button (helps demos a lot)
# ----------------------------
if st.button("🔄 Reset session"):
    st.session_state.pending_question = ""
    st.session_state.clarification_answers = ""
    st.session_state.proceed_with_answers = False
    st.session_state.run_pipeline_next = False
    st.rerun()


# ----------------------------
# Upload
# ----------------------------
uploaded_file = st.file_uploader("Upload a CSV dataset (optional)", type=["csv"])
schema = None
df = None

if uploaded_file:
    try:
        df = load_csv(uploaded_file)
        st.write("Data Preview", df.head())
        schema = summarize_df(df)
        st.write("Schema Summary", schema)
    except Exception as e:
        st.error(f"Error reading CSV: {e}")
        st.stop()


# ----------------------------
# Main UI inputs
# ----------------------------
question = st.text_area("Ask your analytics question", value=st.session_state.pending_question)
run = st.button("Analyze", key="analyze_btn")


def run_pipeline(user_question: str):
    intent_conf_map = {}

    # 1) Intent classification
    intents = classify_intent(client, user_question)
    st.write("Detected intents:", intents)

    # 2) Clarification gate
    gate = get_clarification(client, user_question, intents, schema)

    if gate.get("needs_clarification", False) and not st.session_state.proceed_with_answers:
        st.info("🤔 Clarifying Questions")
        for q in gate.get("questions", []):
            st.write(f"- {q}")

        st.session_state.clarification_answers = st.text_area(
            "Answer the clarifying questions (then click 'Run with clarifications')",
            value=st.session_state.clarification_answers,
            height=120,
            key="clarifications_box",
        )

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Run with clarifications", key="run_with_clarifications_btn"):
                st.session_state.proceed_with_answers = True
                st.session_state.run_pipeline_next = True
                st.rerun()

        with col2:
            if st.button("Clear answers", key="clear_answers_btn"):
                st.session_state.clarification_answers = ""
                st.session_state.proceed_with_answers = False
                st.session_state.run_pipeline_next = False
                st.rerun()

        st.stop()

    user_context = st.session_state.clarification_answers.strip() or None
    if user_context:
        st.caption("Using your clarifications to refine the analysis.")

    # 3) Generate outputs per intent
    for intent in intents:
        if intent == BUSINESS_STRATEGY:
            prompt = build_business_prompt(user_question, schema=schema, user_context=user_context)
            validator = validate_business

        elif intent == PRODUCT_ANALYTICS:
            prompt = build_product_prompt(user_question, schema=schema, user_context=user_context)
            validator = validate_product

        elif intent == SQL_INVESTIGATION:
            if schema is None:
                st.warning("SQL requires an uploaded dataset (schema). Upload CSV to proceed with SQL.")
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
        
        # New Confidence Logic (Object based)
        conf_result = get_confidence(client, output)
        score = conf_result["score"]
        rationale = conf_result["rationale"]
        
        intent_conf_map[intent] = score

        # Display per-intent confidence
        st.subheader(intent.replace("_", " "))
        label = confidence_label(score)
        st.caption(f"Confidence: **{score:.2f} / 1.00** • {label}")
        st.progress(score)
        
        with st.expander("Why this score?"):
            st.write(rationale)

        st.markdown(output)

        is_valid, feedback = validator(output)
        if not is_valid:
            st.warning(feedback)

        if score < CONFIDENCE_THRESHOLD:
            st.warning(f"Low confidence ({score:.2f}). Consider refining the question or adding more context.")

    # 4) Confidence summary
    if intent_conf_map:
        st.divider()
        st.subheader("Overall Confidence Summary")
        for i, c in intent_conf_map.items():
            st.write(f"- {i.replace('_', ' ')}: {c:.2f}")

    # 5) Reset flags
    st.session_state.proceed_with_answers = False
    st.session_state.run_pipeline_next = False


# ----------------------------
# Run logic
# ----------------------------
if run and question.strip():
    # New question = fresh run (prevents Test2 → Test1 bleed)
    st.session_state.pending_question = question.strip()
    st.session_state.run_pipeline_next = True
    st.session_state.proceed_with_answers = False
    st.session_state.clarification_answers = ""

if st.session_state.run_pipeline_next and st.session_state.pending_question:
    run_pipeline(st.session_state.pending_question)