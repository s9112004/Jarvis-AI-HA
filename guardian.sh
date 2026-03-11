#!/bin/bash

# 定義專案路徑與指令
PROJECT_DIR="/home/s9112004/homeassistant/Jarvis-AI-HA"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
MAIN_FILE="main.py"

echo "🛡️ 賈維斯守護者已啟動..."

while true; do
    # 檢查 main.py 是否正在執行 (排除掉 grep 自己)
    if ps aux | grep -v grep | grep "$MAIN_FILE" > /dev/null; then
        # 賈維斯還活著，我們安靜地等待
        sleep 10
    else
        echo "[$(date)] ⚠️ 偵測到賈維斯失聯或崩潰！"
        echo "[$(date)] 🚀 正在執行緊急復甦程序..."
        
        # 切換到目錄並啟動
        cd $PROJECT_DIR
        $PYTHON_BIN $MAIN_FILE &
        
        echo "[$(date)] ✅ 賈維斯已重新上線。"
        sleep 5
    fi
done