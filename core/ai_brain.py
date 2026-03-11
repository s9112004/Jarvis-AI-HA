from google import genai
from google.genai import types
from core import config
from core import smart_home
from core import memory  # 🌟 新增：載入海馬迴模組
import time

client = genai.Client(api_key=config.GEMINI_API_KEY)


# ==========================================
# 🛠️ 賈維斯的萬用工具 (感知與控制)
# ==========================================
def execute_ha_action(entity_id: str, action: str) -> str:
    result = smart_home.control_entity(entity_id, action)
    time.sleep(2)
    return f"執行結果回報：{result}。請務必再次掃描確認實體狀態是否一致。"


def scan_home_devices() -> str:
    devices = smart_home.get_all_entities()
    return f"當前家裡的設備清單與實體屬性如下：{devices}"


# ==========================================
# 🧠 大腦核心狀態管理 (雙核系統 + 記憶體)
# ==========================================
current_model = 'gemini-3-flash-preview'
chat_session = None


def get_system_instruction() -> str:
    """統一管理賈維斯的人格設定與記憶"""
    # 🌟 每次啟動大腦時，動態讀取 JSON 裡的核心記憶
    core_memory = memory.get_core_prompt()

    return (
        f"{core_memory}\n\n"
        "你現在是賈維斯(J.A.R.V.I.S.)，先生的專屬 AI 管家。\n"
        "【設備控制守則】\n"
        "1. 控制設備前必須先用 scan_home_devices 獲取清單。\n"
        "2. 找到正確的 entity_id 並執行 execute_ha_action。\n"
        "3. 執行後必須再次 scan_home_devices 確認狀態，若無改變則誠實回報。\n\n"
        "【長期記憶守則】\n"
        "1. 當先生告訴你密碼、行程、喜好或要求你『記住』某事時，主動呼叫 save_long_term_memory 工具將其存入 SQLite 檔案櫃。請自行設計精準的標籤 (例如 #密碼 #大門)。\n"
        "2. 當先生詢問你不知道的歷史資訊（例如『我之前的密碼是多少』、『上次保養冷氣是何時』），請主動呼叫 search_long_term_memory 工具檢索檔案櫃，再回答先生。\n"
        "回報時請保持優雅、精練，並展現英式管家的專業。"
    )


def init_chat_session(model_name: str):
    """初始化或重新載入對話節點"""
    global chat_session, current_model

    temp = 0.5 if "pro" in model_name.lower() else 0.1

    config_opts = types.GenerateContentConfig(
        system_instruction=get_system_instruction(),
        # 🌟 新增：把兩個記憶工具交給大腦，讓他自己決定何時使用
        tools=[
            scan_home_devices,
            execute_ha_action,
            memory.save_long_term_memory,
            memory.search_long_term_memory
        ],
        temperature=temp,
    )

    chat_session = client.chats.create(
        model=model_name,
        config=config_opts
    )
    current_model = model_name
    print(f"🔄 [系統通知] 賈維斯大腦已切換至: {current_model}，並成功載入核心記憶。")


def switch_model(new_model: str):
    init_chat_session(new_model)


def generate_jarvis_response(user_text: str) -> str:
    global chat_session
    try:
        if chat_session is None:
            init_chat_session(current_model)

        response = chat_session.send_message(user_text)
        return response.text
    except Exception as e:
        print(f"❌ 大腦運算錯誤: {e}")
        if "not found" in str(e).lower() or "invalid" in str(e).lower():
            return f"先生，模型 {current_model} 似乎無法連線。"
        return "先生，我的神經連線出現異常，無法完成運算。"


# 啟動時預設載入
init_chat_session(current_model)