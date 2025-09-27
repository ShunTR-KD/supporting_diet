# components.py
import streamlit as st
import pandas as pd
from typing import List, Dict, Any

from constants import MEAL_TYPES, DIFFICULTY_OPTIONS, GENRE_OPTIONS

def sidebar_inputs(defaults: dict) -> dict:
    st.sidebar.header("🔧 条件入力")
    target_kcal = st.sidebar.number_input(
        "1日の目標カロリー (kcal)", min_value=800, max_value=4000,
        value=defaults["target_kcal"], step=50
    )
    meal_budget = st.sidebar.number_input(
        "1食あたりの予算 (円)", min_value=100, max_value=3000,
        value=defaults["meal_budget"], step=50
    )
    difficulty = st.sidebar.selectbox("料理の難易度", DIFFICULTY_OPTIONS, index=0)
    genre = st.sidebar.selectbox("料理ジャンル", GENRE_OPTIONS, index=0)
    meal_type = st.sidebar.selectbox("食事の区分", MEAL_TYPES, index=1)
    location = st.sidebar.selectbox("地域", ["Tokyo", "Osaka", "Sapporo", "Fukuoka"], index=0)

    st.sidebar.markdown("---")
    propose = st.sidebar.button("🍳 レシピ提案")
    weekly = st.sidebar.button("📅 1週間の献立提案")

    return {
        "target_kcal": int(target_kcal),
        "meal_budget": int(meal_budget),
        "difficulty": difficulty,
        "genre": genre,
        "meal_type": meal_type,
        "location": location,
        "propose": propose,
        "weekly": weekly
    }

def show_weather_calendar(weather: dict):
    st.subheader("📆 今週の天気（最高/最低）")
    daily = weather.get("daily", {})
    if not daily:
        st.info("天気情報を取得できませんでした。")
        return
    df = pd.DataFrame({
        "日付": daily.get("time", []),
        "最高気温(℃)": daily.get("temperature_2m_max", []),
        "最低気温(℃)": daily.get("temperature_2m_min", []),
    })
    st.dataframe(df, use_container_width=True)

def recipe_card(idx: int, r: dict, kcal_info: dict, cheer: str):
    with st.container(border=True):
        cols = st.columns([1,2,2])
        with cols[0]:
            if r.get("foodImageUrl"):
                st.image(r["foodImageUrl"], width=160)
        with cols[1]:
            st.markdown(f"**{idx}. {r.get('recipeName','(名称不明)')}**")
            st.write(f"推定カロリー: **{int(kcal_info['kcal'])} kcal**")
            st.write(f"P: {kcal_info['protein_g']:.1f} g / F: {kcal_info['fat_g']:.1f} g / C: {kcal_info['carb_g']:.1f} g")
            if r.get("recipeUrl"):
                st.link_button("レシピを見る（楽天）", r["recipeUrl"])
        with cols[2]:
            st.caption("管理栄養士AIからのひとこと")
            st.info(cheer)

def weekly_table(rows: List[dict]):
    st.subheader("📅 1週間の献立（1日1品）")
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)