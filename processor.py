import time, os, json
from core import ai_brain

QUEUE_FILE = "task_queue.json"


def work():
    print("🧠 賈維斯參謀部已啟動，準備處理複雜運算...")
    while True:
        if os.path.exists(QUEUE_FILE):
            try:
                with open(QUEUE_FILE, "r+") as f:
                    tasks = json.load(f)
                    if not tasks:
                        time.sleep(1);
                        continue
                    task = tasks.pop(0)
                    f.seek(0);
                    json.dump(tasks, f);
                    f.truncate()

                # --- 根據任務類型處理 ---
                if task['type'] == "switch_model":
                    ai_brain.switch_model(task['model_name'])
                    response_text = f"✅ 先生，核心已切換為 `{task['model_name']}`。我現在感覺更靈敏了。"

                elif task['type'] == "chat":
                    response_text = ai_brain.generate_jarvis_response(task['text'])

                # --- 寫回結果 ---
                result_path = f"reply_{int(time.time() * 1000)}.json"
                with open(result_path, "w") as f:
                    json.dump({"chat_id": task['chat_id'], "text": response_text, "msg_id": task.get('msg_id')}, f)

            except Exception as e:
                print(f"❌ 參謀部運作異常: {e}")
        time.sleep(0.5)


if __name__ == "__main__":
    work()