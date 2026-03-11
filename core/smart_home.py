import requests
import os
from dotenv import load_dotenv

# 1. 載入環境變數
load_dotenv()

HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

# 檢查必要的變數
if not HA_URL or not HA_TOKEN:
    print("❌ 警告：HA_URL 或 HA_TOKEN 未在 .env 中設定，Home Assistant 功能將受限。")

HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "content-type": "application/json",
}

# ==========================================
# 🔍 基礎查詢工具
# ==========================================

def get_all_entities():
    """獲取 Home Assistant 中所有的實體與其詳細屬性清單"""
    url = f"{HA_URL}/api/states"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        states = response.json()
        
        device_list = []
        for state in states:
            entity_id = state['entity_id']
            friendly_name = state['attributes'].get('friendly_name', entity_id)
            status = state['state']
            device_list.append(f"ID: {entity_id} | 名稱: {friendly_name} | 狀態: {status}")
        
        return "\n".join(device_list)
    except Exception as e:
        return f"❌ 獲取設備清單失敗：{e}"

# ==========================================
# 📢 授權優化工具：自動發現通知服務
# ==========================================

def get_notify_services():
    """
    讓賈維斯自動掃描目前 HA 系統中所有可用的通知服務名稱。
    這能讓他在需要發送推播時，不必詢問先生，就能知道正確的服務名稱（例如 notify.mobile_app_iphone）。
    """
    url = f"{HA_URL}/api/services"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        services = response.json()
        
        # 過濾出所有屬於 notify 領域的服務
        notify_list = []
        for domain_data in services:
            if domain_data.get('domain') == 'notify':
                for service_name in domain_data.get('services', {}):
                    notify_list.append(f"notify.{service_name}")
        
        if not notify_list:
            return "📭 偵測完畢，但目前系統中沒有可用的通知服務。"
            
        return f"💡 偵測到系統中可用的通知服務有：{', '.join(notify_list)}"
    except Exception as e:
        return f"❌ 掃描通知服務時發生錯誤：{e}"

# ==========================================
# ⚡ 設備控制工具
# ==========================================

def control_entity(entity_id, action):
    """
    執行 Home Assistant 的動作。
    entity_id: 設備 ID (例如 light.living_room)
    action: 動作 (例如 turn_on, turn_off, toggle)
    """
    # 根據 entity_id 的開頭自動判斷 domain
    domain = entity_id.split('.')[0]
    url = f"{HA_URL}/api/services/{domain}/{action}"
    
    payload = {"entity_id": entity_id}
    
    try:
        response = requests.post(url, headers=HEADERS, json=payload, timeout=10)
        response.raise_for_status()
        return f"✅ 成功執行動作：對 {entity_id} 進行 {action}。"
    except Exception as e:
        # 如果是特殊動作或 domain 不匹配，提供詳細錯誤回傳給 AI 進行修正
        return f"❌ 動作執行失敗。原因：{e} (請檢查 ID 或 Action 是否正確)"

# 測試用 (可選)
if __name__ == "__main__":
    print("--- 正在測試自動發現通知服務 ---")
    print(get_notify_services())