import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from core import ai_brain
from core import evolution_engine

# 1. 初始化環境變數
load_dotenv()

# 🌟 根據您最新的截圖進行精準對接
TELEGRAM_TOKEN = os.getenv("TG_TOKEN")
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID")

if not TELEGRAM_TOKEN:
    print("❌ 致命錯誤：找不到 [TG_TOKEN]！請檢查 .env 檔案。")
    exit(1)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ==========================================
# 🌟 心跳引擎：主動推播進化報告
# ==========================================
def autonomous_evolution_task():
    """賈維斯的自主冥想週期"""
    if not TELEGRAM_ADMIN_ID:
        print("⚠️ 尚未設定 TELEGRAM_ADMIN_ID，無法主動推播。")
        return
        
    print("🔄 [系統排程] 賈維斯正在背景進行自主學習...")
    skill_name, description = evolution_engine.trigger_autonomous_learning()
    
    if skill_name and description:
        # 建立 Telegram 互動按鈕
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
        
        try:
            bot.send_message(TELEGRAM_ADMIN_ID, msg, reply_markup=markup, parse_mode="Markdown")
            print(f"🟢 已推播進化報告 [{skill_name}] 給長官。")
        except Exception as e:
            print(f"❌ 推播失敗: {e}")

# ==========================================
# 🌟 處理長官的按鈕決策 (Callback)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_evolution_decision(call):
    try:
        # 解析按鈕回傳的資料
        action, skill_name = call.data.split("_", 1)
        
        if action == "keep":
            bot.edit_message_text(
                f"✅ 遵命。技能 `{skill_name}` 已成功納入裝備庫。我變得更聰明了，謝謝先生。", 
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id
            )
        elif action == "drop":
            evolution_engine.delete_rejected_skill(skill_name)
            bot.edit_message_text(
                f"🗑️ 收到。已銷毀技能 `{skill_name}` 的所有紀錄與程式碼。", 
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id
            )
    except Exception as e:
        print(f"❌ 按鈕處理錯誤: {e}")

# ==========================================
# 💬 對話與強制指令
# ==========================================
@bot.message_handler(commands=['force_evolve'])
def force_evolve_command(message):
    """手動觸發進化"""
    bot.reply_to(message, "⚙️ 啟動自主學習協議... 正在掃描網路並編寫新技能，請稍候。")
    autonomous_evolution_task()

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """一般對話邏輯"""
    user_text = message.text
    print(f"收到來自先生的指令: {user_text}")
    
    bot.send_chat_action(message.chat.id, 'typing')
    reply_text = ai_brain.generate_jarvis_response(user_text)
    bot.reply_to(message, reply_text)

# ==========================================
# 🚀 系統啟動
# ==========================================
if __name__ == "__main__":
    print(f"🚀 J.A.R.V.I.S. 系統已覺醒 (管理者: {TELEGRAM_ADMIN_ID})")
    
    # 啟動排程：每 4 小時自動學習一次
    scheduler = BackgroundScheduler()
    scheduler.add_job(autonomous_evolution_task, 'interval', hours=4)
    scheduler.start()
    
    bot.infinity_polling()