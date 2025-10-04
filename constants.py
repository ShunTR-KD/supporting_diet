# constants.py
from datetime import date

# --------- LLM / モデル ----------
OPENAI_MODEL = "gpt-4o-mini"

# --------- UI / 初期値 ----------
DEFAULT_TARGET_KCAL = 1800
DEFAULT_MEAL_BUDGET_JPY = 500  # 1食あたりの予算
DEFAULT_MEAL_KCAL = 600       # 1食あたりの希望カロリー
DEFAULT_DIFFICULTY = "初心者"   # "初心者" / "中級者"
DEFAULT_GENRE = "和風"          # "和風" / "洋風" / "中華"
DEFAULT_LOCATION = "Tokyo"

MEAL_TYPES = ["朝", "昼", "晩"]
DIFFICULTY_OPTIONS = ["初心者", "中級者"]
GENRE_OPTIONS = ["和風", "洋風", "中華"]

MEAL_ICONS = ":material/restaurant:"
CUSTOM_ICONS = ":material/settings:"
SCHEDULE_ICONS = ":material/calendar_today:"
RECIPE_ICONS = ":material/local_dining:"

# --------- 楽天レシピ サイト ----------
RAKUTEN_CATEGORY_LIST_URL = "https://app.rakuten.co.jp/services/api/Recipe/CategoryList/20170426"
RAKUTEN_RANKING_URL = "https://app.rakuten.co.jp/services/api/Recipe/CategoryRanking/20170426"

# 楽天API設定
RAKUTEN_API_DELAY = 1.2  # 楽天APIリクエスト間の基本遅延（秒）
RAKUTEN_API_RETRY_DELAY = 3.0  # リトライ時の遅延（秒）
RAKUTEN_API_MAX_RETRIES = 3  # 最大リトライ回数
RAKUTEN_API_TIMEOUT = 25  # タイムアウト時間（秒）

# カテゴリIDマッピング（楽天レシピAPIの構造に基づく）
RAKUTEN_GENRE_TO_CATEGORY = {
    "和風": "10-275",   # 牛肉カテゴリ（和風料理の代表として一旦仮置き）
    "洋風": "10-276",   # 豚肉カテゴリ（洋風料理の代表として一旦仮置き）  
    "中華": "10-277",   # 鶏肉カテゴリ（中華料理の代表として一旦仮置き）
}

RAKUTEN_TOP_N = 4  # 上位4件

# --------- 天気（Open-Meteo） ----------
# 都市→緯度経度
CITY_COORDS = {
    "Tokyo": (35.6895, 139.6917),
    "Osaka": (34.6937, 135.5023),
    "Sapporo": (43.0618, 141.3545),
    "Fukuoka": (33.5902, 130.4017),
}
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

# 温度感の閾値
TEMP_FEEL_THRESHOLDS = {
    "寒い": 10,
    "涼しい": 18,
    "快適": 24,
    "暑い": 30
}

# --------- PFC / 栄養 ----------
# 簡易係数（例）：総カロリーからP/F/Cをざっくり配分（LangChain出力の補助）
DEFAULT_PFC_RATIO = {"P": 0.25, "F": 0.25, "C": 0.50}

# --------- SQLite ----------
DEFAULT_SQLITE_PATH = "./nutribuddy.db"

# --------- プロンプト（応援メッセージ） ----------
SYSTEM_PROMPT = """あなたは思いやりのある管理栄養士AIです。
ユーザーの努力をねぎらい、前向きな短い応援メッセージを日本語で添えます。
語尾は明るく丁寧に。上から目線はNG。"""
# レシピの推定カロリー+PFC
RECIPE_KCAL_PROMPT = """以下の料理について、1人前の推定カロリー(kcal)とPFC(たんぱく質/脂質/炭水化物のグラム)を出力してください。
出力はJSONで、例:
{{"kcal": 520, "protein_g": 28, "fat_g": 18, "carb_g": 60}}
料理名: {recipe_name}
主材料: {ingredients}
調理法: {method}
難易度: {difficulty}
予算: {budget_jpy}円
考慮: 季節({season}), 天気の体感({feel})
注意: 数値は妥当な範囲で整数または少数。日本の一般的な分量を想定。"""

# 応援メッセージ
CHEER_PROMPT = """以下の条件に合う、短い1文の応援メッセージを出してください（30〜50文字目安）。
条件:
- ダイエットを頑張る人への共感と励まし
- 提案レシピのダイエット効果を一言で説明（カロリー調整、栄養バランス、満足感など）
- 今日の提案内容を後押し
- ポジティブ、やさしい口調
- 絵文字は1個まで
- 「〜で」「〜から」などでダイエット効果と応援を自然に繋げる
提案の要約: {summary}"""