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

# UI Config
st.set_page_config(page_title="Analytics Copilot P2", layout="wide", page_icon="🧠")

# --- Onboarding & Capability Helper ---
def show_capabilities():
    st.info("### 🛠️ Interactive Analytics Copilot Capabilities")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **What I Can Do:**
        * **Strategic Framing**: Unit economics & KPI tradeoffs.
        * **Product Insights**: Funnels, cohorts, and experiments.
        * **Grounded SQL**: Database queries based on your actual CSV.
        * **Smart Viz**: Choosing the right chart for your data trends.
        """)
    with col2:
        st.markdown("""
        **My Limitations:**
        * **Fail-Closed**: I won't guess your data. No CSV = No SQL/Viz.
        * **Clarification Gate**: I'll stop to ask for definitions if vague.
        * **Analytical Scope**: I handle business & data only. No general chat.
        """)

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

if not api_key:
    st.info("Please enter your API Key to start.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- App State ---
if "step" not in st.session_state: st.session_state.step = "input"

# --- Main Logic ---
if st.session_state.step == "input":
    st.title("🧠 Analytics Copilot")
    show_capabilities()
    
    q = st.text_area("How can I help with your data today?", placeholder="e.g., Visualize our revenue trend...")
    
    if st.button("Process Request", type="primary"):
        intents = classify_intent(client, q)
        
        if "OUT_OF_SCOPE" in intents:
            st.error("🚫 **Out of Scope**: I'm a specialized analytics partner. I cannot assist with general topics like recipes or travel. Please ask an analytics or business-related question.")
        elif "CAPABILITIES" in intents:
            st.toast("Re-displaying capabilities...")
            st.rerun()
        else:
            st.session_state.question = q
            st.session_state.intents = intents
            gate = get_clarification(client, q, intents, schema)
            
            if gate.get("needs_clarification"):
                st.session_state.questions = gate.get("questions")
                st.session_state.step = "clarify"
                st.rerun()
            else:
                st.session_state.step = "generate"
                st.rerun()

elif st.session_state.step == "clarify":
    st.header("🔍 Targeted Clarifications")
    st.write("To ensure high integrity, I need you to define these aspects before I analyze:")
    with st.form("clarification_form"):
        ans = [st.text_input(q) for q in st.session_state.questions]
        if st.form_submit_button("Generate Grounded Analysis"):
            st.session_state.context = " | ".join(ans)
            st.session_state.step = "generate"
            st.rerun()

elif st.session_state.step == "generate":
    # (Existing Generation Logic from the previous step goes here)
    # Ensure it ends with a 'New Inquiry' button to reset st.session_state.step to 'input'
    if st.button("Start New Inquiry"):
        st.session_state.step = "input"
        st.rerun()