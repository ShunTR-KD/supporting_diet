# utils.py
import os
import json
import math
import sqlite3
import logging
import time
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Tuple
import asyncio
import aiohttp
import functools

import requests
from dotenv import load_dotenv
import streamlit as st

from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

import constants as ct

# ---- ログ設定 ----
def setup_logging():
    """ログ設定を初期化"""
    # ログディレクトリを作成
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # ログファイル名（日付付き）
    log_filename = f"{log_dir}/nutribuddy_{datetime.now().strftime('%Y%m%d')}.log"
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()  # コンソールにも出力
        ]
    )
    
    # アプリケーション用のロガーを作成
    logger = logging.getLogger('NutriBuddy')
    logger.info("="*50)
    logger.info("NutriBuddy アプリケーション開始")
    logger.info("="*50)
    
    return logger

# グローバルロガー
logger = setup_logging()

# ---- 開発用：ログレベル変更機能 ----
def set_debug_mode(enable: bool = True):
    """
    開発用：デバッグモードの有効/無効を切り替え
    
    Args:
        enable: Trueでデバッグモード有効、FalseでINFOレベル
    """
    global logger
    level = logging.DEBUG if enable else logging.INFO
    logger.setLevel(level)
    
    # ハンドラーのレベルも変更
    for handler in logger.handlers:
        handler.setLevel(level)
    
    status = "有効" if enable else "無効"
    logger.info(f"デバッグモード: {status}")

def run_debug_tests(app_id: str):
    """
    開発用：楽天レシピAPIのテスト実行
    カテゴリ一覧とサンプルレシピの取得を行ってJSONデータを表示
    """
    logger.info("=== 開発用テスト実行開始 ===")
    
    # デバッグモード有効化
    set_debug_mode(True)
    
    try:
        # 1. カテゴリ一覧の取得と表示
        logger.info("--- 1. カテゴリ一覧テスト ---")
        debug_fetch_and_display_categories(app_id)
        
        # 2. 動的カテゴリ検索テスト（楽天APIの実際のカテゴリ名を使用）
        logger.info("--- 2. 動的カテゴリ検索テスト（実際のカテゴリ名） ---")
        
        # 楽天APIの実際のカテゴリ名でテスト
        api_based_keywords = [
            ("鶏肉", "和風"),      # 楽天APIには「鶏肉」カテゴリが存在
            ("パスタ", "洋風"),    # 楽天APIには「パスタ」カテゴリが存在
            ("牛肉", None),       # 楽天APIには「牛肉」カテゴリが存在
            ("豚肉", "和風"),     # 楽天APIには「豚肉」カテゴリが存在
            ("サラダ", "洋風"),   # 楽天APIには「サラダ」カテゴリが存在
            ("カレー", None),     # 楽天APIには「カレー」カテゴリが存在
            ("ラーメン", "中華"), # 楽天APIには「ラーメン」カテゴリが存在
            ("炒め物", "中華"),   # 楽天APIには「炒め物」関連カテゴリが存在
            ("スープ", None),     # 楽天APIには「スープ」カテゴリが存在
            ("デザート", None)    # 楽天APIには「デザート」カテゴリが存在
        ]
        
        for keyword, genre_hint in api_based_keywords:
            logger.info(f"=== キーワード検索: '{keyword}' (ジャンル: {genre_hint}) ===")
            category_ids = search_category_by_keyword(app_id, keyword, genre_hint)
            logger.info(f"検索結果: {category_ids}")
            
            # 検索結果が空でない場合、最初のカテゴリの詳細を表示
            if category_ids:
                # カテゴリ詳細を取得して表示
                categories_data = fetch_rakuten_categories(app_id)
                if categories_data and 'result' in categories_data:
                    found_category = find_category_by_id(categories_data['result'], category_ids[0])
                    if found_category:
                        logger.info(f"  -> マッチしたカテゴリ: {found_category['categoryName']} (ID: {found_category['categoryId']})")
            else:
                logger.warning(f"  -> マッチするカテゴリが見つかりませんでした")
            
            logger.info("")  # 空行
        
        # 3. 楽天APIカテゴリ一覧の確認
        logger.info("--- 3. 楽天APIカテゴリ一覧の構造確認 ---")
        categories_data = fetch_rakuten_categories(app_id)
        if categories_data and 'result' in categories_data:
            result = categories_data['result']
            logger.info("カテゴリデータ取得成功")
            
            if isinstance(result, dict):
                # 新形式の場合
                for level_name in ['large', 'medium', 'small']:
                    if level_name in result:
                        categories = result[level_name]
                        logger.info(f"{level_name.upper()}カテゴリ: {len(categories)}件")
                        
                        # サンプルとして最初の5件を表示
                        for i, category in enumerate(categories[:5]):
                            cat_name = category.get('categoryName', 'N/A')
                            cat_id = category.get('categoryId', 'N/A')
                            logger.info(f"  例{i+1}: {cat_name} (ID: {cat_id})")
                        logger.info("")
            else:
                logger.info(f"旧形式（リスト）: {len(result)}件のカテゴリ")
        else:
            logger.error("カテゴリデータの取得に失敗しました")
        
        # 4. サンプルレシピの取得と表示（改良版）
        logger.info("--- 4. 改良版レシピ取得テスト ---")
        test_cases = [
            ("和風", "鶏肉"),
            ("洋風", "パスタ"),
            ("中華", None)
        ]
        
        for genre, keyword in test_cases:
            logger.info(f"=== {genre} レシピテスト (キーワード: {keyword}) ===")
            recipes = fetch_top_recipes_by_genre(genre, app_id, keyword)
            
            if recipes:
                logger.info(f"{genre} レシピ取得成功: {len(recipes)}件")
                # 最初のレシピの詳細表示
                if recipes:
                    first_recipe = recipes[0]
                    logger.info(f"サンプルレシピ: {first_recipe.get('recipeName', 'N/A')}")
                    logger.info(f"使用カテゴリID: {first_recipe.get('categoryId', 'N/A')}")
                    debug_display_json_data([first_recipe], f"{genre} サンプルレシピ")
            else:
                logger.warning(f"{genre} レシピの取得に失敗")
            
            logger.info(f"=== {genre} レシピテスト終了 ===")
            
    except Exception as e:
        logger.error(f"開発テストエラー: {str(e)}")
    finally:
        # デバッグモード無効化（通常動作に戻す）
        set_debug_mode(False)
        logger.info("=== 開発用テスト実行終了 ===")

# ---- env 読み込み ----
def load_env():
    logger.info("環境変数の読み込み開始")
    load_dotenv()
    env_data = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "RAKUTEN_APPLICATION_ID": os.getenv("RAKUTEN_APPLICATION_ID", ""),
        "SQLITE_PATH": os.getenv("SQLITE_PATH", ct.DEFAULT_SQLITE_PATH)
    }
    
    # APIキーの存在確認（セキュリティのため部分的にログ出力）
    openai_status = "設定済み" if env_data["OPENAI_API_KEY"].startswith("sk-") else "未設定"
    rakuten_status = "設定済み" if env_data["RAKUTEN_APPLICATION_ID"] else "未設定"
    
    logger.info(f"OPENAI_API_KEY: {openai_status}")
    logger.info(f"RAKUTEN_APPLICATION_ID: {rakuten_status}")
    logger.info(f"SQLITE_PATH: {env_data['SQLITE_PATH']}")
    logger.info("環境変数の読み込み完了")
    
    return env_data

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

# ---- 天気取得（Open-Meteo） ----
def fetch_weekly_weather(city: str) -> Dict[str, Any]:
    logger.info(f"天気情報取得開始 - 都市: {city}")
    try:
        lat, lon = ct.CITY_COORDS.get(city, ct.CITY_COORDS["Tokyo"])
        logger.info(f"座標取得 - 緯度: {lat}, 経度: {lon}")
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": "Asia/Tokyo"
        }
        
        r = requests.get(ct.OPEN_METEO_BASE, params=params, timeout=15)
        r.raise_for_status()
        
        weather_data = r.json()
        logger.info(f"天気情報取得成功 - データサイズ: {len(str(weather_data))} bytes")
        
        return weather_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"天気情報取得エラー (リクエスト): {str(e)}")
        return {}
    except Exception as e:
        logger.error(f"天気情報取得エラー (その他): {str(e)}")
        return {}

def temp_to_feel(temp_c: float) -> str:
    # 閾値に基づきラベル化
    if temp_c < ct.TEMP_FEEL_THRESHOLDS["寒い"]:
        return "寒い"
    elif temp_c < ct.TEMP_FEEL_THRESHOLDS["涼しい"]:
        return "涼しい"
    elif temp_c < ct.TEMP_FEEL_THRESHOLDS["快適"]:
        return "快適"
    elif temp_c < ct.TEMP_FEEL_THRESHOLDS["暑い"]:
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

# ---- 楽天API設定 ----
def safe_rakuten_api_request(url: str, params: Dict[str, Any], timeout: int = None) -> Dict[str, Any]:
    """
    楽天APIに対する安全なリクエスト（遅延・リトライ機能付き）
    
    Args:
        url: リクエストURL
        params: リクエストパラメータ
        timeout: タイムアウト時間（秒、Noneの場合はデフォルト値使用）
    
    Returns:
        APIレスポンス（JSONデータ）
    """
    if timeout is None:
        timeout = ct.RAKUTEN_API_TIMEOUT
    
    for attempt in range(ct.RAKUTEN_API_MAX_RETRIES + 1):
        try:
            if attempt > 0:
                retry_delay = ct.RAKUTEN_API_RETRY_DELAY * attempt
                logger.info(f"楽天API リトライ {attempt}/{ct.RAKUTEN_API_MAX_RETRIES} - {retry_delay}秒待機")
                time.sleep(retry_delay)
            else:
                # 通常の遅延
                logger.debug(f"楽天API リクエスト前遅延: {ct.RAKUTEN_API_DELAY}秒")
                time.sleep(ct.RAKUTEN_API_DELAY)
            
            logger.debug(f"楽天APIリクエスト - URL: {url}")
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
            
            result = r.json()
            logger.info(f"楽天APIリクエスト成功 - 試行回数: {attempt + 1}")
            return result
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning(f"楽天API レート制限 (429) - 試行 {attempt + 1}/{ct.RAKUTEN_API_MAX_RETRIES + 1}")
                if attempt == ct.RAKUTEN_API_MAX_RETRIES:
                    logger.error("楽天API レート制限により最大リトライ回数に到達")
                    raise
            else:
                logger.error(f"楽天API HTTPエラー: {e.response.status_code}")
                raise
        except requests.exceptions.RequestException as e:
            logger.error(f"楽天API リクエストエラー: {str(e)}")
            if attempt == ct.RAKUTEN_API_MAX_RETRIES:
                raise
        except Exception as e:
            logger.error(f"楽天API 予期しないエラー: {str(e)}")
            if attempt == ct.RAKUTEN_API_MAX_RETRIES:
                raise
    
    return {}

# ---- カテゴリデータのキャッシュ機能 ----
@st.cache_data(ttl=timedelta(hours=24))  # 24時間キャッシュ
def cached_fetch_rakuten_categories(app_id: str) -> Dict[str, Any]:
    """
    楽天レシピAPIからカテゴリ一覧を取得（キャッシュ付き・遅延対応）
    """
    logger.info("楽天レシピカテゴリ一覧取得開始（キャッシュ確認・遅延対応）")
    params = {"applicationId": app_id}
    
    try:
        result = safe_rakuten_api_request(ct.RAKUTEN_CATEGORY_LIST_URL, params)
        if result:
            logger.info("楽天カテゴリ一覧取得成功（キャッシュに保存）")
        return result
    except Exception as e:
        logger.error(f"カテゴリ取得エラー: {str(e)}")
        return {}

def fetch_rakuten_categories(app_id: str) -> Dict[str, Any]:
    """
    楽天レシピAPIからカテゴリ一覧を取得（遅延対応）
    デバッグや設定確認用の関数
    """
    logger.info("楽天レシピカテゴリ一覧取得開始（遅延対応）")
    params = {"applicationId": app_id}
    
    try:
        result = safe_rakuten_api_request(ct.RAKUTEN_CATEGORY_LIST_URL, params)
        if result:
            logger.info("楽天カテゴリ一覧取得成功")
        return result
    except Exception as e:
        logger.error(f"カテゴリ取得エラー: {str(e)}")
        return {}

def find_category_by_id(categories_result: Dict[str, Any], target_id: str) -> Dict[str, Any]:
    """
    カテゴリIDから対応するカテゴリ情報を検索
    
    Args:
        categories_result: 楽天APIのresult部分
        target_id: 検索対象のカテゴリID
    
    Returns:
        マッチしたカテゴリ情報（見つからない場合は空の辞書）
    """
    if isinstance(categories_result, dict):
        # 新形式：large/medium/small構造
        for level_name in ['large', 'medium', 'small']:
            if level_name in categories_result:
                categories = categories_result[level_name]
                for category in categories:
                    if str(category.get('categoryId', '')) == str(target_id):
                        return category
    elif isinstance(categories_result, list):
        # 旧形式：フラットなリスト
        for category in categories_result:
            if str(category.get('categoryId', '')) == str(target_id):
                return category
    
    return {}

def build_hierarchical_category_id(category_id: str, categories_data: dict) -> str:
    """
    カテゴリIDから階層形式のIDを構築する
    
    Args:
        category_id: 単体カテゴリID
        categories_data: カテゴリ一覧データ
    
    Returns:
        階層形式のカテゴリID（例: "30-300" または "30-300-1132"）
    """
    if not categories_data or 'result' not in categories_data:
        return category_id
    
    result = categories_data['result']
    
    # 各レベルでカテゴリIDを検索
    for level_name in ['large', 'medium', 'small']:
        if level_name in result:
            categories = result[level_name]
            
            for category in categories:
                if str(category.get('categoryId', '')) == str(category_id):
                    parent_id = category.get('parentCategoryId', '')
                    
                    if level_name == 'large':
                        # 大カテゴリの場合はそのまま
                        return category_id
                    elif level_name == 'medium':
                        # 中カテゴリの場合: 大-中
                        if parent_id:
                            return f"{parent_id}-{category_id}"
                        return category_id
                    elif level_name == 'small':
                        # 小カテゴリの場合: 大-中-小
                        if parent_id:
                            # 親（中カテゴリ）の階層IDを構築
                            parent_hierarchical = build_hierarchical_category_id(parent_id, categories_data)
                            return f"{parent_hierarchical}-{category_id}"
                        return category_id
    
    # 見つからない場合は元のIDをそのまま返す
    return category_id


# ---- 動的カテゴリ検索機能 ----
def search_category_by_keyword(app_id: str, keyword: str, genre_hint: str = None) -> List[str]:
    """
    キーワードまたはジャンルから適切なカテゴリIDを検索
    
    Args:
        app_id: 楽天アプリケーションID
        keyword: 検索キーワード（例: "鶏肉", "パスタ", "カレー"）
        genre_hint: ジャンルヒント（例: "和風", "洋風", "中華"）
    
    Returns:
        マッチしたカテゴリIDのリスト（優先度順）
    """
    logger.info(f"カテゴリ検索開始 - キーワード: '{keyword}', ジャンル: '{genre_hint}'")
    
    # カテゴリ一覧を取得（キャッシュ利用）
    categories_data = cached_fetch_rakuten_categories(app_id)
    if not categories_data or 'result' not in categories_data:
        logger.warning("カテゴリデータの取得に失敗")
        return []
    
    result = categories_data['result']
    matched_categories = []
    
    def calculate_relevance_score(category_name: str, category_id: str) -> float:
        """カテゴリの関連度スコアを計算（楽天APIのcategoryNameと直接照合）"""
        score = 0.0
        category_name_lower = category_name.lower()
        keyword_lower = keyword.lower() if keyword else ""
        genre_hint_lower = genre_hint.lower() if genre_hint else ""
        
        # 1. キーワードとの完全一致（最高優先度）
        if keyword_lower and keyword_lower == category_name_lower:
            score += 100.0
            logger.debug(f"完全一致: '{keyword}' == '{category_name}' (+100.0)")
        
        # 2. キーワードの部分一致（高優先度）
        elif keyword_lower and keyword_lower in category_name_lower:
            # 一致した部分の長さに応じてスコア調整
            match_ratio = len(keyword_lower) / len(category_name_lower)
            partial_score = 50.0 + (match_ratio * 30.0)  # 50-80点
            score += partial_score
            logger.debug(f"部分一致: '{keyword}' in '{category_name}' (+{partial_score:.1f})")
        
        # 3. カテゴリ名がキーワードに含まれる（逆方向の一致）
        elif keyword_lower and category_name_lower in keyword_lower:
            score += 40.0
            logger.debug(f"逆方向一致: '{category_name}' in '{keyword}' (+40.0)")
        
        # 4. ジャンルヒントとの一致
        if genre_hint_lower:
            # ジャンル名の直接一致
            if genre_hint_lower in category_name_lower:
                score += 25.0
                logger.debug(f"ジャンル一致: '{genre_hint}' in '{category_name}' (+25.0)")
            
            # ジャンル関連キーワード（楽天APIの実際のカテゴリ名から判定）
            japanese_indicators = ["和", "日本", "醤油", "味噌", "だし", "煮物", "焼き", "天ぷら", "寿司", "そば", "うどん", "丼"]
            western_indicators = ["洋", "イタリア", "フランス", "パスタ", "ピザ", "パン", "チーズ", "グラタン", "ステーキ", "ハンバーグ"]
            chinese_indicators = ["中華", "中国", "炒め", "餃子", "ラーメン", "チャーハン", "麻婆", "酢豚", "春巻き"]
            
            if genre_hint_lower in ["和風", "和食", "日本"]:
                for indicator in japanese_indicators:
                    if indicator in category_name_lower:
                        score += 15.0
                        logger.debug(f"和風指標一致: '{indicator}' in '{category_name}' (+15.0)")
                        break
            elif genre_hint_lower in ["洋風", "洋食", "西洋"]:
                for indicator in western_indicators:
                    if indicator in category_name_lower:
                        score += 15.0
                        logger.debug(f"洋風指標一致: '{indicator}' in '{category_name}' (+15.0)")
                        break
            elif genre_hint_lower in ["中華", "中国"]:
                for indicator in chinese_indicators:
                    if indicator in category_name_lower:
                        score += 15.0
                        logger.debug(f"中華指標一致: '{indicator}' in '{category_name}' (+15.0)")
                        break
        
        # 5. 食材・料理関連キーワードの文字レベル類似度
        if keyword_lower:
            # 共通文字の割合を計算
            common_chars = set(keyword_lower) & set(category_name_lower)
            if common_chars:
                char_similarity = len(common_chars) / max(len(keyword_lower), len(category_name_lower))
                char_score = char_similarity * 10.0  # 最大10点
                if char_score >= 3.0:  # 閾値設定
                    score += char_score
                    logger.debug(f"文字類似度: {char_similarity:.2f} (+{char_score:.1f})")
        
        # 6. カテゴリレベルによる重み付け（LARGEを優先）
        if isinstance(category_id, str):
            if len(category_id) == 1:  # LARGEカテゴリ
                score += 15.0
            elif len(category_id) == 2:  # MEDIUMカテゴリ
                score += 8.0
            elif len(category_id) == 3:  # SMALLカテゴリ
                score += 5.0
        
        return score
    
    # 各カテゴリレベルを検索（LARGEを最優先）
    if isinstance(result, dict):
        for level_name in ['large', 'medium', 'small']:  # LARGEを最優先
            if level_name in result:
                categories = result[level_name]
                logger.debug(f"{level_name.upper()}カテゴリから検索: {len(categories)}件")
                
                for category in categories:
                    cat_id = str(category.get('categoryId', ''))
                    cat_name = category.get('categoryName', '')
                    
                    if not cat_id or not cat_name:
                        continue
                    
                    # 関連度スコアを計算
                    score = calculate_relevance_score(cat_name, cat_id)
                    
                    if score > 0:
                        # 階層形式のカテゴリIDを構築
                        hierarchical_id = build_hierarchical_category_id(cat_id, categories_data)
                        
                        matched_categories.append({
                            'categoryId': hierarchical_id,
                            'originalId': cat_id,
                            'categoryName': cat_name,
                            'level': level_name,
                            'score': score
                        })
                        logger.debug(f"マッチ: {cat_name} (元ID: {cat_id} → 階層ID: {hierarchical_id}, レベル: {level_name}, スコア: {score:.1f})")
    elif isinstance(result, list):
        # 旧形式：フラットなリスト
        logger.debug(f"旧形式カテゴリから検索: {len(result)}件")
        for category in result:
            cat_id = str(category.get('categoryId', ''))
            cat_name = category.get('categoryName', '')
            
            if not cat_id or not cat_name:
                continue
            
            # 関連度スコアを計算
            score = calculate_relevance_score(cat_name, cat_id)
            
            if score > 0:
                # 旧形式の場合は階層変換をスキップ
                matched_categories.append({
                    'categoryId': cat_id,
                    'originalId': cat_id,
                    'categoryName': cat_name,
                    'level': 'unknown',
                    'score': score
                })
                logger.debug(f"マッチ: {cat_name} (ID: {cat_id}, スコア: {score:.1f})")
    
    # スコア順でソート
    matched_categories.sort(key=lambda x: x['score'], reverse=True)
    
    # 上位のカテゴリIDを返す
    top_category_ids = [cat['categoryId'] for cat in matched_categories[:5]]
    
    if top_category_ids:
        logger.info(f"カテゴリ検索完了 - マッチ数: {len(matched_categories)}, 上位ID: {top_category_ids[:3]}")
        # マッチした上位カテゴリの詳細をログ出力
        for i, cat in enumerate(matched_categories[:3]):
            original_info = f" (元ID: {cat.get('originalId', cat['categoryId'])})" if cat.get('originalId') and cat.get('originalId') != cat['categoryId'] else ""
            logger.info(f"  {i+1}. {cat['categoryName']} (階層ID: {cat['categoryId']}{original_info}, スコア: {cat['score']:.1f})")
    else:
        logger.warning(f"マッチするカテゴリが見つかりませんでした - キーワード: '{keyword}', ジャンル: '{genre_hint}'")
    
    return top_category_ids

def get_fallback_category_id(genre: str) -> str:
    """
    ジャンルに基づくフォールバックカテゴリID
    動的検索に失敗した場合の安全な選択肢
    """
    fallback_mapping = {
        "和風": "275",   # 牛肉（和風料理でよく使用）
        "洋風": "15",    # パスタ（洋風の代表）
        "中華": "277",   # 鶏肉（中華料理でよく使用）
    }
    
    category_id = fallback_mapping.get(genre, "30")  # デフォルトは人気メニュー
    logger.info(f"フォールバックカテゴリ使用 - ジャンル: {genre}, ID: {category_id}")
    return category_id

# ---- 開発用：JSONデータ表示機能 ----
def debug_display_json_data(data: Dict[str, Any], title: str = "JSON Data", max_depth: int = 3) -> None:
    """
    開発用：JSONデータの構造と内容を見やすく表示
    
    Args:
        data: 表示するJSONデータ
        title: 表示タイトル
        max_depth: 表示する最大深度
    """
    import json
    
    logger.info(f"=== {title} デバッグ表示開始 ===")
    
    try:
        # データサイズ情報
        json_str = json.dumps(data, ensure_ascii=False, indent=2)
        data_size = len(json_str)
        logger.info(f"データサイズ: {data_size:,} bytes")
        
        # 基本構造情報
        if isinstance(data, dict):
            logger.info(f"トップレベルキー数: {len(data)}")
            logger.info(f"トップレベルキー: {list(data.keys())}")
        elif isinstance(data, list):
            logger.info(f"配列要素数: {len(data)}")
            if data:
                logger.info(f"最初の要素タイプ: {type(data[0])}")
        
        # JSON整形表示（サイズ制限あり）
        if data_size < 50000:  # 50KB未満の場合のみ全体表示
            logger.info("=== JSON全体構造 ===")
            lines = json_str.split('\n')
            display_lines = min(200, len(lines))  # 最大200行まで
            for i in range(display_lines):
                logger.info(lines[i])
            if len(lines) > 200:
                logger.info(f"... 他 {len(lines)-200} 行")
        else:
            logger.info("データが大きいため、構造サマリーのみ表示")
            
        # カテゴリデータの場合の特別処理
        if isinstance(data, dict) and 'result' in data:
            _debug_display_category_data(data)
        elif isinstance(data, list) and data and 'recipeId' in str(data[0]):
            _debug_display_recipe_data(data)
            
    except Exception as e:
        logger.error(f"JSONデバッグ表示エラー: {str(e)}")
    
    logger.info(f"=== {title} デバッグ表示終了 ===")

def _debug_display_category_data(data: Dict[str, Any]) -> None:
    """カテゴリデータの詳細表示"""
    logger.info("=== カテゴリデータ詳細 ===")
    
    if 'result' in data:
        result = data['result']
        
        # カテゴリ構造の確認
        if isinstance(result, dict):
            logger.info(f"カテゴリ構造: {list(result.keys())}")
            
            # 各カテゴリレベルの表示
            for level_name in ['large', 'medium', 'small']:
                if level_name in result:
                    categories = result[level_name]
                    logger.info(f"--- {level_name.upper()}カテゴリ ---")
                    logger.info(f"カテゴリ数: {len(categories)}")
                    
                    # 最初の10件を表示
                    display_count = min(10, len(categories))
                    for i in range(display_count):
                        category = categories[i]
                        cat_id = category.get('categoryId', 'N/A')
                        cat_name = category.get('categoryName', 'N/A')
                        logger.info(f"  {i+1:2d}. ID:{cat_id:>6} | 名前:{cat_name}")
                    
                    if len(categories) > 10:
                        logger.info(f"  ... 他 {len(categories)-10} 件")
                    logger.info("")
        elif isinstance(result, list):
            # 旧形式（リスト）の場合
            logger.info(f"カテゴリ総数: {len(result)}")
            display_count = min(20, len(result))
            for i in range(display_count):
                category = result[i]
                cat_id = category.get('categoryId', 'N/A')
                cat_name = category.get('categoryName', 'N/A')
                parent_id = category.get('parentCategoryId', 'N/A')
                logger.info(f"  {i+1:2d}. ID:{cat_id:>3} | 親ID:{parent_id:>3} | 名前:{cat_name}")
            
            if len(result) > 20:
                logger.info(f"  ... 他 {len(result)-20} 件")

def _debug_display_recipe_data(data: List[Dict[str, Any]]) -> None:
    """レシピデータの詳細表示"""
    logger.info("=== レシピデータ詳細 ===")
    logger.info(f"レシピ総数: {len(data)}")
    
    display_count = min(10, len(data))  # 最初の10件のみ
    for i in range(display_count):
        recipe = data[i]
        recipe_id = recipe.get('recipeId', 'N/A')
        recipe_name = recipe.get('recipeName', recipe.get('recipeTitle', 'N/A'))
        cost = recipe.get('recipeCost', 'N/A')
        time = recipe.get('recipeIndication', 'N/A')
        materials_count = len(recipe.get('recipeMaterial', []))
        
        logger.info(f"  {i+1:2d}. ID:{recipe_id} | {recipe_name[:30]}{'...' if len(recipe_name) > 30 else ''}")
        logger.info(f"      コスト:{cost} | 時間:{time} | 材料数:{materials_count}")
    
    if len(data) > 10:
        logger.info(f"  ... 他 {len(data)-10} 件")

def debug_fetch_and_display_categories(app_id: str) -> None:
    """
    開発用：楽天レシピカテゴリを取得して詳細表示
    """
    logger.info("=== 開発用カテゴリ取得＆表示開始 ===")
    
    try:
        # カテゴリデータ取得
        categories_data = fetch_rakuten_categories(app_id)
        
        if not categories_data:
            logger.warning("カテゴリデータの取得に失敗しました")
            return
        
        # 詳細表示
        debug_display_json_data(categories_data, "楽天レシピカテゴリ一覧")
        
        # 使用可能なカテゴリIDのリスト表示
        if 'result' in categories_data:
            result = categories_data['result']
            logger.info("=== 使用可能カテゴリID参考リスト ===")
            
            if isinstance(result, dict):
                # 新形式：large/medium/small構造
                for level_name in ['large', 'medium', 'small']:
                    if level_name in result:
                        categories = result[level_name]
                        logger.info(f"--- {level_name.upper()}カテゴリ ---")
                        
                        display_count = min(10, len(categories))
                        for i in range(display_count):
                            category = categories[i]
                            cat_id = category.get('categoryId')
                            cat_name = category.get('categoryName')
                            if cat_id and cat_name:
                                logger.info(f"  '{cat_name}': '{cat_id}',")
                        
                        if len(categories) > 10:
                            logger.info(f"  ... 他 {len(categories)-10} 件")
                        logger.info("")
            elif isinstance(result, list):
                # 旧形式：フラットなリスト
                display_count = min(30, len(result))
                for i in range(display_count):
                    category = result[i]
                    cat_id = category.get('categoryId')
                    cat_name = category.get('categoryName')
                    if cat_id and cat_name:
                        logger.info(f"  '{cat_name}': '{cat_id}',")
                
                if len(result) > 30:
                    logger.info(f"  ... 他 {len(result)-30} 件")
                    
    except Exception as e:
        logger.error(f"開発用カテゴリ表示エラー: {str(e)}")
    
    logger.info("=== 開発用カテゴリ取得＆表示終了 ===")

# ---- 楽天レシピAPI から上位レシピ取得 ----
def fetch_top_recipes_by_genre(genre: str, app_id: str, keyword: str = None) -> List[Dict[str, Any]]:
    """
    楽天レシピAPIの動的カテゴリ検索に基づいてレシピを取得
    
    Args:
        genre: ジャンル（"和風", "洋風", "中華" など）
        app_id: 楽天アプリケーションID
        keyword: 検索キーワード（オプション）
    
    Returns:
        レシピ情報のリスト
    """
    logger.info(f"楽天レシピ取得開始 - ジャンル: {genre}, キーワード: {keyword}")
    
    # 動的カテゴリ検索
    category_ids = search_category_by_keyword(app_id, keyword or genre, genre)
    
    # フォールバック: 固定マッピングまたはデフォルト
    if not category_ids:
        # まず従来の固定マッピングを試行
        legacy_cat_id = ct.RAKUTEN_GENRE_TO_CATEGORY.get(genre)
        if legacy_cat_id:
            category_ids = [legacy_cat_id.split("-")[-1]]  # "10-277" -> "277"
            logger.info(f"従来マッピング使用 - ジャンル: {genre}, ID: {category_ids[0]}")
        else:
            category_ids = [get_fallback_category_id(genre)]
    
    # 最初のカテゴリIDでレシピを取得
    target_category_id = category_ids[0]
    logger.info(f"使用カテゴリID: {target_category_id}")
    
    # APIリクエストパラメータ
    params = {
        "applicationId": app_id,
        "categoryId": target_category_id
    }
    
    try:
        # 楽天レシピランキングAPIを呼び出し（遅延対応）
        logger.debug("楽天レシピAPIへリクエスト送信（遅延対応）")
        json_data = safe_rakuten_api_request(ct.RAKUTEN_RANKING_URL, params)
        
        if not json_data:
            logger.warning("楽天APIからの応答が空です")
            # 他のカテゴリIDで再試行
            if len(category_ids) > 1:
                logger.info(f"空応答のため別のカテゴリIDで再試行: {category_ids[1]}")
                return fetch_top_recipes_by_genre_with_category_id(category_ids[1], app_id, genre)
            return []
        
        logger.info("楽天レシピAPIからレスポンス受信（遅延対応）")
        
        # 開発用：取得したJSONデータの詳細表示（ログレベルがDEBUGの場合のみ）
        if logger.isEnabledFor(logging.DEBUG):
            debug_display_json_data(json_data, f"楽天レシピAPI レスポンス ({genre})")
        
        # レスポンス構造の確認とエラーハンドリング
        if 'result' not in json_data:
            logger.warning("APIレスポンスにresultキーが存在しません")
            logger.warning(f"レスポンス構造: {list(json_data.keys())}")
            
            # 他のカテゴリIDで再試行
            if len(category_ids) > 1:
                logger.info(f"別のカテゴリIDで再試行: {category_ids[1]}")
                return fetch_top_recipes_by_genre_with_category_id(category_ids[1], app_id, genre)
            return []
            
        # レシピデータを取得（上位N件）
        recipes_data = json_data['result'][:ct.RAKUTEN_TOP_N]
        logger.info(f"レシピデータ取得: {len(recipes_data)}件")
        
        recipes = []
        for i, recipe in enumerate(recipes_data):
            # 楽天レシピAPIの正式なフィールド名に基づいて情報を抽出
            recipe_info = {
                "recipeId": recipe.get("recipeId", ""),
                "recipeName": recipe.get("recipeTitle", ""),
                "recipeUrl": recipe.get("recipeUrl", ""),
                "foodImageUrl": recipe.get("foodImageUrl", ""),
                "recipeMaterial": recipe.get("recipeMaterial", []),
                "recipeCost": recipe.get("recipeCost", ""),
                "recipeIndication": recipe.get("recipeIndication", ""),
                "categoryId": target_category_id,
                "searchKeyword": keyword,
                "genre": genre
            }
            recipes.append(recipe_info)
            logger.debug(f"レシピ{i+1}: {recipe_info['recipeName']}")
            
        logger.info(f"楽天レシピ取得完了 - 取得件数: {len(recipes)}件")
        return recipes
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP エラー: {e.response.status_code}")
        
        # 他のカテゴリIDで再試行
        if len(category_ids) > 1:
            logger.info(f"HTTPエラーのため別のカテゴリIDで再試行: {category_ids[1]}")
            return fetch_top_recipes_by_genre_with_category_id(category_ids[1], app_id, genre)
        return []
        
    except Exception as e:
        logger.error(f"楽天レシピAPI エラー: {str(e)}")
        logger.debug("エラー詳細", exc_info=True)
        return []

def fetch_top_recipes_by_genre_with_category_id(category_id: str, app_id: str, genre: str) -> List[Dict[str, Any]]:
    """
    指定されたカテゴリIDでレシピを取得（再試行用・遅延対応）
    """
    logger.info(f"カテゴリID指定レシピ取得 - ID: {category_id}, ジャンル: {genre}（遅延対応）")
    
    params = {
        "applicationId": app_id,
        "categoryId": category_id
    }
    
    try:
        json_data = safe_rakuten_api_request(ct.RAKUTEN_RANKING_URL, params)
        
        if not json_data or 'result' not in json_data:
            logger.warning(f"カテゴリID {category_id} でもresultキーなし")
            return []
        
        recipes_data = json_data['result'][:ct.RAKUTEN_TOP_N]
        recipes = []
        
        for recipe in recipes_data:
            recipe_info = {
                "recipeId": recipe.get("recipeId", ""),
                "recipeName": recipe.get("recipeTitle", ""),
                "recipeUrl": recipe.get("recipeUrl", ""),
                "foodImageUrl": recipe.get("foodImageUrl", ""),
                "recipeMaterial": recipe.get("recipeMaterial", []),
                "recipeCost": recipe.get("recipeCost", ""),
                "recipeIndication": recipe.get("recipeIndication", ""),
                "categoryId": category_id,
                "genre": genre
            }
            recipes.append(recipe_info)
        
        logger.info(f"再試行成功 - 取得件数: {len(recipes)}件")
        return recipes
        
    except Exception as e:
        logger.error(f"再試行でもエラー: {str(e)}")
        return []

# ---- OpenAI でレシピの推定カロリー/PFC ----
def estimate_recipe_kcal_pfc_openai(
    recipe_name: str,
    ingredients: List[str],
    method: str,
    difficulty: str,
    budget_jpy: int,
    season: str,
    feel: str
) -> Dict[str, Any]:
    """OpenAIを使ってレシピの推定カロリー/PFCを取得"""
    logger.info(f"カロリー推定開始 - レシピ: {recipe_name}")
    logger.debug(f"材料数: {len(ingredients)}, 難易度: {difficulty}, 予算: {budget_jpy}円, 季節: {season}, 気温: {feel}")
    
    try:
        # 環境変数からOpenAI APIキーを取得
        env_data = load_env()
        os.environ["OPENAI_API_KEY"] = env_data["OPENAI_API_KEY"]
        
        llm = ChatOpenAI(
            model=ct.OPENAI_MODEL,
            temperature=0.3,
        )
        sys = SystemMessage(content=ct.SYSTEM_PROMPT)
        prompt = ct.RECIPE_KCAL_PROMPT.format(
            recipe_name=recipe_name,
            ingredients=", ".join(ingredients[:10]),
            method=method or "不明",
            difficulty=difficulty,
            budget_jpy=budget_jpy,
            season=season,
            feel=feel
        )
        user = HumanMessage(content=prompt)
        
        logger.info("OpenAI APIへリクエスト送信")
        resp = llm.invoke([sys, user])
        logger.info("OpenAI APIからレスポンス受信")
        
        # JSONパース（不正時は簡易推定）
        try:
            # レスポンスからJSON部分を抽出
            response_content = resp.content
            logger.debug(f"レスポンス内容: {response_content}")
            
            # レスポンスから```json```で囲まれたJSON部分を抽出
            import re
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                logger.debug(f"抽出されたJSON: {json_str}")
            else:
                # フォールバック: {}で囲まれたJSON部分を探す
                json_match = re.search(r'\{[^{}]*"kcal"[^{}]*\}', response_content)
                if json_match:
                    json_str = json_match.group(0)
                    logger.debug(f"フォールバック抽出JSON: {json_str}")
                else:
                    # 最後の手段: レスポンス全体をそのままJSONとして解析を試行
                    json_str = response_content
            
            obj = json.loads(json_str)
            kcal = float(obj.get("kcal", 0))
            p = float(obj.get("protein_g", 0))
            f = float(obj.get("fat_g", 0))
            c = float(obj.get("carb_g", 0))
            
            if (p+f+c) <= 0 and kcal > 0:
                # ざっくり配分
                p = kcal * ct.DEFAULT_PFC_RATIO["P"] / 4
                f = kcal * ct.DEFAULT_PFC_RATIO["F"] / 9
                c = kcal * ct.DEFAULT_PFC_RATIO["C"] / 4
                logger.info("PFC値をデフォルト比率で補完")
            
            result = {"kcal": kcal, "protein_g": p, "fat_g": f, "carb_g": c}
            logger.info(f"カロリー推定完了 - カロリー: {kcal:.1f}kcal, P: {p:.1f}g, F: {f:.1f}g, C: {c:.1f}g")
            return result
            
        except json.JSONDecodeError as e:
            logger.warning(f"AIレスポンスのJSON解析失敗: {str(e)}")
            logger.debug(f"レスポンス内容: {resp.content}")
            raise
            
    except Exception as e:
        logger.error(f"カロリー推定エラー: {str(e)}")
        logger.debug("エラー詳細", exc_info=True)
        
        # フォールバック（適当な安全値）
        kcal = 500.0
        result = {
            "kcal": kcal,
            "protein_g": kcal*ct.DEFAULT_PFC_RATIO["P"]/4,
            "fat_g": kcal*ct.DEFAULT_PFC_RATIO["F"]/9,
            "carb_g": kcal*ct.DEFAULT_PFC_RATIO["C"]/4,
        }
        logger.info(f"フォールバック値を使用 - カロリー: {kcal:.1f}kcal")
        return result

# ---- 応援メッセージ ----
def generate_cheer(summary: str) -> str:
    logger.info("応援メッセージ生成開始")
    logger.debug(f"サマリー内容: {summary[:100]}..." if len(summary) > 100 else f"サマリー内容: {summary}")
    
    try:
        # 環境変数からOpenAI APIキーを取得
        env_data = load_env()
        os.environ["OPENAI_API_KEY"] = env_data["OPENAI_API_KEY"]
        
        llm = ChatOpenAI(model=ct.OPENAI_MODEL, temperature=0.7)
        sys = SystemMessage(content=ct.SYSTEM_PROMPT)
        user = HumanMessage(content=ct.CHEER_PROMPT.format(summary=summary))
        
        logger.info("OpenAI APIへ応援メッセージリクエスト送信")
        resp = llm.invoke([sys, user])
        logger.info("応援メッセージ生成完了")
        
        message = resp.content.strip()
        logger.debug(f"生成メッセージ: {message[:50]}..." if len(message) > 50 else f"生成メッセージ: {message}")
        
        return message
        
    except Exception as e:
        logger.error(f"応援メッセージ生成エラー: {str(e)}")
        fallback_message = "今日もお疲れ様です！健康的な食生活を続けていきましょう！"
        logger.info(f"フォールバックメッセージを使用: {fallback_message}")
        return fallback_message

# ---- 残りカロリー計算 ----
def calc_remaining_kcal(target_kcal: int, consumed_today: float) -> float:
    return max(0.0, target_kcal - consumed_today)

def sum_today_kcal(db_path: str) -> float:
    logger.debug("今日の摂取カロリー合計計算開始")
    d = date.today().isoformat()
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT SUM(kcal) FROM meal_logs WHERE date = ?", (d,))
        row = cur.fetchone()
        conn.close()
        
        total_kcal = float(row[0]) if row and row[0] else 0.0
        logger.info(f"今日の摂取カロリー合計: {total_kcal:.1f}kcal")
        return total_kcal
        
    except Exception as e:
        logger.error(f"カロリー合計計算エラー: {str(e)}")
        return 0.0

# ---- 食事記録 ----
def insert_meal_log(db_path: str, meal_type: str, name: str, kcal: float):
    logger.info(f"食事記録追加 - 種類: {meal_type}, 名前: {name}, カロリー: {kcal:.1f}kcal")
    
    try:
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
        logger.info("食事記録追加完了")
        
    except Exception as e:
        logger.error(f"食事記録追加エラー: {str(e)}")
        raise

# ---- 非同期版のカロリー推定関数 ----
async def estimate_recipe_kcal_pfc_openai_async(
    openai_api_key: str,
    recipe_name: str,
    ingredients: List[str],
    method: str,
    difficulty: str,
    budget_jpy: int,
    season: str,
    feel: str
) -> Dict[str, Any]:
    """非同期版のカロリー推定関数"""
    # 基本的には同期版と同じロジックだが、非同期対応
    # 実際の実装では aiohttp や非同期対応のOpenAIクライアントを使用
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None, 
        estimate_recipe_kcal_pfc_openai,
        openai_api_key, recipe_name, ingredients, method, 
        difficulty, budget_jpy, season, feel
    )

# ---- Streamlit対応のバッチ処理機能 ----
def batch_estimate_recipes_sync(recipes: List[Dict], **kwargs) -> List[Dict]:
    """Streamlit環境でのバッチ処理（ThreadPoolExecutorを使用）"""
    import concurrent.futures
    import streamlit as st
    
    results = []
    total = len(recipes)
    
    # プログレスバーを表示
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 全てのタスクを投入
        future_to_recipe = {
            executor.submit(
                estimate_recipe_kcal_pfc_openai,
                recipe.get('recipeName', ''),
                recipe.get('recipeMaterial', []),
                recipe.get('recipeIndication', ''),
                kwargs['difficulty'],
                kwargs['budget_jpy'],
                kwargs['season'],
                kwargs['feel']
            ): recipe for recipe in recipes
        }
        
        # 完了したタスクから順次処理
        for i, future in enumerate(concurrent.futures.as_completed(future_to_recipe)):
            try:
                result = future.result()
                results.append(result)
                
                # プログレス更新
                progress = (i + 1) / total
                progress_bar.progress(progress)
                status_text.text(f'処理中... {i + 1}/{total}')
                
            except Exception as e:
                st.error(f"レシピ処理中にエラー: {str(e)}")
                # エラー時はデフォルト値を使用
                results.append({
                    "kcal": 500.0,
                    "protein_g": 31.25,
                    "fat_g": 13.89,
                    "carb_g": 62.5
                })
    
    # プログレスバーとステータステキストをクリア
    progress_bar.empty()
    status_text.empty()
    
    return results

# ---- キャッシュ機能の修正版 ----
@st.cache_data(ttl=timedelta(hours=1))
def cached_fetch_top_recipes_by_genre(genre: str, app_id: str) -> List[Dict]:
    return fetch_top_recipes_by_genre(genre, app_id)

@st.cache_data(ttl=timedelta(hours=6))
def cached_estimate_recipe_kcal_pfc(
    recipe_name: str, 
    ingredients_str: str,  # リストを文字列に変換してキャッシュキーに使用
    method: str,
    difficulty: str,
    budget_jpy: int,
    season: str,
    feel: str
) -> Dict:
    """キャッシュ対応のカロリー推定"""
    ingredients = ingredients_str.split(",") if ingredients_str else []
    return estimate_recipe_kcal_pfc_openai(
        recipe_name=recipe_name,
        ingredients=ingredients,
        method=method,
        difficulty=difficulty,
        budget_jpy=budget_jpy,
        season=season,
        feel=feel
    )

# ---- 改善されたエラーハンドリング付きレシピ取得 ----
def fetch_top_recipes_by_genre_improved(genre: str, app_id: str) -> List[Dict[str, Any]]:
    """エラーハンドリングを改善したレシピ取得（正式版・遅延対応）"""
    cat_id = ct.RAKUTEN_GENRE_TO_CATEGORY.get(genre)
    if not cat_id:
        st.warning(f"ジャンル '{genre}' に対応するカテゴリが見つかりません。")
        return []
    
    params = {
        "applicationId": app_id,
        "categoryId": cat_id
    }
    
    try:
        json_data = safe_rakuten_api_request(ct.RAKUTEN_RANKING_URL, params)
        
        if not json_data:
            st.info("該当するレシピが見つかりませんでした。別のジャンルをお試しください。")
            return []
        
        # APIレスポンスの構造確認
        if 'result' not in json_data:
            st.info("該当するレシピが見つかりませんでした。別のジャンルをお試しください。")
            return []
            
        recipes_data = json_data['result'][:ct.RAKUTEN_TOP_N]
        recipes = []
        
        for recipe in recipes_data:
            recipes.append({
                "recipeId": recipe.get("recipeId", ""),
                "recipeName": recipe.get("recipeTitle", "不明なレシピ"),
                "recipeUrl": recipe.get("recipeUrl", ""),
                "foodImageUrl": recipe.get("foodImageUrl", ""),
                "recipeMaterial": recipe.get("recipeMaterial", []),
                "recipeCost": recipe.get("recipeCost", ""),
                "recipeIndication": recipe.get("recipeIndication", ""),
                "categoryId": cat_id
            })
        return recipes
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            st.error("楽天レシピAPIの設定に問題があります。カテゴリIDを確認してください。")
        elif e.response.status_code == 401:
            st.error("APIキーが無効です。設定を確認してください。")
        elif e.response.status_code == 429:
            st.error("APIの利用制限に達しました。しばらく待ってから再試行してください。")
        else:
            st.error(f"APIエラーが発生しました (ステータス: {e.response.status_code})")
        return []
        
    except requests.exceptions.ConnectionError:
        st.error("インターネット接続を確認してください。")
        return []
        
    except requests.exceptions.Timeout:
        st.error("APIの応答時間が長すぎます。しばらく待ってから再試行してください。")
        return []
        
    except Exception as e:
        st.error(f"予期しないエラーが発生しました: {str(e)}")
        return []