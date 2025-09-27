# constants.py
from datetime import date

# --------- LLM / モデル ----------
OPENAI_MODEL = "gpt-4o-mini"

# --------- UI / 初期値 ----------
DEFAULT_TARGET_KCAL = 1800
DEFAULT_MEAL_BUDGET_JPY = 500  # 1食あたりの予算
DEFAULT_DIFFICULTY = "初心者"   # "初心者" / "中級者"
DEFAULT_GENRE = "和風"          # "和風" / "洋風" / "中華"
DEFAULT_LOCATION = "Tokyo"

MEAL_TYPES = ["朝", "昼", "晩"]
DIFFICULTY_OPTIONS = ["初心者", "中級者"]
GENRE_OPTIONS = ["和風", "洋風", "中華"]

# --------- 楽天レシピ API（雛形） ----------
RAKUTEN_BASE_URL = "https://app.rakuten.co.jp/services/api/Recipe/RecipeCategoryRanking/20170426"
# 実運用では上記を公式に合わせて更新してください（エンドポイント/バージョンは例）
# ジャンル→カテゴリIDの仮マップ（実運用時に正確なカテゴリIDへ更新）
RAKUTEN_GENRE_TO_CATEGORY = {
    "和風": "30-1",   # 例: 和食系のカテゴリID（仮）
    "洋風": "27-1",   # 例: 洋食系
    "中華": "36-1",   # 例: 中華系
}

RAKUTEN_TOP_N = 4  # 上位4件

# --------- 天気（Open-Meteo 仮） ----------
# 都市→緯度経度（簡易、必要に応じて増やしてください）
CITY_COORDS = {
    "Tokyo": (35.6895, 139.6917),
    "Osaka": (34.6937, 135.5023),
    "Sapporo": (43.0618, 141.3545),
    "Fukuoka": (33.5902, 130.4017),
}
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

# 温度感の閾値（お好みで調整）
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
CHEER_PROMPT = """以下の条件に合う、短い1文の応援メッセージを出してください（20〜40文字目安）。
条件:
- ダイエットを頑張る人への共感
- 今日の提案内容を後押し
- ポジティブ、やさしい口調
- 絵文字は1個まで
提案の要約: {summary}"""