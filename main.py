import os
import telebot
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# 匯入核心模組
from core import ai_brain
from core import evolution_engine

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

# 🌟 初始化連線池優化
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True, num_threads=4)

# ==========================================
# 🌟 背景任務與回傳處理
# ==========================================
def autonomous_evolution_task():
    """獨立執行緒：背景學習"""
    if not TELEGRAM_ADMIN_ID: return
    try:
        skill_name, description = evolution_engine.trigger_autonomous_learning()
        if skill_name and description:
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ 批准", callback_data=f"keep_{skill_name}"),
                InlineKeyboardButton("❌ 銷毀", callback_data=f"drop_{skill_name}")
            )
            msg = f"🧠 **【進化報告】**\n代號：`{skill_name}`\n功能：{description}"
            bot.send_message(TELEGRAM_ADMIN_ID, msg, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        print(f"❌ 進化排程錯誤: {e}")

# ==========================================
# 💬 對話邏輯：改為非同步執行緒
# ==========================================
def process_message_async(message):
    """這是在獨立執行緒跑的，不會卡住 Telegram 連線"""
    try:
        # 讓 Bot 先顯示「正在輸入...」保持連線活躍
        bot.send_chat_action(message.chat.id, 'typing')
        
        # 大腦運算 (可能很耗時)
        reply_text = ai_brain.generate_jarvis_response(message.text)
        
        # 回覆結果
        bot.reply_to(message, reply_text)
    except Exception as e:
        print(f"❌ 非同步處理異常: {e}")

@bot.message_handler(commands=['force_evolve'])
def force_evolve_command(message):
    bot.reply_to(message, "⚙️ 啟動自主學習協議... 請稍候。")
    threading.Thread(target=autonomous_evolution_task).start()

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # 🌟 關鍵改動：每收到一個訊息，就開一個新執行緒去處理，主執行緒立刻回去監聽 Telegram
    threading.Thread(target=process_message_async, args=(message,)).start()

# ==========================================
# 🚀 系統啟動 (極速重連模式)
# ==========================================
if __name__ == "__main__":
    print(f"🚀 J.A.R.V.I.S. 穩定版啟動 (ID: {TELEGRAM_ADMIN_ID})")
    
    # 排程設定
    scheduler = BackgroundScheduler()
    scheduler.add_job(autonomous_evolution_task, 'interval', hours=4)
    scheduler.start()
    
    # 處理按鈕回饋
    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        action, name = call.data.split("_", 1)
        if action == "keep":
            bot.edit_message_text(f"✅ 技能 `{name}` 已存檔。", call.message.chat.id, call.message.message_id)
        else:
            evolution_engine.delete_rejected_skill(name)
            bot.edit_message_text(f"🗑️ 技能 `{name}` 已銷毀。", call.message.chat.id, call.message.message_id)

    # 無限重連保護
    while True:
        try:
            print("📡 通訊中樞運作中...")
            bot.polling(none_stop=True, timeout=10, long_polling_timeout=5)
        except Exception as e:
            print(f"⚠️ 通訊抖動: {e}")
            time.sleep(5)
            continue