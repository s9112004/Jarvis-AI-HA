#!/usr/bin/env bash
set -u

PROJECT_DIR="/home/s9112004/homeassistant/Jarvis-AI-HA"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
LOG_DIR="$PROJECT_DIR/logs"
LOCK_FILE="/tmp/jarvis_guardian.lock"

COMMUNICATOR="$PROJECT_DIR/communicator.py"
PROCESSOR="$PROJECT_DIR/processor.py"

mkdir -p "$LOG_DIR"

# 防止同時啟動多個 guardian
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "[$(date '+%F %T')] ⚠️ guardian 已經在執行中，結束本次啟動。"
    exit 1
fi

echo "[$(date '+%F %T')] 🛡️ 賈維斯【雙核心守護者】已啟動..."
echo "[$(date '+%F %T')] 專案路徑: $PROJECT_DIR"
echo "[$(date '+%F %T')] Python 路徑: $PYTHON_BIN"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "[$(date '+%F %T')] ❌ PROJECT_DIR 不存在: $PROJECT_DIR"
    exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
    echo "[$(date '+%F %T')] ❌ PYTHON_BIN 不存在或不可執行: $PYTHON_BIN"
    exit 1
fi

if [ ! -f "$COMMUNICATOR" ]; then
    echo "[$(date '+%F %T')] ❌ 找不到 communicator.py: $COMMUNICATOR"
    exit 1
fi

if [ ! -f "$PROCESSOR" ]; then
    echo "[$(date '+%F %T')] ❌ 找不到 processor.py: $PROCESSOR"
    exit 1
fi

cd "$PROJECT_DIR" || exit 1

is_running() {
    local target="$1"
    pgrep -f "$PYTHON_BIN $target" > /dev/null 2>&1
}

start_service() {
    local name="$1"
    local target="$2"
    local logfile="$3"

    echo "[$(date '+%F %T')] 🚀 啟動 [$name] ..."
    nohup "$PYTHON_BIN" "$target" >> "$logfile" 2>&1 &
    sleep 2

    if is_running "$target"; then
        echo "[$(date '+%F %T')] ✅ [$name] 啟動成功。"
    else
        echo "[$(date '+%F %T')] ❌ [$name] 啟動失敗，請檢查 $logfile"
    fi
}

while true; do
    if ! is_running "$COMMUNICATOR"; then
        echo "[$(date '+%F %T')] ⚠️ 偵測到 [通訊官] 失聯！正在執行緊急復甦..."
        start_service "通訊官" "$COMMUNICATOR" "$LOG_DIR/communicator.out.log"
    fi

    if ! is_running "$PROCESSOR"; then
        echo "[$(date '+%F %T')] ⚠️ 偵測到 [參謀部] 停機！正在重新點火..."
        start_service "參謀部" "$PROCESSOR" "$LOG_DIR/processor.out.log"
    fi

    sleep 10
done