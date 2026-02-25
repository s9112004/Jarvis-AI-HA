import os
from dotenv import load_dotenv

# ==========================================
# 🛡️ 終極安保補丁：強制清除系統 Proxy 干擾
# (防止 Linux 底層幽靈變數導致 urllib3 撞牆)
# ==========================================
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['ALL_PROXY'] = ''

# 載入保險箱
load_dotenv()

# 提取金鑰
TG_TOKEN = os.getenv("TG_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
HA_URL = os.getenv("HA_URL")
HA_TOKEN = os.getenv("HA_TOKEN")

# 啟動前安檢
if not TG_TOKEN or not GEMINI_API_KEY:
    print("🚨 致命錯誤：找不到 Telegram 或 Gemini 金鑰！請檢查 .env 檔案。")
    exit(1)