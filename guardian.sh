#!/bin/bash

# 定義專案路徑與指令
PROJECT_DIR="/home/s9112004/homeassistant/Jarvis-AI-HA"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"

echo "🛡️ 賈維斯【雙核心守護者】已啟動..."

# 切換到專案目錄，確保 SQLite 資料庫等相對路徑讀取正確
cd $PROJECT_DIR

while true; do
    # 1. 巡邏通訊官 (收發室)
    if ! ps aux | grep -v grep | grep "communicator.py" > /dev/null; then
        echo "[$(date)] ⚠️ 偵測到 [通訊官] 失聯！正在執行緊急復甦..."
        $PYTHON_BIN communicator.py &
        sleep 2
    fi

    # 2. 巡邏參謀部 (大腦)
    if ! ps aux | grep -v grep | grep "processor.py" > /dev/null; then
        echo "[$(date)] ⚠️ 偵測到 [參謀部] 停機！正在重新點火..."
        $PYTHON_BIN processor.py &
        sleep 2
    fi

    # 每 10 秒巡邏一次
    sleep 10
done