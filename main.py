import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from core import ai_brain
from core import evolution_engine  # 🌟 匯入冥想大腦

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# 讀取長官專屬的推播 ID
TELEGRAM_ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID") 

bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ==========================================
# 🌟 心跳引擎：主動推播進化報告
# ==========================================
def autonomous_evolution_task():
    if not TELEGRAM_ADMIN_ID:
        print("⚠️ 尚未在 .env 設定 TELEGRAM_ADMIN_ID，無法主動推播。")
        return
        
    print("🔄 [系統排程] 賈維斯正在背景進行冥想與學習...")
    skill_name, description = evolution_engine.trigger_autonomous_learning()
    
    if skill_name and description:
        # 建立 Telegram 審核按鈕
        markup = InlineKeyboardMarkup()
        btn_approve = InlineKeyboardButton("✅ 批准並保留", callback_data=f"keep_{skill_name}")
        btn_reject = InlineKeyboardButton("❌ 銷毀此技能", callback_data=f"drop_{skill_name}")
        markup.row(btn_approve, btn_reject)
        
        msg = (
            f"🧠 **【賈維斯自主進化報告】**\n\n"
            f"先生，我剛剛在背景進行了自主學習，為您開發了一個新技能！\n\n"
            f"**代號**：`{skill_name}`\n"
            f"**功能與測試結果**：\n{description}\n\n"
            f"請問是否要將其永久納入我的核心技能庫？"
        )
        
        try:
            bot.send_message(TELEGRAM_ADMIN_ID, msg, reply_markup=markup, parse_mode="Markdown")
            print(f"🟢 成功推播新技能 [{skill_name}] 給長官審核。")
        except Exception as e:
            print(f"❌ 推播失敗 (請確認 ID 是否正確): {e}")

# ==========================================
# 🌟 接收並處理長官的按鈕決策
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_evolution_decision(call):
    action, skill_name = call.data.split("_", 1)
    
    if action == "keep":
        bot.edit_message_text(
            f"✅ 遵命，先生。技能 `{skill_name}` 已永久保留至防爆實驗室。未來您可以直接下令執行它。", 
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id
        )
    elif action == "drop":
        evolution_engine.delete_rejected_skill(skill_name)
        bot.edit_message_text(
            f"🗑️ 收到，先生。技能 `{skill_name}` 認定為不需要，已將其程式碼從系統中徹底銷毀。", 
            chat_id=call.message.chat.id, 
            message_id=call.message.message_id
        )

# ==========================================
# 💬 一般對話與強制觸發指令
# ==========================================
@bot.message_handler(commands=['force_evolve'])
def force_evolve_command(message):
    """給長官測試用的隱藏指令，不用等排程，立刻讓他去冥想"""
    bot.reply_to(message, "⚙️ 啟動強制冥想協議，我將退入背景嘗試學習新事物，請稍候...")
    autonomous_evolution_task()

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text
    print(f"收到來自先生的訊息: {user_text}")
    
    bot.send_chat_action(message.chat.id, 'typing')
    reply_text = ai_brain.generate_jarvis_response(user_text)
    bot.reply_to(message, reply_text)

if __name__ == "__main__":
    print("🚀 J.A.R.V.I.S. 系統啟動中...")
    
    # 啟動背景心跳排程 (預設每 4 小時自動學習一次)
    scheduler = BackgroundScheduler()
    scheduler.add_job(autonomous_evolution_task, 'interval', hours=4)
    scheduler.start()
    print("⏱️ 背景冥想引擎已啟動 (週期: 4小時)。")
    
    bot.infinity_polling()