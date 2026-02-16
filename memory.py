import streamlit as st

def init_memory():
    if "definitions" not in st.session_state:
        st.session_state["definitions"] = {}

def store_definition(key, value):
    st.session_state["definitions"][key] = value

def get_definitions():
    return st.session_state.get("definitions", {})
