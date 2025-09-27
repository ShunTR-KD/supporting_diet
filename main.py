# main.py
import streamlit as st
from datetime import date

from initialize import initialize_once
from components import sidebar_inputs, show_weather_calendar, recipe_card, weekly_table
from utils import (
    load_env, fetch_weekly_weather, temp_to_feel, get_season,
    fetch_top_recipes_by_genre, estimate_recipe_kcal_pfc_openai,
    generate_cheer, sum_today_kcal, calc_remaining_kcal, insert_meal_log
)
from constants import (
    DEFAULT_TARGET_KCAL, DEFAULT_MEAL_BUDGET_JPY, DEFAULT_LOCATION
)

st.set_page_config(page_title="NutriBuddy", page_icon="🍽️", layout="wide")

# 初回のみ初期化
initialize_once()
env = load_env()
OPENAI_API_KEY = env["OPENAI_API_KEY"]
RAKUTEN_APP_ID = env["RAKUTEN_APPLICATION_ID"]
DB_PATH = env["SQLITE_PATH"]

# ヘッダ
st.title("🍽️ NutriBuddy（ニュートリバディ）")
st.caption("“あなたの努力を見守り、毎日応援してくれるダイエットパートナー管理栄養士AI”")

# サイドバー入力
inputs = sidebar_inputs({
    "target_kcal": DEFAULT_TARGET_KCAL,
    "meal_budget": DEFAULT_MEAL_BUDGET_JPY,
    "meal_budget_unit": "JPY",
    "location": DEFAULT_LOCATION
})

# 天気
weather = fetch_weekly_weather(inputs["location"])
show_weather_calendar(weather)

# 今日の温度感（今日の最高気温を採用）
today_feel = "快適"
try:
    max_list = weather.get("daily", {}).get("temperature_2m_max", [])
    if max_list:
        today_feel = temp_to_feel(float(max_list[0]))
except Exception:
    pass

# 今日の食事状況
consumed = sum_today_kcal(DB_PATH)
remaining = calc_remaining_kcal(inputs["target_kcal"], consumed)
st.metric(label="今日の残り摂取可能カロリー", value=f"{int(remaining)} kcal", delta=f"摂取済み {int(consumed)} kcal")

# レシピ提案
if inputs["propose"]:
    st.subheader("🍳 レシピ提案（上位4件×推定カロリー/PFC）")
    season = get_season()
    recipes = fetch_top_recipes_by_genre(inputs["genre"], RAKUTEN_APP_ID)

    if not recipes:
        st.warning("レシピが取得できませんでした。ジャンルやAPI設定を確認してください。")
    else:
        for i, r in enumerate(recipes, start=1):
            kcal_info = estimate_recipe_kcal_pfc_openai(
                OPENAI_API_KEY,
                recipe_name=r.get("recipeName",""),
                ingredients=r.get("recipeMaterial",[]),
                method=r.get("recipeIndication") or "",
                difficulty=inputs["difficulty"],
                budget_jpy=inputs["meal_budget"],
                season=season,
                feel=today_feel
            )
            summary = f"{r.get('recipeName','')} / 約{int(kcal_info['kcal'])}kcal / {inputs['genre']} / {inputs['difficulty']} / 予算{inputs['meal_budget']}円 / 体感:{today_feel}"
            cheer = generate_cheer(OPENAI_API_KEY, summary)
            recipe_card(i, r, kcal_info, cheer)

            # 記録ボタン
            col1, col2 = st.columns([1,4])
            with col1:
                if st.button(f"この料理を{inputs['meal_type']}に記録", key=f"log_{i}"):
                    insert_meal_log(DB_PATH, inputs["meal_type"], r.get("recipeName","不明"), float(kcal_info["kcal"]))
                    st.success("食事を記録しました。ページを再読み込みすると残カロリーが更新されます。")
            st.divider()

# 1週間の献立
if inputs["weekly"]:
    st.subheader("📅 1週間の献立を作成中…")
    season = get_season()
    recipes = fetch_top_recipes_by_genre(inputs["genre"], RAKUTEN_APP_ID)
    rows = []
    if recipes:
        # シンプルに同じ上位候補から日替わりで1品ずつ（本実装では重複回避や多様性ロジックを向上）
        for d in range(7):
            r = recipes[d % len(recipes)]
            kcal_info = estimate_recipe_kcal_pfc_openai(
                OPENAI_API_KEY,
                recipe_name=r.get("recipeName",""),
                ingredients=r.get("recipeMaterial",[]),
                method=r.get("recipeIndication") or "",
                difficulty=inputs["difficulty"],
                budget_jpy=inputs["meal_budget"],
                season=season,
                feel=today_feel
            )
            summary = f"{r.get('recipeName','')} / 約{int(kcal_info['kcal'])}kcal / 日{d+1}"
            cheer = generate_cheer(OPENAI_API_KEY, summary)
            rows.append({
                "日": f"Day {d+1}",
                "料理名": r.get("recipeName",""),
                "推定kcal": int(kcal_info["kcal"]),
                "応援": cheer
            })
        weekly_table(rows)
    else:
        st.warning("献立を作成できませんでした（レシピ取得失敗）。")