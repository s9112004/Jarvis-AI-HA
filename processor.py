import time
from core import queue_manager
from core import ai_brain
from core.logger import logger  # 🌟 引入全知之眼

def work():
    logger.info("🧠 賈維斯參謀部已啟動，具備斷線重試防護...")
    while True:
        task = queue_manager.get_next_pending_task()
        
        if not task:
            time.sleep(1)
            continue
            
        logger.info(f"⚙️ 開始處理排隊任務 ID[{task['id']}]: {task['text'][:30]}...")
        
        queue_manager.set_state("BUSY")
        queue_manager.mark_task_processing(task['id'])
        
        try:
            if task['task_type'] == "switch_model":
                ai_brain.switch_model(task['text'])
                response_text = f"✅ 先生，核心已成功切換為 `{task['text']}`。"
                logger.info(f"模型切換成功: {task['text']}")
                
            elif task['task_type'] == "chat":
                response_text = ai_brain.generate_jarvis_response(task['text'])
                
                if "神經連線出現異常" in response_text or "無法完成運算" in response_text:
                    raise ConnectionError("AI Brain Network Drop")
                    
            elif task['task_type'] == "evolution_decision":
                response_text = "✅ 技能決策已處理。"
            else:
                response_text = "❌ 未知的任務類型。"
                
            queue_manager.mark_task_completed(task['id'], response_text)
            logger.info(f"✅ 任務 ID[{task['id']}] 大腦運算完畢，等待通訊官發送。")
            
        except Exception as e:
            error_str = str(e).lower()
            if "network drop" in error_str or "101" in error_str or "connection" in error_str or "unreachable" in error_str:
                logger.warning(f"⚠️ 偵測到網路斷流！任務 ID[{task['id']}] 將被保留，10 秒後自動重試...")
                
                with queue_manager.get_conn() as conn:
                    conn.cursor().execute('UPDATE tasks SET status="PENDING" WHERE id=?', (task['id'],))
                    conn.commit()
                time.sleep(10)
            else:
                logger.error(f"系統運算發生未知異常，任務中斷: {e}", exc_info=True)
                error_msg = f"❌ 系統運算異常，任務中斷: {e}"
                queue_manager.mark_task_completed(task['id'], error_msg)
                
        finally:
            queue_manager.set_state("IDLE")

if __name__ == "__main__":
    work()