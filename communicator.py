import os
import telebot
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

# 引入我們剛建立的 SQLite 佇列管理器
from core import queue_manager

# 1. 載入環境變數
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

if not TELEGRAM_TOKEN:
    print("❌ 致命錯誤：找不到 [TG_TOKEN]！請檢查 .env 檔案。")
    exit(1)

# 初始化 Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)


# ==========================================
# 🛠️ 模型切換與按鈕指令
# ==========================================
@bot.message_handler(commands=['model'])
def model_switch_command(message):
    """呼叫模型切換選單"""
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🚀 Flash (快速)", callback_data="setmodel_gemini-2.0-flash"),
        InlineKeyboardButton("🧠 Pro (最強)", callback_data="setmodel_gemini-2.0-pro-exp-02-05")
    )
    bot.reply_to(message, "先生，請選擇您希望我使用的邏輯核心：", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    """處理所有的按鈕點擊事件"""
    if call.data.startswith("setmodel_"):
        new_model = call.data.split("_")[1]
        # 將切換模型的任務排入 SQLite
        queue_manager.add_task(call.message.chat.id, call.message.message_id, new_model, "switch_model")
        bot.edit_message_text(f"⚙️ 正在切換核心至 `{new_model}`，已加入排程...", call.message.chat.id,
                              call.message.message_id)

    elif call.data.startswith("keep_") or call.data.startswith("drop_"):
        # 將進化決策排入 SQLite
        queue_manager.add_task(call.message.chat.id, call.message.message_id, call.data, "evolution_decision")
        bot.answer_callback_query(call.id, "決策已排入處理序列。")


# ==========================================
# 💬 一般對話收發處理 (紅綠燈機制)
# ==========================================
@bot.message_handler(func=lambda message: True)
def handle_incoming(message):
    """接收訊息並安全地存入資料庫佇列"""
    # 🌟 核心防禦：先看大腦目前忙不忙
    current_state = queue_manager.get_state()

    if current_state == "BUSY":
        bot.reply_to(message, "⏳ 先生，我正在處理上一個指令（運算中），您的需求已排入序列，我稍後為您處理。")
    else:
        bot.reply_to(message, "⚙️ 收到指令，正在交由大腦處理...")

    # 安全地將任務存入 SQLite，絕不卡死通訊
    queue_manager.add_task(message.chat.id, message.message_id, message.text, "chat")


# ==========================================
# 📡 背景發送巡邏隊
# ==========================================
def response_listener():
    """獨立執行緒：只負責從資料庫撈取大腦算好的答案並發送"""
    while True:
        try:
            completed_tasks = queue_manager.get_completed_tasks()
            for task in completed_tasks:
                try:
                    # 嘗試發送回覆
                    bot.send_message(task['chat_id'], task['response'], reply_to_message_id=task['message_id'])
                    # 發送成功才從資料庫刪除該任務
                    queue_manager.delete_task(task['id'])
                except Exception as e:
                    print(f"❌ 發送回覆失敗 (Task ID {task['id']}): {e}")
                    # 如果是空訊息錯誤等無效請求，強制刪除避免無限卡死
                    if "empty" in str(e).lower() or "not found" in str(e).lower():
                        queue_manager.delete_task(task['id'])
        except Exception as db_e:
            print(f"❌ 巡邏隊讀取資料庫異常: {db_e}")

        time.sleep(2)


# ==========================================
# 🚀 系統啟動 (開機防彈衣版)
# ==========================================
if __name__ == "__main__":
    print("📡 賈維斯收發室 (SQLite 防彈版) 準備上線...")

    # 1. 啟動背景發送巡邏隊
    threading.Thread(target=response_listener, daemon=True).start()

    # 2. 告訴 Telegram 套件：遇到網路波動請自行重試，不要當機
    telebot.apihelper.RETRY_ON_ERROR = True

    # 3. 🛡️ 終極防彈衣：阻擋啟動時與運行中的 Errno 101
    while True:
        try:
            print("🔄 正在嘗試與 Telegram 建立穩定連線...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            # 攔截所有致命連線錯誤
            print(f"\n⚠️ 網路暫時無法到達或發生斷線: {e}")
            print("⏳ 10 秒後重新嘗試連線，期間收發室暫停收信...")
            time.sleep(10)