import time

from core import ai_brain
from core import queue_manager
from core.logger import logger
from core.network_health import network_health
from core.startup_checks import run_startup_checks

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


def _service_name_for_task(task_type):
    if task_type == "chat":
        return "gemini"
    if task_type == "smart_home":
        return "home_assistant"
    return "general"


def work():
    logger.info("🧠 賈維斯參謀部已啟動，具備穩定版斷線重試防護...")
    run_startup_checks(logger)

    while True:
        task = queue_manager.claim_next_pending_task()

        if not task:
            queue_manager.set_state("IDLE")
            time.sleep(IDLE_SLEEP_SECONDS)
            continue

        task_id = task["id"]
        trace_id = task.get("trace_id") or "unknown"
        task_type = task.get("task_type")
        task_text = task.get("text") or ""
        retry_count = int(task.get("process_retry_count") or 0)
        service_name = _service_name_for_task(task_type)

        can_attempt, wait_seconds = network_health.can_attempt(service_name)
        if not can_attempt:
            queue_manager.requeue_task(
                task_id,
                delay_seconds=wait_seconds,
                error=f"{service_name} circuit open",
                increment_retry=False,
            )
            logger.warning(
                f"[trace:{trace_id}] ⚠️ {service_name} 目前離線保護中，"
                f"任務 ID[{task_id}] 延後 {wait_seconds} 秒再試。"
            )
            time.sleep(0.2)
            continue

        logger.info(
            f"[trace:{trace_id}] ⚙️ 開始處理排隊任務 ID[{task_id}] "
            f"type={task_type} text={_preview_text(task_text)}"
        )
        queue_manager.set_state("BUSY")

        try:
            if task_type == "switch_model":
                ai_brain.switch_model(task_text)
                response_text = f"✅ 先生，核心已成功切換為 `{task_text}`。"

            elif task_type == "chat":
                raw_response = ai_brain.generate_jarvis_response(task_text)
                response_text = _normalize_ai_response(raw_response)

            elif task_type == "evolution_decision":
                response_text = "✅ 技能決策已處理。"

            elif task_type == "smart_home":
                # 這裡先保留掛點，之後你要接 smart_home.py 可直接換掉
                response_text = "✅ 智慧家庭任務已收到，待後續模組處理。"

            else:
                response_text = "❌ 未知的任務類型。"

            network_health.mark_success(service_name)
            queue_manager.mark_task_completed(
                task_id,
                response_text,
                finished_reason="completed",
            )
            logger.info(f"[trace:{trace_id}] ✅ 任務 ID[{task_id}] 運算完畢，等待通訊官發送。")

        except Exception as e:
            if _is_network_error(e):
                network_health.mark_failure(service_name, e)
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
                        f"[trace:{trace_id}] ⚠️ 偵測到外部連線異常，任務 ID[{task_id}] "
                        f"將於 {delay} 秒後進行第 {next_retry_count} 次重試。error={e}"
                    )
                else:
                    logger.error(
                        f"[trace:{trace_id}] ❌ 任務 ID[{task_id}] 已達處理重試上限。error={e}",
                        exc_info=True
                    )
                    queue_manager.mark_task_completed(
                        task_id,
                        "❌ 目前外部連線仍不穩定，這次任務已停止重試，請稍後再試。",
                        error=str(e),
                        finished_reason="process_retry_exhausted",
                    )

            else:
                logger.error(
                    f"[trace:{trace_id}] 系統運算發生未知異常，任務中斷: {e}",
                    exc_info=True
                )
                queue_manager.mark_task_completed(
                    task_id,
                    "❌ 系統運算發生異常，這次任務已中止，請稍後再試。",
                    error=str(e),
                    finished_reason="processor_exception",
                )

        finally:
            queue_manager.set_state("IDLE")


if __name__ == "__main__":
    work()