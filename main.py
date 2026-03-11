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

# 初始化 Telegram Bot
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ==========================================
# 🌟 心跳引擎：主動推播進化報告
# ==========================================
def autonomous_evolution_task():
    """賈維斯的背景自主學習週期"""
    if not TELEGRAM_ADMIN_ID:
        print("⚠️ 尚未設定 TELEGRAM_ADMIN_ID，無法主動推播報告。")
        return
        
    print("🔄 [系統排程] 賈維斯正在背景進行自主學習...")
    
    try:
        # 呼叫進化引擎進行發明與測試
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
            
            bot.send_message(TELEGRAM_ADMIN_ID, msg, reply_markup=markup, parse_mode="Markdown")
            print(f"🟢 已成功推播進化報告 [{skill_name}]。")
    except Exception as e:
        print(f"❌ 自主學習週期發生異常: {e}")

# ==========================================
# 🌟 處理按鈕回饋 (Callback)
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_evolution_decision(call):
    try:
        # 解析按鈕回傳的資料格式 "action_skillname"
        action, skill_name = call.data.split("_", 1)
        
        if action == "keep":
            bot.edit_message_text(
                f"✅ 遵命。技能 `{skill_name}` 已納入裝備庫。我變得更強大了，謝謝先生。", 
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id
            )
        elif action == "drop":
            evolution_engine.delete_rejected_skill(skill_name)
            bot.edit_message_text(
                f"🗑️ 收到。已銷毀技能 `{skill_name}` 的所有程式碼與紀錄。", 
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id
            )
    except Exception as e:
        print(f"❌ 按鈕處理錯誤: {e}")

# ==========================================
# 💬 一般對話與強制指令
# ==========================================
@bot.message_handler(commands=['force_evolve'])
def force_evolve_command(message):
    """手動強制觸發自主學習"""
    try:
        bot.reply_to(message, "⚙️ 啟動自主學習協議... 正在掃描網路並編寫新技能，請稍候。")
        time.sleep(1) # 緩衝以避免連線重疊
        autonomous_evolution_task()
    except Exception as e:
        print(f"❌ 強制進化指令執行失敗: {e}")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    """一般對話處理"""
    try:
        user_text = message.text
        print(f"收到來自先生的指令: {user_text}")
        
        bot.send_chat_action(message.chat.id, 'typing')
        reply_text = ai_brain.generate_jarvis_response(user_text)
        bot.reply_to(message, reply_text)
    except Exception as e:
        print(f"❌ 對話處理異常: {e}")

# ==========================================
# 🚀 系統啟動 (防斷線自我修復版)
# ==========================================
if __name__ == "__main__":
    print(f"🚀 J.A.R.V.I.S. 系統已覺醒 (管理者 ID: {TELEGRAM_ADMIN_ID})")
    
    # 1. 啟動背景排程 (每 4 小時一次)
    scheduler = BackgroundScheduler()
    scheduler.add_job(autonomous_evolution_task, 'interval', hours=4)
    scheduler.start()
    
    print("📡 正在建立防斷線連線通道...")

    # 2. 無限重連迴圈，徹底對抗 Errno 101
    while True:
        try:
            # 啟動長輪詢，設定較短的超時以利快速反應網路波動
            bot.infinity_polling(
                timeout=20, 
                long_polling_timeout=10, 
                non_stop=True,
                allowed_updates=['message', 'callback_query']
            )
        except Exception as e:
            # 當網路不通 (Errno 101) 時會觸發此處
            print(f"\n⚠️ [系統警告] 偵測到網路波動: {e}")
            print("🔄 正在重新初始化通訊模組，10 秒後自動復活...")
            
            # 清理舊連線並等待網路恢復
            bot.stop_polling()
            time.sleep(10) 
            
            # 回到迴圈開頭重新啟動 polling
            continue