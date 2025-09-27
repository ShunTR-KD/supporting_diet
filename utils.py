# utils.py
import os
import json
import math
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any, Tuple

import requests
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from constants import (
    OPENAI_MODEL, SYSTEM_PROMPT, RECIPE_KCAL_PROMPT, CHEER_PROMPT,
    RAKUTEN_BASE_URL, RAKUTEN_GENRE_TO_CATEGORY, RAKUTEN_TOP_N,
    OPEN_METEO_BASE, CITY_COORDS, TEMP_FEEL_THRESHOLDS,
    DEFAULT_PFC_RATIO, DEFAULT_SQLITE_PATH
)

# ---- env 読み込み（initialize からも呼ばれるが冪等） ----
def load_env():
    load_dotenv()
    return {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "RAKUTEN_APPLICATION_ID": os.getenv("RAKUTEN_APPLICATION_ID", ""),
        "SQLITE_PATH": os.getenv("SQLITE_PATH", DEFAULT_SQLITE_PATH)
    }

# ---- DB 初期化 ----
def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meal_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            date TEXT NOT NULL,
            meal_type TEXT NOT NULL,     -- 朝/昼/晩
            name TEXT NOT NULL,          -- 料理名
            kcal REAL NOT NULL           -- 推定カロリー
        )
    """)
    conn.commit()
    conn.close()

# ---- 天気取得（Open-Meteo 仮） ----
def fetch_weekly_weather(city: str) -> Dict[str, Any]:
    lat, lon = CITY_COORDS.get(city, CITY_COORDS["Tokyo"])
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "Asia/Tokyo"
    }
    r = requests.get(OPEN_METEO_BASE, params=params, timeout=15)
    r.raise_for_status()
    return r.json()

def temp_to_feel(temp_c: float) -> str:
    # 閾値に基づきラベル化
    if temp_c < TEMP_FEEL_THRESHOLDS["寒い"]:
        return "寒い"
    elif temp_c < TEMP_FEEL_THRESHOLDS["涼しい"]:
        return "涼しい"
    elif temp_c < TEMP_FEEL_THRESHOLDS["快適"]:
        return "快適"
    elif temp_c < TEMP_FEEL_THRESHOLDS["暑い"]:
        return "やや暑い"
    else:
        return "暑い"

# ---- 季節の算出（簡易） ----
def get_season(today: date = date.today()) -> str:
    m = today.month
    if m in (12,1,2): return "冬"
    if m in (3,4,5):  return "春"
    if m in (6,7,8):  return "夏"
    return "秋"

# ---- 楽天レシピAPI から上位4件取得（雛形） ----
def fetch_top_recipes_by_genre(genre: str, app_id: str) -> List[Dict[str, Any]]:
    """
    実運用：公式ドキュメントに従い、genre→categoryId 変換と
    正式なエンドポイント/パラメータを設定してください。
    ここでは rank 上位を4件返す想定の雛形です。
    """
    cat_id = RAKUTEN_GENRE_TO_CATEGORY.get(genre)
    if not cat_id:
        return []
    params = {
        "applicationId": app_id,
        "categoryId": cat_id
    }
    r = requests.get(RAKUTEN_BASE_URL, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    # 実レスポンス仕様に合わせてパースすること
    items = data.get("result", [])[:RAKUTEN_TOP_N]
    recipes = []
    for it in items:
        recipes.append({
            "recipeName": it.get("recipeTitle") or it.get("recipeName"),
            "recipeUrl": it.get("recipeUrl"),
            "foodImageUrl": it.get("foodImageUrl"),
            "recipeMaterial": it.get("recipeMaterial", []),
            "recipeIndication": it.get("recipeIndication"),  # 調理時間など
        })
    return recipes

# ---- OpenAI でレシピの推定カロリー/PFC ----
def estimate_recipe_kcal_pfc_openai(
    openai_api_key: str,
    recipe_name: str,
    ingredients: List[str],
    method: str,
    difficulty: str,
    budget_jpy: int,
    season: str,
    feel: str
) -> Dict[str, Any]:
    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        temperature=0.3,
        openai_api_key=openai_api_key,
    )
    sys = SystemMessage(content=SYSTEM_PROMPT)
    prompt = RECIPE_KCAL_PROMPT.format(
        recipe_name=recipe_name,
        ingredients=", ".join(ingredients[:10]),
        method=method or "不明",
        difficulty=difficulty,
        budget_jpy=budget_jpy,
        season=season,
        feel=feel
    )
    user = HumanMessage(content=prompt)
    resp = llm.invoke([sys, user])
    # JSONパース（不正時は簡易推定）
    try:
        obj = json.loads(resp.content)
        kcal = float(obj.get("kcal", 0))
        p = float(obj.get("protein_g", 0))
        f = float(obj.get("fat_g", 0))
        c = float(obj.get("carb_g", 0))
        if (p+f+c) <= 0 and kcal > 0:
            # ざっくり配分
            p = kcal * DEFAULT_PFC_RATIO["P"] / 4
            f = kcal * DEFAULT_PFC_RATIO["F"] / 9
            c = kcal * DEFAULT_PFC_RATIO["C"] / 4
        return {"kcal": kcal, "protein_g": p, "fat_g": f, "carb_g": c}
    except Exception:
        # フォールバック（適当な安全値）
        kcal = 500.0
        return {
            "kcal": kcal,
            "protein_g": kcal*DEFAULT_PFC_RATIO["P"]/4,
            "fat_g": kcal*DEFAULT_PFC_RATIO["F"]/9,
            "carb_g": kcal*DEFAULT_PFC_RATIO["C"]/4,
        }

# ---- 応援メッセージ ----
def generate_cheer(openai_api_key: str, summary: str) -> str:
    llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0.7, openai_api_key=openai_api_key)
    sys = SystemMessage(content=SYSTEM_PROMPT)
    user = HumanMessage(content=CHEER_PROMPT.format(summary=summary))
    resp = llm.invoke([sys, user])
    return resp.content.strip()

# ---- 残りカロリー計算 ----
def calc_remaining_kcal(target_kcal: int, consumed_today: float) -> float:
    return max(0.0, target_kcal - consumed_today)

def sum_today_kcal(db_path: str) -> float:
    d = date.today().isoformat()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT SUM(kcal) FROM meal_logs WHERE date = ?", (d,))
    row = cur.fetchone()
    conn.close()
    return float(row[0]) if row and row[0] else 0.0

# ---- 食事記録 ----
def insert_meal_log(db_path: str, meal_type: str, name: str, kcal: float):
    now = datetime.now().isoformat(timespec="seconds")
    d = date.today().isoformat()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO meal_logs (ts, date, meal_type, name, kcal) VALUES (?, ?, ?, ?, ?)",
        (now, d, meal_type, name, kcal)
    )
    conn.commit()
    conn.close()