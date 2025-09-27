# Dockerfile
FROM python:3.11-slim

# システム依存のビルドに必要なもの（必要最低限）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依存関係
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリ配置
COPY . /app

# Streamlitのネットワーク設定
ENV STREAMLIT_PORT=8501
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

# 本番エントリ（開発は devcontainer から実行でもOK）
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]