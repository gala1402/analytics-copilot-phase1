import streamlit as st
import pandas as pd
from config import AppConfig
from llm.client import LLMClient
from core.gatekeeper import gatekeep
from core.task_planner import plan_tasks
from core.clarifier import clarify_tasks_if_needed
from core.executors import execute_tasks
from core.composer import compose
from data_utils import summarize_df
from memory import init_memory, store_definition, get_definitions

st.set_page_config(layout="wide")
st.title("Interactive Analytics Copilot (GPT-4o-mini Optimized)")

init_memory()

config = AppConfig.from_env()
llm = LLMClient(config)

uploaded = st.file_uploader("Upload CSV (optional)", type=["csv"])
df_summary = None
df = None

if uploaded:
    df = pd.read_csv(uploaded)
    df_summary = summarize_df(df)
    st.write(df.head())

user_input = st.text_area("Ask your analytics question:")

if st.button("Run"):

    # Include prior clarifications in context
    prior = get_definitions()
    prior_context = "\n".join([f"{k}: {v}" for k, v in prior.items()]) if prior else ""
    enriched_input = user_input
    if prior_context.strip():
        enriched_input += "\n\nAdditional context from earlier clarifications:\n" + prior_context

    # 1) Gatekeeper
    gk = gatekeep(llm, enriched_input, df_summary)

    if gk["decision"] == "REFUSE":
        st.error(gk.get("message") or "Out of scope.")
        st.stop()

    # If Gatekeeper produced optional questions, show them (non-blocking)
    if gk.get("questions"):
        st.info("Optional context to improve accuracy (not required):")
        for q in gk["questions"]:
            st.write(f"- {q}")

        opt = st.text_area("Optional additional context (you can leave this blank):")
        if st.button("Add optional context"):
            if opt.strip():
                store_definition("optional_context", opt.strip())
                st.experimental_rerun()

    # If Gatekeeper is truly blocking, THEN stop and ask for clarification
    if gk["decision"] == "ASK" and gk.get("blocking", False):
        st.warning(gk.get("message") or "Need clarification to proceed:")
        for q in gk.get("questions", []):
            st.write(f"- {q}")

        clarification_input = st.text_area("Provide clarification:")
        if st.button("Submit clarification"):
            if clarification_input.strip():
                store_definition("manual_clarification", clarification_input.strip())
                st.experimental_rerun()
        st.stop()

    # 2) Plan tasks
    plan = plan_tasks(llm, enriched_input, df_summary)
    st.write(f"Confidence: {plan.get('confidence', 0.0):.2f}")

    # 3) Clarifier (hard blocking only for SQL/Pandas)
    clarification = clarify_tasks_if_needed(plan["tasks"], df_summary)

    if clarification["needs_hard_clarification"]:
        st.warning("Required clarification before proceeding:")
        for q in clarification["hard_questions"]:
            st.write(f"- {q}")

        clarification_input = st.text_area("Provide required clarification:")
        if st.button("Submit required clarification"):
            if clarification_input.strip():
                store_definition("required_clarification", clarification_input.strip())
                st.experimental_rerun()
        st.stop()

    # 4) Execute supported tasks
    results = execute_tasks(llm, plan["tasks"], df_summary=df_summary, df=df)

    # 5) Compose
    final = compose(user_input, plan["tasks"], results)
    st.markdown(final)
