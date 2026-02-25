import requests
from core import config

# 從 config 讀取連線資訊
HEADERS = {
    "Authorization": f"Bearer {config.HA_TOKEN}",
    "Content-Type": "application/json",
}

def get_all_entities():
    """
    獲取 Home Assistant 中所有的設備清單與狀態。
    這是賈維斯的「感知掃描」，讓他看清家裡有哪些東西。
    """
    url = f"{config.HA_URL}/api/states"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            # 簡化清單，過濾出 AI 易於理解的格式
            entities = res.json()
            simplified_list = []
            for e in entities:
                # 只保留常見的控制類別，避免清單太長干擾 AI
                domain = e['entity_id'].split(".")[0]
                if domain in ['light', 'switch', 'fan', 'media_player', 'climate', 'sensor']:
                    simplified_list.append({
                        "entity_id": e['entity_id'],
                        "name": e.get('attributes', {}).get('friendly_name', e['entity_id']),
                        "state": e['state']
                    })
            return simplified_list
        else:
            print(f"❌ 掃描失敗，HA 回應碼: {res.status_code}")
            return f"無法獲取清單 (錯誤碼: {res.status_code})"
    except Exception as e:
        print(f"❌ HA 連線異常: {e}")
        return f"連線錯誤: {e}"

def control_entity(entity_id: str, action: str):
    """
    通用控制函式。
    entity_id: 設備 ID (例如 light.master_bedroom)
    action: 動作 (turn_on / turn_off)
    """
    domain = entity_id.split(".")[0]
    # 根據 HA 的 Service 規則拼接 URL
    url = f"{config.HA_URL}/api/services/{domain}/{action}"
    
    # 建立傳送數據
    data = {"entity_id": entity_id}
    
    try:
        # 正式發送指令
        res = requests.post(url, headers=HEADERS, json=data, timeout=10)
        
        # 【重要】長官，這是我們用來抓出「騙人行為」的監測點
        debug_msg = f"DEBUG: 嘗試控制 [{entity_id}] 執行 [{action}], HA 回傳碼: {res.status_code}"
        print(f"===============================================")
        print(debug_msg)
        print(f"HA 回應內容: {res.text}")
        print(f"===============================================")
        
        if res.status_code == 200:
            return f"指令執行成功：{entity_id} 已執行 {action}"
        elif res.status_code == 404:
            return f"指令失敗：找不到該設備 ({entity_id})"
        elif res.status_code == 400:
            return f"指令失敗：格式錯誤或該設備不支援此動作"
        else:
            return f"指令失敗，伺服器回傳：{res.text}"
            
    except Exception as e:
        error_msg = f"連線至 HA 時發生物理性錯誤: {e}"
        print(f"❌ {error_msg}")
        return error_msg