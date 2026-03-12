import os
import requests
from dotenv import load_dotenv
from core.logger import logger  # 引入日誌系統記錄錯誤

load_dotenv()
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

HEADERS = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json",
}

# 🌟 統一設定超時限制 (5秒連線，10秒讀取)
REQ_TIMEOUT = (5, 10)

def get_ha_state(entity_id):
    """獲取實體狀態，具備超時防護"""
    url = f"{HA_URL}/api/states/{entity_id}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQ_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"連線 HA 獲取 {entity_id} 狀態超時！(超過 10 秒)")
        return {"error": "連線超時，Home Assistant 無回應"}
    except requests.exceptions.RequestException as e:
        logger.error(f"連線 HA 發生錯誤: {e}")
        return {"error": f"連線異常: {e}"}

def call_ha_service(domain, service, service_data=None):
    """呼叫 HA 服務，具備超時防護"""
    url = f"{HA_URL}/api/services/{domain}/{service}"
    try:
        response = requests.post(url, headers=HEADERS, json=service_data or {}, timeout=REQ_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        logger.error(f"呼叫 HA 服務 {domain}.{service} 超時！")
        return {"error": "服務呼叫超時，Home Assistant 無回應"}
    except requests.exceptions.RequestException as e:
        logger.error(f"呼叫 HA 服務發生錯誤: {e}")
        return {"error": f"連線異常: {e}"}

def get_ha_notify_services():
    """獲取通知服務清單，具備超時防護"""
    url = f"{HA_URL}/api/services"
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQ_TIMEOUT)
        response.raise_for_status()
        services = response.json()
        
        for domain in services:
            if domain.get("domain") == "notify":
                return domain.get("services", {})
        return {}
    except requests.exceptions.Timeout:
        logger.error("獲取 HA 通知服務清單超時！")
        return {"error": "連線超時"}
    except requests.exceptions.RequestException as e:
        logger.error(f"獲取通知服務清單錯誤: {e}")
        return {"error": str(e)}