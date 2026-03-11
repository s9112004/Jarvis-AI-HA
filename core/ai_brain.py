from google import genai
from google.genai import types
from core import config
from core import smart_home
from core import memory
from core import google_services
from core import skill_builder  # 🌟 新增：載入防爆實驗室模組
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
# 🧠 大腦核心狀態管理 (完全體)
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
        "1. 控制設備前必須先用 scan_home_devices 獲取清單，找到正確的 entity_id 並執行 execute_ha_action。\n\n"
        "【長期記憶守則】\n"
        "1. 主動使用 save_long_term_memory 與 search_long_term_memory 存取先生的專屬記憶。\n\n"
        "【數位助理守則】\n"
        "1. 使用 check_unread_emails 讀取並摘要未讀信件。\n\n"
        "【🤖 自我進化守則 (最高指導原則)】\n"
        "1. 當先生要求你執行你目前『不會做』的事情（例如：查當前股價、算複雜數學、爬取網頁資訊），你必須展現自主性，自己寫程式來解決！\n"
        "2. 步驟一：呼叫 create_new_skill 工具，為自己編寫一個 Python 腳本。腳本必須將最終結果用 `print()` 印出，絕不能修改系統核心檔案。\n"
        "3. 步驟二：腳本建立成功後，立刻呼叫 execute_skill 工具來執行它，並讀取 print 出來的結果。\n"
        "4. 步驟三：將執行結果整理成優雅的口語回報給先生。如果執行報錯，請告訴先生你遇到了錯誤，並嘗試修正代碼重新建立技能。\n\n"
        "回報時請保持優雅、精練，並展現英式管家的專業。"
    )

def init_chat_session(model_name: str):
    """初始化或重新載入對話節點"""
    global chat_session, current_model
    
    temp = 0.5 if "pro" in model_name.lower() else 0.1
    
    config_opts = types.GenerateContentConfig(
        system_instruction=get_system_instruction(),
        # 🌟 新增：把實驗室的兩把鑰匙交給大腦
        tools=[
            scan_home_devices, 
            execute_ha_action, 
            memory.save_long_term_memory, 
            memory.search_long_term_memory,
            google_services.check_unread_emails,
            skill_builder.create_new_skill,  # 👈 寫扣能力
            skill_builder.execute_skill      # 👈 執行能力
        ],
        temperature=temp,
    )
    
    chat_session = client.chats.create(
        model=model_name,
        config=config_opts
    )
    current_model = model_name
    print(f"🔄 [系統通知] 賈維斯大腦已切換至: {current_model}，【自我進化模組】已上線。")

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