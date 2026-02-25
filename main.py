import os
# --- 終極清除干擾：強制 Python 無視任何 Proxy 設定 ---
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['ALL_PROXY'] = ''
# ---------------------------------------------------

import telebot
from dotenv import load_dotenv
from google import genai

# ---------------------------------------------------------
# 1. 系統初始化：載入機密金鑰 (從 .env 讀取)
# ---------------------------------------------------------
load_dotenv()
TG_TOKEN = os.getenv("TG_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# 安全檢查
if not TG_TOKEN or not GEMINI_KEY:
    print("🚨 錯誤：找不到金鑰！請檢查 .env 檔案內容是否正確。")
    exit()

# ---------------------------------------------------------
# 2. 喚醒 Gemini 最新版大腦
# ---------------------------------------------------------
# 這裡會自動從變數讀取金鑰，不會再發生 NameError
client = genai.Client(api_key=GEMINI_KEY)

# ---------------------------------------------------------
# 3. 連結 Telegram 嘴巴與耳朵
# ---------------------------------------------------------
bot = telebot.TeleBot(TG_TOKEN)

# ---------------------------------------------------------
# 4. 定義對話邏輯
# ---------------------------------------------------------
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    print(f"👉 收到訊息: {message.text}")
    
    try:
        # 設定賈維斯的管家人格
        prompt = f"你現在是賈維斯(J.A.R.V.I.S.)，請像個優雅的英國管家一樣尊稱我為先生，並回答：{message.text}"
        
        # 呼叫 Gemini 產生回應
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt
        )
        
        # 回傳給 Telegram
        bot.reply_to(message, response.text)
        print("✅ 賈維斯已回覆。")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        bot.reply_to(message, "先生，我的系統遭遇了一些干擾，暫時無法回應。")

# ---------------------------------------------------------
# 5. 上線！
# ---------------------------------------------------------
print("===============================================")
print("🟢 J.A.R.V.I.S. 系統核心已上線！")
print("🟢 正在監聽 Telegram 訊息...")
print("===============================================")

bot.infinity_polling()
