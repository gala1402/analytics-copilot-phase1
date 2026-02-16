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

if uploaded:
    df = pd.read_csv(uploaded)
    df_summary = summarize_df(df)
    st.write(df.head())

user_input = st.text_area("Ask your analytics question:")

if st.button("Run"):

    # Append prior clarifications into context
    prior_context = "\n".join(
        [f"{k}: {v}" for k, v in get_definitions().items()]
    )

    enriched_input = user_input + "\n\nAdditional context:\n" + prior_context

    # 1️⃣ Gatekeeper
    gk = gatekeep(llm, enriched_input, df_summary)

    if gk["decision"] == "REFUSE":
        st.error("Out of scope.")
        st.stop()

    if gk["decision"] == "ASK":
        st.warning("Need clarification:")
        for q in gk.get("questions", []):
            st.write("- ", q)

        clarification_input = st.text_area("Provide clarification:")
        if st.button("Submit clarification"):
            store_definition("manual_clarification", clarification_input)
            st.experimental_rerun()
        st.stop()

    # 2️⃣ Plan
    plan = plan_tasks(llm, enriched_input, df_summary)
    st.write(f"Confidence: {plan['confidence']:.2f}")

    # 3️⃣ Clarifier
    clarification = clarify_tasks_if_needed(plan["tasks"], df_summary)

    # HARD BLOCK
    if clarification["needs_hard_clarification"]:
        st.warning("Required clarification before proceeding:")
        for q in clarification["hard_questions"]:
            st.write("- ", q)

        clarification_input = st.text_area("Provide required clarification:")
        if st.button("Submit clarification"):
            store_definition("manual_clarification", clarification_input)
            st.experimental_rerun()
        st.stop()


    # 4️⃣ Execute
    results = execute_tasks(llm, plan["tasks"], df_summary)

    # 5️⃣ Compose
    final = compose(user_input, plan["tasks"], results)

    st.markdown(final)
