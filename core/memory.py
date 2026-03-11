import sqlite3
import json
import os
from datetime import datetime

# ==========================================
# 📂 系統路徑設定 (確保檔案長在專案根目錄)
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(BASE_DIR, "core_settings.json")
DB_PATH = os.path.join(BASE_DIR, "archive.db")


# ==========================================
# 🧠 Tier 1: 核心設定與短期記憶 (JSON 管理員)
# ==========================================
def init_core_settings():
    """初始化核心記憶，如果檔案不存在就自動建立一個預設版"""
    if not os.path.exists(JSON_PATH):
        default_settings = {
            "user_persona": {
                "name": "Steven",
                "role": "長官/先生"
            },
            "habits": [
                "喜歡精簡、高效的回覆",
                "目前正在開發智慧家庭與 AI 專案"
            ],
            "home_specs": "目前主臥室有飛利浦吸頂燈，並有 HA (Home Assistant) 系統",
            "recent_context": "正在進行賈維斯大腦的階段二：長期記憶系統建置。"
        }
        with open(JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(default_settings, f, indent=4, ensure_ascii=False)
        print("🟢 [記憶模組] 已自動建立核心記憶檔 (core_settings.json)")


def get_core_prompt() -> str:
    """讀取 JSON 並轉換成大腦看得懂的 Prompt 文字"""
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 將 JSON 轉化為易讀的字串
        prompt = "【系統絕對記憶 (核心設定)】\n"
        prompt += f"- 先生稱呼：{data['user_persona']['name']} ({data['user_persona']['role']})\n"
        prompt += f"- 先生習慣：{', '.join(data['habits'])}\n"
        prompt += f"- 家庭設備概況：{data['home_specs']}\n"
        prompt += f"- 近期專案上下文：{data['recent_context']}\n"
        return prompt
    except Exception as e:
        print(f"❌ 讀取核心記憶失敗: {e}")
        return "【系統絕對記憶】讀取失敗，請以預設管家模式運作。"


# ==========================================
# 🗄️ Tier 3: 長期檔案櫃 (SQLite 管理員)
# ==========================================
def init_archive_db():
    """初始化 SQLite 資料庫，建立記憶資料表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 建立 long_term_memories 資料表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS long_term_memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            tags TEXT NOT NULL,
            content TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    if not os.path.exists(DB_PATH):
        print("🟢 [記憶模組] 已自動建立長期檔案櫃 (archive.db)")


def save_long_term_memory(tags: str, content: str) -> str:
    """
    提供給 AI 的工具：儲存長期記憶。
    tags: 記憶的分類標籤 (例如 '#密碼 #大門')
    content: 記憶的具體內容 (例如 '大門密碼改為 5678')
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO long_term_memories (timestamp, tags, content) VALUES (?, ?, ?)",
            (current_time, tags, content)
        )
        conn.commit()
        conn.close()
        return f"✅ 記憶已成功封存至檔案櫃。標籤: [{tags}]"
    except Exception as e:
        return f"❌ 記憶存檔失敗: {e}"


def search_long_term_memory(keyword: str) -> str:
    """
    提供給 AI 的工具：檢索長期記憶。
    keyword: 搜尋關鍵字 (例如 '密碼' 或 '大門')
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 使用 LIKE 進行模糊搜尋 (標籤或內容包含關鍵字即可)
        query = f"%{keyword}%"
        cursor.execute(
            "SELECT timestamp, tags, content FROM long_term_memories WHERE tags LIKE ? OR content LIKE ? ORDER BY id DESC LIMIT 5",
            (query, query)
        )
        results = cursor.fetchall()
        conn.close()

        if not results:
            return f"🔍 在檔案櫃中找不到與「{keyword}」相關的紀錄。"

        # 將搜尋結果整理成字串回傳給 AI
        reply = f"🔍 找到與「{keyword}」相關的歷史紀錄：\n"
        for row in results:
            reply += f"[{row[0]}] 標籤:{row[1]} 內容:{row[2]}\n"
        return reply

    except Exception as e:
        return f"❌ 記憶檢索失敗: {e}"


# ==========================================
# 🚀 模組載入時自動執行初始化
# ==========================================
init_core_settings()
init_archive_db()