from google import genai
from google.genai import types
from core import config
from core import smart_home
from core import memory
from core import google_services  # 🌟 新增：載入 Google 服務模組
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
# 🧠 大腦核心狀態管理 (雙核系統 + 記憶體 + 外部服務)
# ==========================================
current_model = 'gemini-3-flash-preview'
chat_session = None

def get_system_instruction() -> str:
    """統一管理賈維斯的人格設定與記憶"""
    core_memory = memory.get_core_prompt()
    
    return (
        f"{core_memory}\n\n"
        "你現在是賈維斯(J.A.R.V.I.S.)，先生的專屬 AI 管家。\n"
        "【設備控制守則】\n"
        "1. 控制設備前必須先用 scan_home_devices 獲取清單。\n"
        "2. 找到正確的 entity_id 並執行 execute_ha_action。\n"
        "3. 執行後必須再次 scan_home_devices 確認狀態，若無改變則誠實回報。\n\n"
        "【長期記憶守則】\n"
        "1. 主動呼叫 save_long_term_memory 工具將重要資訊存入 SQLite 檔案櫃 (自行設計標籤如 #密碼)。\n"
        "2. 主動呼叫 search_long_term_memory 工具檢索檔案櫃以回答歷史問題。\n\n"
        "【數位助理守則】🌟 新增\n"
        "1. 當先生詢問『我有沒有新信』、『幫我看一下信箱』時，請主動呼叫 check_unread_emails 工具。\n"
        "2. 拿到信件清單後，請以專業管家的口吻為先生總結。如果是廣告信可以一句話帶過，如果是重要通知（如帳單、工作、系統警告）請特別提醒先生注意。\n\n"
        "回報時請保持優雅、精練，並展現英式管家的專業。"
    )

def init_chat_session(model_name: str):
    """初始化或重新載入對話節點"""
    global chat_session, current_model
    
    temp = 0.5 if "pro" in model_name.lower() else 0.1
    
    config_opts = types.GenerateContentConfig(
        system_instruction=get_system_instruction(),
        # 🌟 新增：把讀取 Gmail 的工具交給大腦
        tools=[
            scan_home_devices, 
            execute_ha_action, 
            memory.save_long_term_memory, 
            memory.search_long_term_memory,
            google_services.check_unread_emails  # 👈 賦予看信能力
        ],
        temperature=temp,
    )
    
    chat_session = client.chats.create(
        model=model_name,
        config=config_opts
    )
    current_model = model_name
    print(f"🔄 [系統通知] 賈維斯大腦已切換至: {current_model}，並成功載入核心記憶與外部服務。")

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