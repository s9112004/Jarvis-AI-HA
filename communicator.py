import os
import threading
import time

import telebot
from dotenv import load_dotenv
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from core import queue_manager
from core.logger import logger
from core.network_health import network_health
from core.startup_checks import run_startup_checks

load_dotenv()

TG_TOKEN = os.getenv("TG_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

if not TG_TOKEN:
    raise RuntimeError("TG_TOKEN 未設定，請先確認 .env 或系統環境變數。")

bot = telebot.TeleBot(TG_TOKEN)

# 交給我們自己的 retry / backoff 控制
telebot.apihelper.RETRY_ON_ERROR = False
telebot.apihelper.CONNECT_TIMEOUT = 10
telebot.apihelper.READ_TIMEOUT = 15

MAX_SEND_RETRIES = 10
SEND_RETRY_BASE_DELAY = 5
SEND_RETRY_MAX_DELAY = 300
LISTENER_IDLE_SLEEP_SECONDS = 2
HEARTBEAT_INTERVAL_SECONDS = 60


def _preview_text(text, limit=20):
    if text is None:
        return "<空內容>"
    text = str(text).replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _extract_message_text(message):
    text = getattr(message, "text", None) or getattr(message, "caption", None)
    if text is None:
        return None
    text = text.strip()
    return text if text else None


def _calculate_backoff(retry_count, base_delay=5, max_delay=300):
    retry_count = max(1, int(retry_count))
    delay = base_delay * (2 ** (retry_count - 1))
    return min(delay, max_delay)


def _is_network_error(exc):
    error_text = str(exc).lower()

    keywords = [
        "network is unreachable",
        "connection",
        "unreachable",
        "timeout",
        "timed out",
        "connect timeout",
        "read timeout",
        "read timed out",
        "max retries exceeded",
        "temporary failure",
        "name or service not known",
        "dns",
        "remote disconnected",
        "connection reset",
        "connection aborted",
        "broken pipe",
        "errno 101",
    ]
    return any(keyword in error_text for keyword in keywords)


def _is_reply_target_missing_error(exc):
    error_text = str(exc).lower()
    return "message to reply not found" in error_text


def _is_permanent_send_error(exc):
    error_text = str(exc).lower()

    permanent_keywords = [
        "forbidden",
        "bot was blocked by the user",
        "user is deactivated",
        "chat not found",
        "message text is empty",
        "have no rights to send a message",
        "not enough rights",
    ]
    return any(keyword in error_text for keyword in permanent_keywords)


def _send_task_response(task):
    response_text = task.get("response") or "⚠️ 任務已完成，但沒有可發送的內容。"
    chat_id = task["chat_id"]
    message_id = task.get("message_id")

    try:
        if message_id:
            return bot.send_message(chat_id, response_text, reply_to_message_id=message_id)
        return bot.send_message(chat_id, response_text)
    except Exception as e:
        if _is_reply_target_missing_error(e):
            logger.warning(
                f"[trace:{task.get('trace_id')}] ⚠️ 原始訊息已不可回覆，改為直接發送一般訊息。"
            )
            return bot.send_message(chat_id, response_text)
        raise


def _format_health_snapshot():
    snapshot = network_health.snapshot()
    if not snapshot:
        return "目前尚無健康狀態資料。"

    lines = []
    for name, info in snapshot.items():
        status = info.get("status", "UNKNOWN")
        retry_after = info.get("retry_after_seconds", 0)
        last_error = info.get("last_error")
        line = f"- {name}: {status}"
        if retry_after:
            line += f"（{retry_after} 秒後再試）"
        if last_error:
            line += f" | last_error={last_error}"
        lines.append(line)

    return "\n".join(lines)


def heartbeat_worker():
    while True:
        try:
            stats = queue_manager.get_queue_stats()
            health = network_health.snapshot()
            logger.info(f"💓 heartbeat queue={stats} health={health}")
        except Exception as e:
            logger.warning(f"heartbeat 記錄失敗: {e}")
        time.sleep(HEARTBEAT_INTERVAL_SECONDS)


@bot.message_handler(commands=["model"])
def model_switch_command(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🚀 Flash", callback_data="setmodel_gemini-3.0-flash"),
        InlineKeyboardButton("🧠 Pro", callback_data="setmodel_gemini-3.1-pro"),
    )

    try:
        bot.reply_to(message, "先生，請選擇邏輯核心：", reply_markup=markup)
        logger.info("已發送模型切換選單。")
    except Exception as e:
        logger.error(f"發送模型選單失敗: {e}", exc_info=True)


@bot.message_handler(commands=["health"])
def health_command(message):
    try:
        text = "🩺 Jarvis 健康狀態\n\n"
        text += f"系統狀態: {queue_manager.get_state()}\n\n"
        text += _format_health_snapshot()
        bot.reply_to(message, text)
    except Exception as e:
        logger.error(f"/health 回覆失敗: {e}", exc_info=True)


@bot.message_handler(commands=["queue"])
def queue_command(message):
    try:
        stats = queue_manager.get_queue_stats()
        lines = ["📦 目前佇列狀態"]
        for k, v in stats.items():
            lines.append(f"- {k}: {v}")
        bot.reply_to(message, "\n".join(lines))
    except Exception as e:
        logger.error(f"/queue 回覆失敗: {e}", exc_info=True)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try:
        if call.data.startswith("setmodel_"):
            new_model = call.data.split("setmodel_", 1)[1]
            created = queue_manager.add_task(
                call.message.chat.id,
                call.message.message_id,
                new_model,
                "switch_model",
                source="telegram",
            )
            bot.edit_message_text(
                f"⚙️ 正在切換核心至 `{new_model}`，已加入排程...",
                call.message.chat.id,
                call.message.message_id,
            )
            logger.info(f"[trace:{created['trace_id']}] 使用者請求切換模型至: {new_model}")

        elif call.data.startswith("keep_") or call.data.startswith("drop_"):
            created = queue_manager.add_task(
                call.message.chat.id,
                call.message.message_id,
                call.data,
                "evolution_decision",
                source="telegram",
            )
            bot.answer_callback_query(call.id, "決策已排入處理序列。")
            logger.info(f"[trace:{created['trace_id']}] 收到進化決策: {call.data}")

    except Exception as e:
        logger.error(f"按鈕處理回覆失敗: {e}", exc_info=True)


@bot.message_handler(func=lambda message: True)
def handle_incoming(message):
    incoming_text = _extract_message_text(message)
    current_state = queue_manager.get_state()

    if not incoming_text:
        try:
            bot.reply_to(message, "⚠️ 目前只支援文字指令。")
        except Exception as e:
            logger.warning(f"無法回覆不支援的訊息類型: {e}")
        return

    if incoming_text.startswith("/"):
        logger.info(f"略過一般文字佇列，交由指令處理: {incoming_text}")
        return

    created = queue_manager.add_task(
        message.chat.id,
        message.message_id,
        incoming_text,
        "chat",
        source="telegram",
    )
    trace_id = created["trace_id"]

    logger.info(
        f"[trace:{trace_id}] 收到來自先生的新訊息: "
        f"{_preview_text(incoming_text)} (當前大腦狀態: {current_state})"
    )

    try:
        if current_state == "BUSY":
            bot.reply_to(
                message,
                "⏳ 先生，我正在處理上一個指令，您的需求已排入序列，我稍後為您處理。"
            )
        else:
            bot.reply_to(message, "⚙️ 收到指令，正在交由大腦處理...")
    except Exception as e:
        logger.warning(f"[trace:{trace_id}] 網路抖動，無法發送確認訊息，但指令已成功入列: {e}")


def response_listener():
    while True:
        task = queue_manager.claim_next_outgoing_task()

        if not task:
            time.sleep(LISTENER_IDLE_SLEEP_SECONDS)
            continue

        task_id = task["id"]
        trace_id = task.get("trace_id") or "unknown"
        send_retry_count = int(task.get("send_retry_count") or 0)

        can_attempt, wait_seconds = network_health.can_attempt("telegram")
        if not can_attempt:
            queue_manager.mark_send_failed(
                task_id,
                "telegram circuit open",
                delay_seconds=wait_seconds,
                permanent=False,
                increment_retry=False,
            )
            logger.warning(
                f"[trace:{trace_id}] ⚠️ Telegram 離線保護中，任務 ID[{task_id}] "
                f"延後 {wait_seconds} 秒再送。"
            )
            time.sleep(0.2)
            continue

        try:
            _send_task_response(task)
            network_health.mark_success("telegram")
            logger.info(f"[trace:{trace_id}] ✅ 成功發送任務 ID[{task_id}] 的回覆給先生。")
            queue_manager.delete_task(task_id)

        except Exception as e:
            error_text = str(e)

            if _is_permanent_send_error(e):
                logger.warning(
                    f"[trace:{trace_id}] ⚠️ 不可恢復的 Telegram 發送錯誤，"
                    f"任務 ID[{task_id}] 將標記為 FAILED: {e}"
                )
                queue_manager.mark_send_failed(
                    task_id,
                    error_text,
                    permanent=True,
                )
                continue

            if _is_network_error(e):
                network_health.mark_failure("telegram", e)

            next_retry_count = send_retry_count + 1
            if next_retry_count > MAX_SEND_RETRIES:
                logger.error(
                    f"[trace:{trace_id}] ❌ 任務 ID[{task_id}] 已達發送重試上限，最後錯誤: {e}",
                    exc_info=True
                )
                queue_manager.mark_send_failed(
                    task_id,
                    f"send retry limit reached: {error_text}",
                    permanent=True,
                )
                continue

            delay = _calculate_backoff(
                next_retry_count,
                base_delay=SEND_RETRY_BASE_DELAY,
                max_delay=SEND_RETRY_MAX_DELAY,
            )
            queue_manager.mark_send_failed(
                task_id,
                error_text,
                delay_seconds=delay,
                permanent=False,
                increment_retry=True,
            )

            if _is_network_error(e):
                logger.warning(
                    f"[trace:{trace_id}] ⚠️ Telegram 發送疑似遇到網路異常，"
                    f"任務 ID[{task_id}] 將於 {delay} 秒後進行第 {next_retry_count} 次重送..."
                )
            else:
                logger.error(
                    f"[trace:{trace_id}] 發送回覆失敗 (任務 ID: {task_id})，"
                    f"{delay} 秒後重送: {e}",
                    exc_info=True
                )


if __name__ == "__main__":
    logger.info("📡 賈維斯收發室準備上線...")
    run_startup_checks(logger)

    threading.Thread(target=response_listener, daemon=True).start()
    threading.Thread(target=heartbeat_worker, daemon=True).start()

    while True:
        try:
            logger.info("🔄 啟動通訊輪詢，等待指令...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            network_health.mark_failure("telegram", e)
            logger.error("通訊輪詢中斷，10 秒後嘗試重連...", exc_info=True)
            time.sleep(10)