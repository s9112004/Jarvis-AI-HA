import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from core import config
from core.ai_brain import generate_jarvis_response, switch_model

bot = telebot.TeleBot(config.TG_TOKEN)

# ==========================================
# 🎛️ 新增：引擎切換面板指令 (/mode)
# ==========================================
@bot.message_handler(commands=['mode', 'switch'])
def send_model_switch_panel(message):
    """當長官輸入 /mode 時，彈出切換按鈕"""
    markup = InlineKeyboardMarkup()
    # 定義兩個按鈕，callback_data 是我們等一下要接收的暗號
    btn_flash = InlineKeyboardButton("⚡ 日常極速 (Flash)", callback_data="model_flash")
    btn_pro = InlineKeyboardButton("🧠 深度運算 (Pro)", callback_data="model_pro")
    
    # 把按鈕排成一列
    markup.row(btn_flash, btn_pro)
    
    bot.reply_to(message, "先生，請選擇您需要啟動的大腦引擎：", reply_markup=markup)

# ==========================================
# 📡 新增：按鈕點擊接收器
# ==========================================
@bot.callback_query_handler(func=lambda call: True)
def handle_model_switch(call):
    """處理長官點擊按鈕後的動作"""
    if call.data == "model_flash":
        new_model = "gemini-3-flash-preview"
        msg = "⚡ 已切換至【日常極速模式】。隨時為您處理瑣事，先生。"
    elif call.data == "model_pro":
        new_model = "gemini-3.1-pro-preview" 
        msg = "🧠 已切換至【深度運算模式】。算力已全面解放，準備好進行深度探討。"
    
    # 呼叫大腦進行核心切換 (我們等一下要在 ai_brain.py 寫這個函式)
    switch_model(new_model)
    
    # 彈出通知並修改原本的訊息
    bot.answer_callback_query(call.id, "引擎切換成功")
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=msg)

# ==========================================
# 💬 原本的對話處理器
# ==========================================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # 忽略以 / 開頭的指令，避免跟上面的 /mode 衝突
    if message.text.startswith('/'):
        return
        
    print(f"👉 收到先生的指令: {message.text}")
    reply_text = generate_jarvis_response(message.text)
    bot.reply_to(message, reply_text)
    print("✅ 賈維斯已完成回報。")

if __name__ == "__main__":
    print("===============================================")
    print("🟢 J.A.R.V.I.S. 系統核心已上線！(支援雙核引擎切換)")
    print("🟢 正在監聽 Telegram 訊息...")
    print("===============================================")
    bot.infinity_polling()