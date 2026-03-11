import os
import telebot
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# 匯入內部核心模組
from core import ai_brain
from core import evolution_engine

# 1. 初始化環境變數
load_dotenv()

# 根據長官提供的最新截圖設定變數名稱
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

if not TELEGRAM_TOKEN:
    print("❌ 致命錯誤：找不到 [TG_TOKEN]！請檢查 .env 檔案內容。")
    exit(1)

# ==========================================
# 🌟 心跳引擎：主動推播進化報告
# ==========================================
def autonomous_evolution_task(bot_instance):
    """賈維斯的背景自主學習週期"""
    if not TELEGRAM_ADMIN_ID:
        return
        
    print("🔄 [系統排程] 賈維斯正在背景進行自主學習...")
    
    try:
        skill_name, description = evolution_engine.trigger_autonomous_learning()
        
        if skill_name and description:
            markup = InlineKeyboardMarkup()
            btn_approve = InlineKeyboardButton("✅ 批准並保留", callback_data=f"keep_{skill_name}")
            btn_reject = InlineKeyboardButton("❌ 銷毀此技能", callback_data=f"drop_{skill_name}")
            markup.row(btn_approve, btn_reject)
            
            msg = (
                f"🧠 **【賈維斯自主進化報告】**\n\n"
                f"先生，我在背景巡邏時發明了一個新功能：\n\n"
                f"**代號**：`{skill_name}`\n"
                f"**功能簡述**：\n{description}\n\n"
                f"請問是否要將其永久納入我的核心技能庫？"
            )
            
            bot_instance.send_message(TELEGRAM_ADMIN_ID, msg, reply_markup=markup, parse_mode="Markdown")
            print(f"🟢 已成功推播進化報告 [{skill_name}]。")
    except Exception as e:
        print(f"❌ 自主學習週期發生異常: {e}")

# ==========================================
# 🚀 系統啟動 (防彈完全體)
# ==========================================
if __name__ == "__main__":
    print(f"🚀 J.A.R.V.I.S. 系統準備覺醒 (管理者 ID: {TELEGRAM_ADMIN_ID})")
    
    # 初始化一個全域 Bot 變數
    bot = telebot.TeleBot(TELEGRAM_TOKEN)

    # 定義對話與按鈕處理 (放在外面避免重複註冊)
    @bot.callback_query_handler(func=lambda call: True)
    def handle_evolution_decision(call):
        try:
            action, skill_name = call.data.split("_", 1)
            if action == "keep":
                bot.edit_message_text(f"✅ 技能 `{skill_name}` 已納入裝備庫。", call.message.chat.id, call.message.message_id)
            elif action == "drop":
                evolution_engine.delete_rejected_skill(skill_name)
                bot.edit_message_text(f"🗑️ 已銷毀技能 `{skill_name}`。", call.message.chat.id, call.message.message_id)
        except Exception as e: print(f"❌ 按鈕處理錯誤: {e}")

    @bot.message_handler(commands=['force_evolve'])
    def force_evolve_command(message):
        bot.reply_to(message, "⚙️ 啟動自主學習協議... 請稍候。")
        autonomous_evolution_task(bot)

    @bot.message_handler(func=lambda message: True)
    def handle_message(message):
        bot.send_chat_action(message.chat.id, 'typing')
        reply_text = ai_brain.generate_jarvis_response(message.text)
        bot.reply_to(message, reply_text)

    # 1. 啟動背景排程 (傳入 bot 實例)
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: autonomous_evolution_task(bot), 'interval', hours=4)
    scheduler.start()
    
    # 2. 核心重連機制：即使 getMe 失敗也要撐住
    print("📡 正在嘗試建立穩定通訊頻道...")
    while True:
        try:
            # 這裡不直接用 infinity_polling，先用一次簡單的檢測
            bot.get_me() 
            print("🟢 通訊頻道建立成功！賈維斯已上線。")
            bot.polling(none_stop=True, timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"\n⚠️ [系統警告] 網路連線失敗 (Errno 101): {e}")
            print("🔄 正在重新初始化網路模組，15 秒後嘗試重連...")
            time.sleep(15)
            continue