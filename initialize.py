# initialize.py
import streamlit as st
from utils import load_env, init_db
from constants import DEFAULT_SQLITE_PATH

def initialize_once():
    if st.session_state.get("_initialized"):
        return
    env = load_env()
    db_path = env.get("SQLITE_PATH", DEFAULT_SQLITE_PATH)
    init_db(db_path)
    st.session_state["_initialized"] = True