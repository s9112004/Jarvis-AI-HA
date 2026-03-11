import time
from core import queue_manager
from core import ai_brain


def work():
    print("🧠 賈維斯參謀部已啟動，準備進行安全運算...")
    while True:
        # 1. 拿取最新的任務
        task = queue_manager.get_next_pending_task()

        if not task:
            time.sleep(1)
            continue

        print(f"⚙️ 開始處理排隊任務 ID[{task['id']}]: {task['text'][:20]}...")

        # 2. 🌟 上鎖：宣告大腦忙碌中
        queue_manager.set_state("BUSY")
        queue_manager.mark_task_processing(task['id'])

        try:
            # 3. 根據任務類型進行運算
            if task['task_type'] == "switch_model":
                ai_brain.switch_model(task['text'])
                response_text = f"✅ 先生，核心已成功切換為 `{task['text']}`。"

            elif task['task_type'] == "chat":
                response_text = ai_brain.generate_jarvis_response(task['text'])

            elif task['task_type'] == "evolution_decision":
                # 未來若需處理決策邏輯可放此
                response_text = "✅ 技能決策已處理。"
            else:
                response_text = "❌ 未知的任務類型。"

            # 4. 運算成功，寫入結果
            queue_manager.mark_task_completed(task['id'], response_text)
            print(f"✅ 任務 ID[{task['id']}] 處理完畢。")

        except Exception as e:
            # 發生任何錯誤，將錯誤訊息回傳給通訊官
            error_msg = f"❌ 系統運算異常，任務中斷: {e}"
            print(error_msg)
            queue_manager.mark_task_completed(task['id'], error_msg)

        finally:
            # 5. 🌟 絕對解鎖：不管成功失敗，都要把狀態改回空閒
            queue_manager.set_state("IDLE")


if __name__ == "__main__":
    work()