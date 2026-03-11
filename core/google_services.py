import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# 權限範圍 (Scopes)：我們要求 Gmail 的唯讀權限，以及 Tasks 的讀寫權限
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/tasks'
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

def authenticate_google():
    """處理 Google OAuth 2.0 認證並回傳憑證"""
    creds = None
    
    # 1. 檢查是否已經有之前產生過的 token.json (永久通行證)
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        
    # 2. 如果沒有 token，或者 token 過期了，就重新要求授權
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # 🌟 這裡會彈出網頁瀏覽器要求長官登入授權
            print("⚠️ 準備開啟瀏覽器進行 Google 授權...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            
        # 3. 授權成功後，把新的通行證存成 token.json，以後就不用再點網頁了
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
            
    print("🟢 [Google 服務] 憑證狀態：已成功獲得授權！")
    return creds

if __name__ == "__main__":
    # 單獨執行此檔案來測試認證
    authenticate_google()