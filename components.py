# components.py
import streamlit as st
import pandas as pd
from typing import List, Dict, Any
import time
import logging

import constants as ct

# ログ設定（utils.pyで初期化済みのロガーを取得）
logger = logging.getLogger(__name__)

def sidebar_inputs(defaults: dict, consumed_kcal: float = 0) -> dict:
    logger.debug("サイドバー入力処理開始")
    
    # 摂取状況を最上部に表示
    st.sidebar.markdown("### 今日の摂取状況")
    
    # 目標カロリーの取得（一時的にデフォルト値を使用）
    temp_target = defaults["target_kcal"]
    temp_remaining = temp_target - consumed_kcal
    
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("摂取済み", f"{int(consumed_kcal)}kcal", 
                 delta=None if consumed_kcal == 0 else f"+{int(consumed_kcal)}", 
                 help="今日摂取したカロリーの合計")
    with col2:
        remaining_color = "normal" if temp_remaining > 200 else "inverse"
        st.metric("残り", f"{int(temp_remaining)}kcal", 
                 delta=f"目標 {int(temp_target)}kcal", 
                 delta_color=remaining_color,
                 help=f"目標カロリーまであと{int(temp_remaining)}kcal")
    
    # 進捗バー
    progress = max(0, min(1, consumed_kcal / temp_target)) if temp_target > 0 else 0
    st.sidebar.progress(progress, text=f"進捗: {progress:.1%}")
    st.sidebar.markdown("---")
    
    # 条件入力
    st.sidebar.header(f"{ct.CUSTOM_ICONS} 条件入力")
    target_kcal = st.sidebar.number_input(
        "1日の目標カロリー (kcal)", min_value=800, max_value=4000,
        value=defaults["target_kcal"], step=50
    )
    
    # 目標カロリーが変更された場合の再計算と表示更新
    if target_kcal != temp_target:
        updated_remaining = target_kcal - consumed_kcal
        updated_progress = max(0, min(1, consumed_kcal / target_kcal)) if target_kcal > 0 else 0
        
        # 更新された値を表示エリアに反映
        st.sidebar.markdown("**📊 更新された摂取状況**")
        col1_update, col2_update = st.sidebar.columns(2)
        with col1_update:
            st.metric("摂取済み", f"{int(consumed_kcal)}kcal", help="今日摂取したカロリーの合計")
        with col2_update:
            remaining_color = "normal" if updated_remaining > 200 else "inverse"
            st.metric("残り", f"{int(updated_remaining)}kcal", 
                     delta=f"目標 {int(target_kcal)}kcal", 
                     delta_color=remaining_color,
                     help=f"目標カロリーまであと{int(updated_remaining)}kcal")
        
        st.sidebar.progress(updated_progress, text=f"更新進捗: {updated_progress:.1%}")
        st.sidebar.markdown("---")
    meal_budget = st.sidebar.number_input(
        "1食あたりの予算 (円)", min_value=100, max_value=3000,
        value=defaults["meal_budget"], step=50
    )
    difficulty = st.sidebar.selectbox("料理の難易度", ct.DIFFICULTY_OPTIONS, index=0)
    genre = st.sidebar.selectbox("料理ジャンル", ct.GENRE_OPTIONS, index=0)
    
    # キーワード検索機能を追加
    st.sidebar.markdown("**🔍 詳細検索**")
    search_keyword = st.sidebar.text_input(
        "料理のキーワード", 
        placeholder="例: 鶏肉、パスタ、カレー",
        help="具体的な食材や料理名を入力すると、より精密な検索ができます"
    )
    
    # 検索モード選択
    search_mode = st.sidebar.radio(
        "検索方式",
        ["ジャンル優先", "キーワード優先"],
        help="ジャンル優先: 選択したジャンル内で検索 / キーワード優先: キーワードを重視した検索"
    )
    
    meal_type = st.sidebar.selectbox("食事の区分", ct.MEAL_TYPES, index=1)
    location = st.sidebar.selectbox("地域", ["Tokyo", "Osaka", "Sapporo", "Fukuoka"], index=0)

    st.sidebar.markdown("---")
    propose = st.sidebar.button(f"{ct.RECIPE_ICONS} レシピ提案")
    weekly = st.sidebar.button(f"{ct.SCHEDULE_ICONS} 1週間の献立提案")

    inputs = {
        "target_kcal": int(target_kcal),
        "meal_budget": int(meal_budget),
        "difficulty": difficulty,
        "genre": genre,
        "search_keyword": search_keyword.strip() if search_keyword else None,
        "search_mode": search_mode,
        "meal_type": meal_type,
        "location": location,
        "propose": propose,
        "weekly": weekly
    }
    
    if propose:
        logger.info(f"レシピ提案ボタンクリック - ジャンル: {genre}, 難易度: {difficulty}")
    if weekly:
        logger.info(f"週間献立ボタンクリック - ジャンル: {genre}")
    
    return inputs

def show_weather_calendar(weather: dict):
    logger.debug("天気カレンダー表示処理開始")
    st.subheader(f"{ct.SCHEDULE_ICONS} 今週の天気（最高/最低）")
    daily = weather.get("daily", {})
    if not daily:
        logger.warning("天気データが空です")
        st.info("天気情報を取得できませんでした。")
        return
        
    logger.debug(f"天気データ件数: {len(daily.get('time', []))}日分")
    df = pd.DataFrame({
        "日付": daily.get("time", []),
        "最高気温(℃)": daily.get("temperature_2m_max", []),
        "最低気温(℃)": daily.get("temperature_2m_min", []),
    })
    st.dataframe(df, use_container_width=True, hide_index=True)

def recipe_card(idx: int, r: dict, kcal_info: dict, cheer: str):
    recipe_name = r.get('recipeName', '(名称不明)')
    logger.debug(f"レシピカード{idx}表示: {recipe_name}")
    
    with st.container(border=True):
        cols = st.columns([1,2,2])
        with cols[0]:
            if r.get("foodImageUrl"):
                st.image(r["foodImageUrl"], width=160)
                logger.debug(f"レシピ{idx}画像表示")
        with cols[1]:
            st.markdown(f"**{idx}. {recipe_name}**")
            st.write(f"推定カロリー: **{int(kcal_info['kcal'])} kcal**")
            st.write(f"P: {kcal_info['protein_g']:.1f} g / F: {kcal_info['fat_g']:.1f} g / C: {kcal_info['carb_g']:.1f} g")
            if r.get("recipeUrl"):
                st.link_button("レシピを見る（楽天）", r["recipeUrl"])
        with cols[2]:
            st.caption("管理栄養士AIからのひとこと")
            st.info(cheer)

def weekly_table(rows: List[dict]):
    logger.info(f"週間献立テーブル表示 - {len(rows)}日分")
    st.subheader(f"{ct.SCHEDULE_ICONS} 1週間の献立（1日1品）")
    
    # データフレームを作成
    df = pd.DataFrame(rows)
    
    # レシピリンク列がある場合は削除（streamlitでサポートされていないためテーブルには表示しない）
    if "レシピリンク" in df.columns:
        df = df.drop("レシピリンク", axis=1)
    
    # テーブル表示
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # リンクボタンを別途表示
    original_rows = pd.DataFrame(rows)
    if "レシピリンク" in original_rows.columns:
        st.write("📖 **レシピ詳細リンク:**")
        
        # 3列でリンクボタンを配置
        cols = st.columns(3)
        for i, row in enumerate(rows):
            if row.get("レシピリンク") and row["レシピリンク"].startswith("http"):
                with cols[i % 3]:  # 3列に分散配置
                    st.write(f"**{row['日']}**")
                    st.write(f"{row['料理名'][:15]}...")  # 料理名を短縮
                    st.link_button("🔗 レシピを見る", row["レシピリンク"])
                    st.write("")  # 間隔調整

def show_loading_progress(message: str, progress: float = None):
    """ローディング表示とプログレスバー"""
    logger.debug(f"ローディング表示: {message}")
    if progress is not None:
        st.progress(progress, text=message)
    else:
        with st.spinner(message):
            time.sleep(0.1)  # UI更新のため

def error_feedback(error_type: str, details: str = None):
    """エラーの種類に応じた適切なフィードバック表示"""
    logger.warning(f"エラーフィードバック表示 - タイプ: {error_type}, 詳細: {details}")
    error_messages = {
        "network": "インターネット接続を確認してください",
        "api_limit": "API制限に達しました。しばらく待ってから再試行してください", 
        "invalid_input": "入力内容を確認してください"
    }
    
    message = error_messages.get(error_type, "予期しないエラーが発生しました")
    if details:
        message += f"\n詳細: {details}"
    
    st.error(message)