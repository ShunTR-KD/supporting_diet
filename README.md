# NutriBuddy（ニュートリバディ）

「あなたの努力を見守り、毎日応援してくれる管理栄養士ダイエットパートナーAI」

## 機能概要

- **AI食事記録**: OpenAI APIを使った栄養素推定
- **レシピ提案**: 楽天レシピAPIから人気レシピを取得
- **カロリー管理**: 目標カロリーと摂取カロリーの管理
- **週間献立**: 1週間分の献立自動生成
- **天気連動**: 気候に応じたレシピ推薦
- **応援メッセージ**: AIによる励ましメッセージ

## ログ機能

アプリケーションの動作状況、API呼び出し、エラー情報を詳細にログファイルに記録します。

### ログファイル
- **保存場所**: `logs/nutribuddy_YYYYMMDD.log`
- **ローテーション**: 日次（毎日新しいファイル）
- **レベル**: INFO, WARNING, ERROR, DEBUG

### ログ内容
- アプリケーション開始/終了
- API呼び出し（楽天レシピAPI、OpenAI API）
- データベース操作
- ユーザー操作（ボタンクリック、設定変更）
- エラー詳細（スタックトレース付き）
- 処理時間とパフォーマンス情報

### ログ例
```
2025-10-01 07:57:55,442 - NutriBuddy - INFO - NutriBuddy アプリケーション開始
2025-10-01 07:57:55,445 - main - INFO - ユーザー設定 - 目標カロリー: 2000kcal, 予算: 800JPY, 場所: Tokyo
2025-10-01 07:57:56,123 - utils - INFO - 楽天レシピ取得開始 - ジャンル: 和食
2025-10-01 07:57:56,456 - utils - INFO - OpenAI APIへリクエスト送信
2025-10-01 07:57:57,789 - utils - INFO - カロリー推定完了 - カロリー: 485.0kcal
```

## 技術スタック

- **Frontend**: Streamlit
- **AI**: OpenAI GPT-3.5-turbo, LangChain
- **API**: 楽天レシピAPI, Open-Meteo Weather API
- **Database**: SQLite
- **Logging**: Python logging (日次ローテーション)
- **Container**: Docker

## セットアップ

### 環境変数
```env
OPENAI_API_KEY=your_openai_api_key
RAKUTEN_APPLICATION_ID=your_rakuten_app_id
SQLITE_PATH=./nutribuddy.db
```

### 実行方法
```bash
# 依存関係インストール
pip install -r requirements.txt

# Streamlitアプリ起動
streamlit run main.py
```

### Docker実行
```bash
docker-compose up --build
```

## ファイル構成

- `main.py`: メインアプリケーション
- `utils.py`: ユーティリティ関数（API呼び出し、ログ設定）
- `components.py`: Streamlit UI コンポーネント
- `constants.py`: 定数定義
- `initialize.py`: 初期化処理
- `logs/`: ログファイル保存ディレクトリ

## ログ監視

ログファイルをリアルタイムで監視する場合：
```bash
tail -f logs/nutribuddy_$(date +%Y%m%d).log
```
