# Git操作手順書

## 前提条件
- DockerコンテナにGitがインストール済み
- GitHubアカウントとリポジトリが準備済み

## 初回セットアップ

### 1. Gitユーザー設定
```bash
git config --global user.name "あなたの名前"
git config --global user.email "your@email.com"
```

### 2. セーフディレクトリ設定（コンテナ環境用）
```bash
git config --global --add safe.directory /app
```

### 3. Gitリポジトリ初期化（新規の場合）
```bash
# リポジトリ初期化
git init

# リモートリポジトリ追加
git remote add origin https://github.com/username/repository.git
```

## ファイルのアップロード手順

### 1. 変更状態の確認
```bash
# 現在の状態確認
git status

# 変更内容の確認
git diff
```

### 2. ファイルの追加
```bash
# 全ファイル追加
git add .

# または特定ファイルのみ
git add main.py utils.py components.py
```

### 3. コミット
```bash
git commit -m "feat: NutriBuddy機能の更新"
```

### 4. プッシュ
```bash
# 通常のプッシュ
git push

# 初回プッシュの場合（上流ブランチ設定）
git push -u origin main
```

## よく使うGitコマンド

### ブランチ操作
```bash
# 現在のブランチ確認
git branch

# 新しいブランチ作成と切り替え
git checkout -b feature/new-feature

# ブランチ切り替え
git checkout main
```

### 履歴確認
```bash
# コミット履歴確認
git log --oneline

# リモートリポジトリ確認
git remote -v
```

### 変更の取り消し
```bash
# ステージング取り消し
git reset HEAD <ファイル名>

# ワーキングディレクトリの変更取り消し
git checkout -- <ファイル名>
```

## 認証について

### HTTPSの場合
- GitHub Personal Access Tokenを使用
- パスワード入力時にトークンを入力

### SSHの場合
```bash
# SSH鍵生成
ssh-keygen -t ed25519 -C "your@email.com"

# 公開鍵をGitHubに登録後
git remote set-url origin git@github.com:username/repository.git
```

## 推奨ファイル構成

アップロード対象の主要ファイル：
- `main.py` - メインアプリケーション
- `utils.py` - ユーティリティ関数
- `components.py` - UIコンポーネント
- `constants.py` - 定数定義
- `initialize.py` - 初期化処理
- `requirements.txt` - Python依存関係
- `Dockerfile` - Docker設定
- `README.md` - プロジェクト説明
- `.gitignore` - Git除外設定

## 注意事項

1. **機密情報の除外**
   - `.env`ファイルは`.gitignore`で除外済み
   - APIキーやパスワードはコミットしない

2. **ログファイルの扱い**
   - `logs/`ディレクトリは`.gitignore`で除外済み
   - 開発用ログは含めない

3. **データベースファイル**
   - `nutribuddy.db`は`.gitignore`で除外済み
   - 本番データは含めない

## 推奨コミットメッセージ形式

```
feat: 新機能追加
fix: バグ修正
docs: ドキュメント更新
style: コードフォーマット
refactor: リファクタリング
test: テスト追加
chore: その他の変更
```

例：
```bash
git commit -m "feat: カテゴリ一覧のJSONデバッグ表示機能を追加"
git commit -m "fix: カロリー計算のバグを修正"
git commit -m "docs: README.mdにセットアップ手順を追加"
```