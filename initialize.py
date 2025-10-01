# initialize.py
import streamlit as st
import logging
from utils import load_env, init_db, setup_logging
from constants import DEFAULT_SQLITE_PATH

def initialize_once():
    if st.session_state.get("_initialized"):
        return
    
    # ログ設定を最初に初期化
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("アプリケーション初期化開始")
    env = load_env()
    db_path = env.get("SQLITE_PATH", DEFAULT_SQLITE_PATH)
    init_db(db_path)
    st.session_state["_initialized"] = True
    logger.info("アプリケーション初期化完了")