from google import genai
from core import config

# 喚醒 Gemini 2.0 引擎
client = genai.Client(api_key=config.GEMINI_API_KEY)

def generate_jarvis_response(user_text: str) -> str:
    """
    將使用者的訊息送給 Gemini，並套用賈維斯的人設。
    未來會在這裡注入對話歷史與 HA 的狀態。
    """
    try:
        # 這是賈維斯的靈魂設定 (System Prompt 的雛形)
        prompt = f"你現在是賈維斯(J.A.R.V.I.S.)，請像個優雅、機智的英國管家一樣尊稱我為先生，並簡明扼要地回答我的問題：{user_text}"
        
        # 呼叫最新 3.0-flash 模型
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents=prompt
        )
        return response.text

    except Exception as e:
        print(f"❌ 大腦運算錯誤: {e}")
        return "先生，我的神經網絡似乎受到了干擾，請稍後再試。"