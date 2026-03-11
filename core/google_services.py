import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build  # 🌟 新增：用來建立 Google API 服務的工具

# 從原本的 .readonly 改成完全控制權限
SCOPES = [
    'https://mail.google.com/',  # 🌟 Gmail 上帝權限：可讀、可寫、可刪、可發送
    'https://www.googleapis.com/auth/tasks'
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")

def authenticate_google():
    """處理 Google OAuth 2.0 認證並回傳憑證"""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("⚠️ 準備開啟瀏覽器進行 Google 授權...")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())
    return creds

# ==========================================
# 🛠️ 賈維斯的新工具：讀取 Gmail
# ==========================================
def check_unread_emails() -> str:
    """提供給 AI 的工具：讀取最新的未讀信件"""
    try:
        # 1. 拿出通行證
        creds = authenticate_google()
        # 2. 呼叫 Gmail 服務台
        service = build('gmail', 'v1', credentials=creds)
        
        # 3. 搜尋「收件匣」中「未讀」的信件 (設定最多抓最新 5 封，避免資訊爆炸)
        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=5).execute()
        messages = results.get('messages', [])

        if not messages:
            return "📭 報告先生，目前收件匣沒有新的未讀信件。"

        email_summaries = []
        for msg in messages:
            # 根據信件 ID 抓取詳細內容
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = msg_data['payload']['headers']
            
            # 從標頭檔中過濾出「主旨 (Subject)」和「寄件者 (From)」
            subject = next((header['value'] for header in headers if header['name'].lower() == 'subject'), "無標題")
            sender = next((header['value'] for header in headers if header['name'].lower() == 'from'), "未知寄件者")
            
            email_summaries.append(f"- 寄件者：[{sender}] | 主旨：{subject}")

        # 4. 把結果包裝成漂亮的字串回傳給大腦
        reply = f"📬 先生，為您整理出最新的未讀信件如下：\n" + "\n".join(email_summaries)
        return reply

    except Exception as e:
        return f"❌ 讀取 Gmail 失敗，神經網路連線異常：{e}"

if __name__ == "__main__":
    # 單獨測試：如果您現在在終端機跑這個檔案，他應該會印出您的未讀信件！
    print("正在測試讀取 Gmail...")
    print(check_unread_emails())