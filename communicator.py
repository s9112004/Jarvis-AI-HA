import os, telebot, time, threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from core import queue_manager
from core.logger import logger  # 🌟 引入全知之眼

load_dotenv()
bot = telebot.TeleBot(os.getenv("TG_TOKEN"))
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

telebot.apihelper.RETRY_ON_ERROR = True

# 🌟 新增的網路保險絲：強制 Telegram 連線與讀取的超時時間
telebot.apihelper.CONNECT_TIMEOUT = 10  # 嘗試連線超過 10 秒就放棄
telebot.apihelper.READ_TIMEOUT = 15     # 等待伺服器回應超過 15 秒就放棄

@bot.message_handler(commands=['model'])
def model_switch_command(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🚀 Flash", callback_data="setmodel_gemini-3.0-flash"),
        InlineKeyboardButton("🧠 Pro", callback_data="setmodel_gemini-3.1-pro")
    )
    try:
        bot.reply_to(message, "先生，請選擇邏輯核心：", reply_markup=markup)
        logger.info("已發送模型切換選單。")
    except Exception as e:
        logger.error(f"發送模型選單失敗: {e}", exc_info=True)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try:
        if call.data.startswith("setmodel_"):
            new_model = call.data.split("_")[1]
            queue_manager.add_task(call.message.chat.id, call.message.message_id, new_model, "switch_model")
            bot.edit_message_text(f"⚙️ 正在切換核心至 `{new_model}`，已加入排程...", call.message.chat.id, call.message.message_id)
            logger.info(f"使用者請求切換模型至: {new_model}")
        elif call.data.startswith("keep_") or call.data.startswith("drop_"):
            queue_manager.add_task(call.message.chat.id, call.message.message_id, call.data, "evolution_decision")
            bot.answer_callback_query(call.id, "決策已排入處理序列。")
            logger.info(f"收到進化決策: {call.data}")
    except Exception as e:
        logger.error(f"按鈕處理回覆失敗: {e}", exc_info=True)

@bot.message_handler(func=lambda message: True)
def handle_incoming(message):
    current_state = queue_manager.get_state()
    logger.info(f"收到來自先生的新訊息: {message.text[:20]}... (當前大腦狀態: {current_state})")
    
    try:
        if current_state == "BUSY":
            bot.reply_to(message, "⏳ 先生，我正在處理上一個指令（運算中），您的需求已排入序列，我稍後為您處理。")
        else:
            bot.reply_to(message, "⚙️ 收到指令，正在交由大腦處理...")
    except Exception as e:
        logger.warning(f"網路抖動，無法發送確認訊息，但指令已攔截: {e}")
        
    queue_manager.add_task(message.chat.id, message.message_id, message.text, "chat")

def response_listener():
    while True:
        completed_tasks = queue_manager.get_completed_tasks()
        for task in completed_tasks:
            try:
                bot.send_message(task['chat_id'], task['response'], reply_to_message_id=task['message_id'])
                logger.info(f"✅ 成功發送任務 ID[{task['id']}] 的回覆給先生。")
                queue_manager.delete_task(task['id'])
            except Exception as e:
                # 記錄嚴重錯誤，方便未來除錯
                logger.error(f"發送回覆失敗 (任務 ID: {task['id']}): {e}", exc_info=True)
                if "empty" in str(e).lower() or "forbidden" in str(e).lower():
                    logger.warning(f"偵測到不可恢復的錯誤，放棄任務 ID[{task['id']}]。")
                    queue_manager.delete_task(task['id'])
        time.sleep(2)

if __name__ == "__main__":
    logger.info("📡 賈維斯收發室準備上線...")
    threading.Thread(target=response_listener, daemon=True).start()
    
    while True:
        try:
            logger.info("🔄 啟動通訊輪詢，等待指令...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            logger.error(f"通訊中斷 (Errno 101 等原因)，10 秒後嘗試重連...", exc_info=True)
            time.sleep(10)