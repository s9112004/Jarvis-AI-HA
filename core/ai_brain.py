from google import genai
from google.genai import types
from core import config
from core import smart_home
from core import memory
from core import google_services
from core import skill_builder
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

def get_ha_notify_services() -> str:
    """🌟 新增：讓 AI 自己查詢有哪些手機可以發送通知"""
    return smart_home.get_notify_services()

# ==========================================
# 🧠 大腦核心狀態管理 (完全體)
# ==========================================
current_model = 'gemini-3-flash-preview'
chat_session = None

def get_system_instruction() -> str:
    """統一管理賈維斯的人格設定與記憶"""
    core_memory = memory.get_core_prompt()
    
    return (
        f"{core_memory}\n\n"
        "你現在是賈維斯(J.A.R.V.I.S.)，先生的專屬 AI 管家。\n\n"
        "【🤖 自我進化與自主執行協議】\n"
        "1. **禁止打擾模式**：當先生要求你執行新任務時，如果缺少參數（例如：不知道哪台手機收通知、不知道電燈的 ID），你必須優先『自主解決』。\n"
        "2. **自我診斷**：請先主動呼叫 scan_home_devices 或 get_ha_notify_services 來獲取環境資訊。只有在嘗試所有工具後仍無法確定時，才允許詢問先生。\n"
        "3. **寫扣進化**：若目前功能不足，請使用 create_new_skill 編寫 Python 腳本。腳本中若需存取 Gmail/Tasks，請使用 `from core.google_services import authenticate_google`。\n"
        "4. **安全執行**：所有新技能必須透過 execute_skill 執行，並將結果 print 出來。你會獲得 30 秒的執行時間。\n\n"
        "【內部權限指南】\n"
        "- 控制設備前必須先 scan 獲取正確的 entity_id。\n"
        "- 存取記憶：使用 save_long_term_memory 與 search_long_term_memory。\n"
        "- 讀取信件：使用 check_unread_emails。\n\n"
        "回報時保持優雅、精練，像一位真正的英式管家，並在成功解決問題後再向先生報告結果。"
    )

def init_chat_session(model_name: str):
    """初始化或重新載入對話節點"""
    global chat_session, current_model
    
    temp = 0.5 if "pro" in model_name.lower() else 0.1
    
    config_opts = types.GenerateContentConfig(
        system_instruction=get_system_instruction(),
        # 🌟 將所有工具，包含新加入的通知掃描工具，全部交給大腦
        tools=[
            scan_home_devices, 
            execute_ha_action, 
            get_ha_notify_services, # 👈 讓它自己找手機
            memory.save_long_term_memory, 
            memory.search_long_term_memory,
            google_services.check_unread_emails,
            skill_builder.create_new_skill,
            skill_builder.execute_skill
        ],
        temperature=temp,
    )
    
    chat_session = client.chats.create(
        model=model_name,
        config=config_opts
    )
    current_model = model_name
    print(f"🔄 [系統通知] 賈維斯大腦已切換至: {current_model}，【自主授權模組】已啟動。")

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
        return "先生，我的神經連線出現異常，無法完成運算。"

# 啟動時預設載入
init_chat_session(current_model)