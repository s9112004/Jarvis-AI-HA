import os, telebot, json, time, threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
bot = telebot.TeleBot(os.getenv("TG_TOKEN"))
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")
QUEUE_FILE = "task_queue.json"


# --- 模型切換指令 ---
@bot.message_handler(commands=['model'])
def model_switch_command(message):
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("🚀 Flash (快速)", callback_data="setmodel_gemini-3-flash-preview"),
        InlineKeyboardButton("🧠 Pro (最強)", callback_data="setmodel_gemini-3.1-pro-preview")
    )
    bot.reply_to(message, "先生，請選擇您希望我使用的邏輯核心：", reply_markup=markup)


# --- 處理所有按鈕回饋 ---
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    if call.data.startswith("setmodel_"):
        new_model = call.data.split("_")[1]
        # 發送一個特殊的切換任務給 Processor
        add_task_to_queue({"type": "switch_model", "model_name": new_model, "chat_id": call.message.chat.id})
        bot.edit_message_text(f"⚙️ 正在切換核心至 `{new_model}`，請稍候...", call.message.chat.id,
                              call.message.message_id)

    elif call.data.startswith("keep_") or call.data.startswith("drop_"):
        # 轉發給 Processor 處理進化決策
        add_task_to_queue({"type": "evolution_decision", "data": call.data, "chat_id": call.message.chat.id,
                           "msg_id": call.message.message_id})
        bot.answer_callback_query(call.id, "決策已送交參謀部。")


# --- 一般訊息處理 ---
@bot.message_handler(func=lambda message: True)
def handle_incoming(message):
    bot.send_chat_action(message.chat.id, 'typing')
    add_task_to_queue({"type": "chat", "chat_id": message.chat.id, "text": message.text, "msg_id": message.message_id})


def add_task_to_queue(task_data):
    tasks = []
    if os.path.exists(QUEUE_FILE):
        try:
            with open(QUEUE_FILE, "r") as f:
                tasks = json.load(f)
        except:
            tasks = []
    tasks.append(task_data)
    with open(QUEUE_FILE, "w") as f:
        json.dump(tasks, f)


def response_listener():
    while True:
        for file in os.listdir("."):
            if file.startswith("reply_") and file.endswith(".json"):
                try:
                    with open(file, "r") as f:
                        data = json.load(f)
                    bot.send_message(data['chat_id'], data['text'], reply_to_message_id=data.get('msg_id'))
                    os.remove(file)
                except:
                    pass
        time.sleep(1)


if __name__ == "__main__":
    print("📡 賈維斯收發室（含模型切換功能）已上線。")
    threading.Thread(target=response_listener, daemon=True).start()
    bot.infinity_polling(timeout=20)