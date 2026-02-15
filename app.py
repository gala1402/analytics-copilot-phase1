import streamlit as st
import pandas as pd
import json
import os
from openai import OpenAI

# ==========================================
# 1. CONFIGURATION & STYLING
# ==========================================
st.set_page_config(page_title="Analytics Copilot (MVP)", page_icon="🧠", layout="wide")

# Custom CSS for the "Traffic Light" Badges
st.markdown("""
    <style>
    .stTextArea textarea { font-size: 16px !important; }
    .status-badge {
        padding: 8px 12px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 16px;
        display: inline-block;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Constants
OPENAI_MODEL = "gpt-4o-mini"

# ==========================================
# 2. HELPER FUNCTIONS (The "Brain")
# ==========================================

def get_confidence_badge(score, rationale):
    """Returns HTML for the Traffic Light UI."""
    if score >= 0.9:
        color, bg, emoji, label = "green", "#e6ffe6", "🟢", "High Confidence"
    elif score >= 0.7:
        color, bg, emoji, label = "#b38600", "#fff8e6", "🟡", "Medium Confidence"
    else:
        color, bg, emoji, label = "red", "#ffe6e6", "🔴", "Low Confidence"
    
    return f"""
    <div class="status-badge" style="background-color: {bg}; border: 1px solid {color};">
        {emoji} <span style="color: {color};">{label}</span>
    </div>
    <div style="color: gray; font-size: 14px; margin-bottom: 15px;">
        <b>Diagnosis:</b> {rationale}
    </div>
    """

@st.cache_data
def load_data(file):
    if file is None: return None, "No Data"
    try:
        df = pd.read_csv(file)
        # MVP Schema Extraction: Simple & Fast
        schema = {}
        for col in df.columns:
            schema[col] = str(df[col].dtype)
            # Add sample values for 'context'
            if df[col].nunique() < 10:
                schema[f"{col}_samples"] = df[col].unique().tolist()
        return df, json.dumps(schema, indent=2)
    except:
        return None, "Error loading CSV"

def call_llm(client, system_prompt, user_prompt):
    """Simple wrapper for OpenAI calls."""
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def get_auditor_score(client, question, answer, schema_str):
    """The 'Auditor' Logic - Simplified for MVP."""
    prompt = f"""
    Rate confidence (0.0 to 1.0) of the AI Answer based on the Schema.
    
    RULES:
    - 1.0 (High): Uses existing columns/values OR correctly refuses missing data.
    - 0.5 (Med): Generic advice.
    - 0.1 (Low): Hallucinated columns.

    Schema: {schema_str}
    Question: {question}
    Answer: {answer}

    Return JSON: {{"score": float, "rationale": "Short reason"}}
    """
    try:
        res = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "system", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(res.choices[0].message.content)
    except:
        return {"score": 0.5, "rationale": "Auditor failed."}

# ==========================================
# 3. SIDEBAR (Inputs)
# ==========================================
with st.sidebar:
    st.title("🧠 Settings")
    
    # API Key Handling
    api_key = st.secrets.get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        api_key = st.text_input("OpenAI API Key", type="password")
    
    st.divider()
    
    # Data Uploader
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])
    df, schema_str = load_data(uploaded_file)
    
    if df is not None:
        st.success(f"Loaded {len(df)} rows")
        with st.expander("View Schema"):
            st.code(schema_str)
    
    st.divider()
    
    with st.expander("📊 Legend"):
        st.markdown("""
        🟢 **High:** Verified Facts / Safe Refusal
        🟡 **Medium:** Generic Advice
        🔴 **Low:** Guessing / Error
        """)

# ==========================================
# 4. MAIN INTERFACE
# ==========================================
st.title("Analytics Copilot")
st.caption("MVP Version • Updated UI • One-File Architecture")

if not api_key:
    st.warning("Please enter your OpenAI API Key in the sidebar to start.")
    st.stop()

client = OpenAI(api_key=api_key)

# Input Area
question = st.text_area("What do you want to know?", height=100, placeholder="e.g. Calculate churn rate for Pro users")
run_btn = st.button("🚀 Run Analysis", type="primary", use_container_width=True)

# ==========================================
# 5. EXECUTION LOGIC (The "Old School" Flow)
# ==========================================
if run_btn and question:
    with st.status("Running Analysis...", expanded=True) as status:
        
        # 1. Simple Router (No separate file)
        status.write("📍 Routing Request...")
        router_prompt = "Classify intent: [SQL, BUSINESS, PRODUCT]. Return JSON: {'intents': []}"
        intents_json = call_llm(client, router_prompt, question)
        
        # Fallback routing logic if LLM fails or is lazy
        intents = []
        if "SQL" in intents_json or "count" in question.lower() or "calculate" in question.lower():
            intents.append("SQL Agent")
        if "why" in question.lower() or "strategy" in question.lower():
            intents.append("Business Agent")
        if "usage" in question.lower() or "product" in question.lower() or not intents:
            intents.append("Product Agent") # Default
            
        intents = list(set(intents)) # Dedupe
        status.write(f"✅ Activated Agents: {', '.join(intents)}")
        
        # 2. Run Agents & Auditor
        results = {}
        
        for agent in intents:
            status.write(f"⚡ Running {agent}...")
            
            # --- AGENT PROMPTS (Inline) ---
            if agent == "SQL Agent":
                sys_prompt = f"You are a SQL Expert. Schema: {schema_str}. Write a query for: {question}. If table missing, say so."
            elif agent == "Business Agent":
                sys_prompt = f"You are a Business Strategist. Schema: {schema_str}. Context: {question}. If data missing, give generic advice but WARN the user."
            else: # Product
                sys_prompt = f"You are a Product Analyst. Schema: {schema_str}. Context: {question}. Cite specific columns."
            
            # Generate Answer
            answer = call_llm(client, sys_prompt, question)
            
            # Audit Answer
            audit = get_auditor_score(client, question, answer, schema_str)
            
            results[agent] = {
                "response": answer,
                "score": audit["score"],
                "rationale": audit["rationale"]
            }
            
        status.update(label="Analysis Complete", state="complete", expanded=False)

    # ==========================================
    # 6. RESULTS DISPLAY (The "New UI")
    # ==========================================
    st.divider()
    
    # Create Tabs
    tabs = st.tabs([name for name in results.keys()])
    
    for i, (agent_name, data) in enumerate(results.items()):
        with tabs[i]:
            # 1. Traffic Light Badge
            st.markdown(get_confidence_badge(data['score'], data['rationale']), unsafe_allow_html=True)
            
            # 2. The Answer
            st.markdown("### Answer")
            st.markdown(data['response'])