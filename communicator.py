import os, telebot, time, threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from core import queue_manager  # 引入新武器

load_dotenv()
bot = telebot.TeleBot(os.getenv("TG_TOKEN"))
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")


# --- 模型切換 ---
@bot.message_handler(commands=['model'])
def model_switch_command(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🚀 Flash", callback_data="setmodel_gemini-2.0-flash"),
        InlineKeyboardButton("🧠 Pro", callback_data="setmodel_gemini-2.0-pro-exp-02-05")
    )
    bot.reply_to(message, "先生，請選擇邏輯核心：", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("setmodel_"):
        new_model = call.data.split("_")[1]
        queue_manager.add_task(call.message.chat.id, call.message.message_id, new_model, "switch_model")
        bot.edit_message_text(f"⚙️ 正在切換核心至 `{new_model}`，已加入排程...", call.message.chat.id,
                              call.message.message_id)
    elif call.data.startswith("keep_") or call.data.startswith("drop_"):
        queue_manager.add_task(call.message.chat.id, call.message.message_id, call.data, "evolution_decision")
        bot.answer_callback_query(call.id, "決策已排入處理序列。")


# --- 對話收發處理 ---
@bot.message_handler(func=lambda message: True)
def handle_incoming(message):
    # 🌟 核心防禦機制：先看大腦忙不忙
    current_state = queue_manager.get_state()

    if current_state == "BUSY":
        bot.reply_to(message, "⏳ 先生，我正在處理上一個指令（運算中），您的需求已排入序列，我稍後為您處理。")
    else:
        bot.reply_to(message, "⚙️ 收到指令，正在交由大腦處理...")

    # 安全地將任務存入 SQLite
    queue_manager.add_task(message.chat.id, message.message_id, message.text, "chat")


def response_listener():
    """背景巡邏隊：只負責把大腦算好的答案發出去"""
    while True:
        completed_tasks = queue_manager.get_completed_tasks()
        for task in completed_tasks:
            try:
                bot.send_message(task['chat_id'], task['response'], reply_to_message_id=task['message_id'])
                queue_manager.delete_task(task['id'])  # 發送成功才刪除
            except Exception as e:
                print(f"❌ 發送回覆失敗: {e}")
                # 如果是空訊息錯誤，還是要刪除，避免無限卡住
                if "empty" in str(e).lower():
                    queue_manager.delete_task(task['id'])
        time.sleep(2)


if __name__ == "__main__":
    print("📡 賈維斯收發室 (SQLite 版) 已上線。")
    threading.Thread(target=response_listener, daemon=True).start()
    # 長輪詢參數保守設定
    bot.infinity_polling(timeout=20, long_polling_timeout=10)