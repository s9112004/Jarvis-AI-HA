import os
from urllib.parse import urlparse

import requests


def _ok(result: dict):
    result["ok"] = True
    return result


def _fail(result: dict, error: Exception | str):
    result["ok"] = False
    result["error"] = str(error)
    return result


def check_telegram():
    result = {"service": "telegram"}
    token = os.getenv("TG_TOKEN")

    if not token:
        return _fail(result, "TG_TOKEN 未設定")

    try:
        url = f"https://api.telegram.org/bot{token}/getMe"
        resp = requests.get(url, timeout=(5, 10))

        if resp.ok:
            data = resp.json()
            result["status_code"] = resp.status_code
            result["description"] = data.get("description", "OK")
            return _ok(result)

        result["status_code"] = resp.status_code
        return _fail(result, f"Telegram 回傳 HTTP {resp.status_code}")

    except Exception as e:
        return _fail(result, e)


def check_gemini():
    result = {"service": "gemini"}

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    try:
        if api_key:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        else:
            url = "https://generativelanguage.googleapis.com"

        resp = requests.get(url, timeout=(5, 10), allow_redirects=True)
        result["status_code"] = resp.status_code

        # 這裡重點是可達性，不強求一定 200
        return _ok(result)

    except Exception as e:
        return _fail(result, e)


def check_home_assistant():
    result = {"service": "home_assistant"}

    ha_url = os.getenv("HA_URL")
    ha_token = os.getenv("HA_TOKEN")

    if not ha_url:
        return _fail(result, "HA_URL 未設定")

    try:
        base = ha_url.rstrip("/")
        target = f"{base}/api/"
        headers = {}

        if ha_token:
            headers["Authorization"] = f"Bearer {ha_token}"

        resp = requests.get(target, headers=headers, timeout=(5, 10))
        result["status_code"] = resp.status_code
        result["host"] = urlparse(base).netloc

        # HA /api/ 正常授權時通常會 200；若 401 也表示至少網路打得到
        if resp.status_code in (200, 401):
            return _ok(result)

        return _fail(result, f"HA 回傳 HTTP {resp.status_code}")

    except Exception as e:
        return _fail(result, e)


def run_startup_checks(logger=None):
    results = {
        "telegram": check_telegram(),
        "gemini": check_gemini(),
        "home_assistant": check_home_assistant(),
    }

    if logger:
        logger.info("🔍 啟動自我檢查開始...")
        for name, result in results.items():
            if result.get("ok"):
                logger.info(f"✅ {name} 檢查通過: {result}")
            else:
                logger.warning(f"⚠️ {name} 檢查失敗: {result}")
        logger.info("🔍 啟動自我檢查完成。")

    return results