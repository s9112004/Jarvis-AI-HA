from google import genai
from google.genai import types
from core import config
from core import smart_home
import time

client = genai.Client(api_key=config.GEMINI_API_KEY)

# ==========================================
# 🛠️ 賈維斯的萬用工具：動態操作任何設備
# ==========================================
def execute_ha_action(entity_id: str, action: str) -> str:
    """
    執行設備控制動作。
    entity_id: 設備 ID
    action: 'turn_on' 或 'turn_off'
    """
    result = smart_home.control_entity(entity_id, action)
    # 執行後稍微等待，讓硬體有時間反應
    time.sleep(2) 
    return f"執行結果回報：{result}。請務必再次掃描確認實體狀態是否一致。"

def scan_home_devices() -> str:
    """獲取目前家裡所有設備的最新清單與狀態。"""
    devices = smart_home.get_all_entities()
    return f"當前家裡的設備清單與實體屬性如下：{devices}"

# ==========================================
# 🧠 核心對話邏輯 (gemini-3-flash-preview)
# ==========================================
chat = client.chats.create(
    model='gemini-3-flash-preview',
    config=types.GenerateContentConfig(
        system_instruction=(
            "你現在是賈維斯(J.A.R.V.I.S.)，先生的專業 AI 管家。 "
            "當先生要求控制設備時，你的標準流程如下： "
            "1. 使用 scan_home_devices 獲取清單。 "
            "2. 找到正確的 entity_id 並執行 execute_ha_action。 "
            "3. 【關鍵步驟】執行完後，必須再次使用 scan_home_devices 獲取最新狀態。 "
            "4. 比較執行後的狀態。如果狀態沒變（例如你執行了 turn_off 但狀態還是 on），"
            "   請誠實告訴先生：『先生，指令已發送但設備似乎沒有回應，建議您檢查實體連線或 Token 狀態。』"
            "回報時請保持優雅，並提供正確的設備 friendly_name。"
        ),
        tools=[scan_home_devices, execute_ha_action],
        temperature=0.1,
    )
)

def generate_jarvis_response(user_text: str) -> str:
    try:
        response = chat.send_message(user_text)
        return response.text
    except Exception as e:
        print(f"❌ 大腦運算錯誤: {e}")
        return "先生，我的神經連線出現異常。"