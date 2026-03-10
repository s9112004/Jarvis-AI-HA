from google import genai
from google.genai import types
from core import config
from core import smart_home
import time

# 喚醒引擎基礎連線
client = genai.Client(api_key=config.GEMINI_API_KEY)

# ==========================================
# 🛠️ 賈維斯的萬用工具 (感知與控制)
# ==========================================
def execute_ha_action(entity_id: str, action: str) -> str:
    """執行設備控制動作。"""
    result = smart_home.control_entity(entity_id, action)
    time.sleep(2) # 讓硬體有時間反應
    return f"執行結果回報：{result}。請務必再次掃描確認實體狀態是否一致。"

def scan_home_devices() -> str:
    """獲取目前家裡所有設備的最新清單與狀態。"""
    devices = smart_home.get_all_entities()
    return f"當前家裡的設備清單與實體屬性如下：{devices}"

# ==========================================
# 🧠 大腦核心狀態管理 (雙核系統)
# ==========================================
# 預設啟動為日常極速模式
current_model = 'gemini-3-flash-preview'
chat_session = None

def get_system_instruction() -> str:
    """統一管理賈維斯的人格設定"""
    return (
        "你現在是賈維斯(J.A.R.V.I.S.)，先生的專業 AI 管家。 "
        "當先生要求控制設備時，你的標準流程如下： "
        "1. 使用 scan_home_devices 獲取清單。 "
        "2. 找到正確的 entity_id 並執行 execute_ha_action。 "
        "3. 執行完後，必須再次使用 scan_home_devices 獲取最新狀態。 "
        "4. 比較執行後的狀態。如果狀態沒變，請誠實告訴先生設備沒有反應。 "
        "回報時請保持優雅，並提供正確的設備 friendly_name。 "
        "如果是深度技術探討，請展現你強大的邏輯分析能力，並提供具體的解決方案。"
    )

def init_chat_session(model_name: str):
    """
    初始化或重新載入對話節點 (動態切換大腦)
    """
    global chat_session, current_model
    
    # 根據不同模型設定不同參數 (Pro 模式稍微提高一點溫度，增加思考深度與創意)
    temp = 0.5 if "pro" in model_name.lower() else 0.1
    
    config_opts = types.GenerateContentConfig(
        system_instruction=get_system_instruction(),
        tools=[scan_home_devices, execute_ha_action],
        temperature=temp,
    )
    
    # 重置大腦核心 (⚠️ 注意：目前切換模型會重置「短期對話記憶」)
    chat_session = client.chats.create(
        model=model_name,
        config=config_opts
    )
    current_model = model_name
    print(f"🔄 [系統通知] 賈維斯大腦已成功切換至: {current_model}")

def switch_model(new_model: str):
    """提供給外部 (main.py) 呼叫的切換開關"""
    init_chat_session(new_model)

def generate_jarvis_response(user_text: str) -> str:
    """處理長官傳來的訊息"""
    global chat_session
    try:
        # 防呆機制：如果大腦還沒啟動，先啟動一次
        if chat_session is None:
            init_chat_session(current_model)
            
        response = chat_session.send_message(user_text)
        return response.text
    except Exception as e:
        print(f"❌ 大腦運算錯誤: {e}")
        # 如果 API 報錯找不到模型，給予明確提示
        if "not found" in str(e).lower() or "invalid" in str(e).lower():
            return f"先生，模型 {current_model} 似乎無法連線，請確認 Google AI Studio 支援該模型代號。"
        return "先生，我的神經連線出現異常，無法完成運算。"

# 系統啟動時，預設先載入一次大腦
init_chat_session(current_model)