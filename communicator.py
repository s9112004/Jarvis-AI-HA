import os, telebot, time, threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from core import queue_manager

load_dotenv()
bot = telebot.TeleBot(os.getenv("TG_TOKEN"))
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

# 告訴底層套件遇到錯誤自動重試
telebot.apihelper.RETRY_ON_ERROR = True


@bot.message_handler(commands=['model'])
def model_switch_command(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🚀 Flash", callback_data="setmodel_gemini-3-flash-preview"),
        InlineKeyboardButton("🧠 Pro", callback_data="setmodel_gemini-3.1-pro-preview"),
    )
    try:
        bot.reply_to(message, "先生，請選擇邏輯核心：", reply_markup=markup)
    except Exception as e:
        print(f"⚠️ 發送模型選單失敗: {e}")


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    try:
        if call.data.startswith("setmodel_"):
            new_model = call.data.split("_")[1]
            queue_manager.add_task(call.message.chat.id, call.message.message_id, new_model, "switch_model")
            bot.edit_message_text(f"⚙️ 正在切換核心至 `{new_model}`，已加入排程...", call.message.chat.id,
                                  call.message.message_id)
        elif call.data.startswith("keep_") or call.data.startswith("drop_"):
            queue_manager.add_task(call.message.chat.id, call.message.message_id, call.data, "evolution_decision")
            bot.answer_callback_query(call.id, "決策已排入處理序列。")
    except Exception as e:
        print(f"⚠️ 按鈕處理回覆失敗: {e}")


@bot.message_handler(func=lambda message: True)
def handle_incoming(message):
    current_state = queue_manager.get_state()

    # 🌟 絕對防禦：就算發送「收到指令」時網路斷了，任務也要存進資料庫
    try:
        if current_state == "BUSY":
            bot.reply_to(message, "⏳ 先生，我正在處理上一個指令（運算中），您的需求已排入序列，我稍後為您處理。")
        else:
            bot.reply_to(message, "⚙️ 收到指令，正在交由大腦處理...")
    except Exception as e:
        print(f"⚠️ 網路抖動，無法發送確認訊息，但指令已攔截: {e}")

    queue_manager.add_task(message.chat.id, message.message_id, message.text, "chat")


def response_listener():
    while True:
        completed_tasks = queue_manager.get_completed_tasks()
        for task in completed_tasks:
            try:
                bot.send_message(task['chat_id'], task['response'], reply_to_message_id=task['message_id'])
                queue_manager.delete_task(task['id'])
            except Exception as e:
                print(f"❌ 發送回覆失敗: {e}")
                # 如果是空訊息或被封鎖，直接刪除任務，以免卡死迴圈
                if "empty" in str(e).lower() or "forbidden" in str(e).lower():
                    queue_manager.delete_task(task['id'])
        time.sleep(2)


if __name__ == "__main__":
    print("📡 賈維斯收發室 (防彈版) 準備上線...")
    threading.Thread(target=response_listener, daemon=True).start()

    while True:
        try:
            print("🔄 啟動通訊輪詢...")
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"⚠️ 通訊中斷 (Errno 101)，10 秒後重連: {e}")
            time.sleep(10)