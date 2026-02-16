import streamlit as st
import pandas as pd
from config import AppConfig
from llm.client import LLMClient
from core.gatekeeper import gatekeep
from core.task_planner import plan_tasks
from core.executors import execute_tasks
from core.composer import compose
from data_utils import summarize_df
from memory import init_memory

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

    gk = gatekeep(llm, user_input, df_summary)

    if gk["decision"] == "REFUSE":
        st.error("Out of scope.")
        st.stop()

    if gk["decision"] == "ASK":
        st.warning("Need clarification:")
        for q in gk.get("questions", []):
            st.write("- ", q)
        st.stop()

    plan = plan_tasks(llm, user_input, df_summary)
    st.write(f"Confidence: {plan['confidence']:.2f}")

    results = execute_tasks(llm, plan["tasks"], df_summary)
    final = compose(user_input, plan["tasks"], results)

    st.markdown(final)
