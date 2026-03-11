import os
import telebot
import time
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# 匯入賈維斯核心模組
from core import ai_brain
from core import evolution_engine

# 1. 載入環境變數
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

if not TELEGRAM_TOKEN:
    print("❌ 致命錯誤：找不到 [TG_TOKEN]！系統終止。")
    exit(1)

# 2. 初始化 Bot (啟用多執行緒模式，預留 5 個執行緒處理併發請求)
bot = telebot.TeleBot(TELEGRAM_TOKEN, threaded=True, num_threads=5)

# ==========================================
# 🌟 背景進化任務 (主動學習與推播)
# ==========================================
def autonomous_evolution_task():
    """獨立執行緒：讓賈維斯在背景自行研究新技能"""
    if not TELEGRAM_ADMIN_ID:
        print("⚠️ 警告：未設定 ADMIN ID，進化報告將無法推播。")
        return
        
    print("🔄 [系統排程] 賈維斯正在背景冥想...")
    try:
        skill_name, description = evolution_engine.trigger_autonomous_learning()
        if skill_name and description:
            markup = InlineKeyboardMarkup()
            markup.row(
                InlineKeyboardButton("✅ 批准並保留", callback_data=f"keep_{skill_name}"),
                InlineKeyboardButton("❌ 銷毀此技能", callback_data=f"drop_{skill_name}")
            )
            msg = (
                f"🧠 **【賈維斯自主進化報告】**\n\n"
                f"先生，我在背景巡邏時發明了一個新功能：\n"
                f"**代號**：`{skill_name}`\n"
                f"**功能簡述**：\n{description}\n\n"
                f"請問是否要將其永久納入我的技能庫？"
            )
            bot.send_message(TELEGRAM_ADMIN_ID, msg, reply_markup=markup, parse_mode="Markdown")
            print(f"🟢 進化報告 [{skill_name}] 已送達長官手機。")
    except Exception as e:
        print(f"❌ 背景進化過程出錯: {e}")

# ==========================================
# 💬 對話處理邏輯 (非同步執行，徹底解決 Errno 101)
# ==========================================
def process_message_async(message):
    """將耗時的大腦運算丟進獨立執行緒，避免阻塞 Telegram 通訊包"""
    try:
        # 讓 Bot 先顯示「正在輸入...」保持連線活躍感
        bot.send_chat_action(message.chat.id, 'typing')
        
        # 呼叫大腦運算 (內含 HA 掃描、Gmail 讀取、寫扣等動作)
        print(f"🧠 大腦正在運算先生的指令: {message.text[:20]}...")
        reply_text = ai_brain.generate_jarvis_response(message.text)
        
        # 回覆結果給先生
        bot.reply_to(message, reply_text)
    except Exception as e:
        print(f"❌ 對話執行緒異常: {e}")

# ==========================================
# 🛠️ 指令監聽器
# ==========================================
@bot.message_handler(commands=['force_evolve'])
def force_evolve_command(message):
    bot.reply_to(message, "⚙️ 啟動強制進化協議... 我會退入背景思考，請稍候。")
    # 開啟獨立執行緒去執行進化任務
    threading.Thread(target=autonomous_evolution_task).start()

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """每收到一個訊息，就開一個新執行緒去處理，主執行緒立刻回去監聽 Telegram"""
    threading.Thread(target=process_message_async, args=(message,)).start()

# ==========================================
# 🚀 系統啟動與監控
# ==========================================
if __name__ == "__main__":
    print(f"🚀 J.A.R.V.I.S. 穩定版已啟動 (管理者: {TELEGRAM_ADMIN_ID})")
    
    # 啟動排程器 (每 4 小時自動學習一次)
    scheduler = BackgroundScheduler()
    scheduler.add_job(autonomous_evolution_task, 'interval', hours=4)
    scheduler.start()
    
    # 處理按鈕回饋 (Inline Keyboard)
    @bot.callback_query_handler(func=lambda call: True)
    def handle_query(call):
        try:
            action, name = call.data.split("_", 1)
            if action == "keep":
                bot.edit_message_text(f"✅ 技能 `{name}` 已正式存入核心庫。", call.message.chat.id, call.message.message_id)
            else:
                evolution_engine.delete_rejected_skill(name)
                bot.edit_message_text(f"🗑️ 技能 `{name}` 已被銷毀。", call.message.chat.id, call.message.message_id)
        except Exception as e:
            print(f"❌ 按鈕處理錯誤: {e}")

    # 啟動通訊輪詢 (配合守護者腳本，不再使用複雜的 while 迴圈)
    print("📡 通訊中樞已就位，等待先生指令...")
    try:
        # 這裡不加 while True，因為 guardian.sh 會在崩潰時自動重啟我
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        print(f"⚠️ 通訊終止: {e}")
        # 直接結束，讓外部的 guardian.sh 來拯救我