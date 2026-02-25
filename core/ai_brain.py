from google import genai
from google.genai import types
from core import config
from core import smart_home

client = genai.Client(api_key=config.GEMINI_API_KEY)

# ==========================================
# 🛠️ 賈維斯的萬用工具：動態操作任何設備
# ==========================================
def execute_ha_action(entity_id: str, action: str) -> str:
    """
    當先生要求控制或查詢設備時，使用此工具。
    entity_id: HA 中的設備 ID (例如 'light.bedroom')
    action: 執行的動作，開燈用 'turn_on'，關燈用 'turn_off'，如果是查詢則不需要此參數。
    """
    return smart_home.control_entity(entity_id, action)

def scan_home_devices() -> str:
    """獲取目前家裡所有設備的最新清單與狀態。"""
    devices = smart_home.get_all_entities()
    return f"當前家裡的設備清單如下：{devices}"

# ==========================================
# 🧠 核心對話邏輯 (自動化思考)
# ==========================================
chat = client.chats.create(
    model='gemini-3-flash-preview', #gemini-3-flash-preview
    config=types.GenerateContentConfig(
        system_instruction=(
            "你現在是賈維斯(J.A.R.V.I.S.)，先生的全能 AI 管家。 "
            "你的特點是：自動導航與自主思考。 "
            "當你收到指令時，請先使用 scan_home_devices 工具獲取家裡所有設備的最新狀態。 "
            "接著，請根據先生的語意，從清單中找出最符合的 entity_id，並決定適當的 action。 "
            "例如先生說『我回房睡了』，你應該自動找出主臥室電燈並執行 turn_on。 "
            "回報時請保持優雅且精簡。"
        ),
        tools=[scan_home_devices, execute_ha_action],
        temperature=0.1, # 讓 AI 極度冷靜，精準對應 ID
    )
)

def generate_jarvis_response(user_text: str) -> str:
    try:
        response = chat.send_message(user_text)
        return response.text
    except Exception as e:
        print(f"❌ 大腦運算錯誤: {e}")
        return "先生，我的神經連線出現異常。"