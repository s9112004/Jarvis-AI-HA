import time
from core import ai_brain
from core import queue_manager
from core.logger import logger

MAX_PROCESS_RETRIES = 6
PROCESS_RETRY_BASE_DELAY = 10
PROCESS_RETRY_MAX_DELAY = 300
IDLE_SLEEP_SECONDS = 1


def _preview_text(text, limit=30):
    if text is None:
        return "<空內容>"
    text = str(text).replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def _calculate_backoff(retry_count, base_delay=10, max_delay=300):
    retry_count = max(1, int(retry_count))
    delay = base_delay * (2 ** (retry_count - 1))
    return min(delay, max_delay)


def _is_network_error(exc):
    error_text = str(exc).lower()

    keywords = [
        "network drop",
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
        "returned none",
        "returned empty response",
    ]
    return any(keyword in error_text for keyword in keywords)


def _normalize_ai_response(response_text):
    if response_text is None:
        raise ConnectionError("AI Brain returned None")

    if not isinstance(response_text, str):
        raise TypeError(f"AI Brain returned invalid type: {type(response_text).__name__}")

    clean_text = response_text.strip()
    if not clean_text:
        raise ConnectionError("AI Brain returned empty response")

    if "神經連線出現異常" in clean_text or "無法完成運算" in clean_text:
        raise ConnectionError("AI Brain Network Drop")

    return clean_text


def work():
    logger.info("🧠 賈維斯參謀部已啟動，具備穩定版斷線重試防護...")

    while True:
        task = queue_manager.claim_next_pending_task()

        if not task:
            queue_manager.set_state("IDLE")
            time.sleep(IDLE_SLEEP_SECONDS)
            continue

        task_id = task["id"]
        task_type = task.get("task_type")
        task_text = task.get("text") or ""
        retry_count = int(task.get("process_retry_count") or 0)

        logger.info(f"⚙️ 開始處理排隊任務 ID[{task_id}]: {_preview_text(task_text)}")
        queue_manager.set_state("BUSY")

        try:
            if task_type == "switch_model":
                ai_brain.switch_model(task_text)
                response_text = f"✅ 先生，核心已成功切換為 `{task_text}`。"
                logger.info(f"模型切換成功: {task_text}")

            elif task_type == "chat":
                raw_response = ai_brain.generate_jarvis_response(task_text)
                response_text = _normalize_ai_response(raw_response)

            elif task_type == "evolution_decision":
                response_text = "✅ 技能決策已處理。"

            else:
                response_text = "❌ 未知的任務類型。"

            queue_manager.mark_task_completed(task_id, response_text)
            logger.info(f"✅ 任務 ID[{task_id}] 大腦運算完畢，等待通訊官發送。")

        except Exception as e:
            if _is_network_error(e):
                next_retry_count = retry_count + 1

                if next_retry_count <= MAX_PROCESS_RETRIES:
                    delay = _calculate_backoff(
                        next_retry_count,
                        base_delay=PROCESS_RETRY_BASE_DELAY,
                        max_delay=PROCESS_RETRY_MAX_DELAY,
                    )
                    queue_manager.requeue_task(
                        task_id,
                        delay_seconds=delay,
                        error=str(e),
                        increment_retry=True,
                    )
                    logger.warning(
                        f"⚠️ 偵測到外部連線異常！任務 ID[{task_id}] 將保留，"
                        f"{delay} 秒後進行第 {next_retry_count} 次重試..."
                    )
                else:
                    logger.error(
                        f"❌ 任務 ID[{task_id}] 已達處理重試上限，最後錯誤: {e}",
                        exc_info=True
                    )
                    queue_manager.mark_task_completed(
                        task_id,
                        "❌ 目前外部連線仍不穩定，這次任務已停止重試，請稍後再試。",
                        error=str(e),
                    )
            else:
                logger.error(f"系統運算發生未知異常，任務中斷: {e}", exc_info=True)
                queue_manager.mark_task_completed(
                    task_id,
                    "❌ 系統運算發生異常，這次任務已中止，請稍後再試。",
                    error=str(e),
                )

        finally:
            queue_manager.set_state("IDLE")


if __name__ == "__main__":
    work()