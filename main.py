import telebot
from core import config
from core.ai_brain import generate_jarvis_response

# 啟動通訊模組
bot = telebot.TeleBot(config.TG_TOKEN)

# 定義訊息接收與處理邏輯
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print(f"👉 收到先生的指令: {message.text}")
    
    # 呼叫大腦進行思考
    reply_text = generate_jarvis_response(message.text)
    
    # 回報給先生
    bot.reply_to(message, reply_text)
    print("✅ 賈維斯已完成回報。")

if __name__ == "__main__":
    print("===============================================")
    print("🟢 J.A.R.V.I.S. 系統核心已上線！(模組化架構 V2.0)")
    print("🟢 正在監聽 Telegram 訊息...")
    print("===============================================")
    
    # 開始無限期站崗
    bot.infinity_polling()