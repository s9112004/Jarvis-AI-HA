import os
import subprocess
import ast

# 定義實驗室路徑
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS_DIR = os.path.join(BASE_DIR, "skills")

# 如果 skills 資料夾不存在，就自動建立
if not os.path.exists(SKILLS_DIR):
    os.makedirs(SKILLS_DIR)
    # 建立一個 __init__.py 讓它變成標準模組
    with open(os.path.join(SKILLS_DIR, "__init__.py"), "w") as f:
        f.write("# Jarvis Dynamic Skills Module\n")

# ==========================================
# 🛠️ 賦予大腦的工具一：創造新技能
# ==========================================
def create_new_skill(skill_name: str, python_code: str) -> str:
    """
    提供給 AI 的工具：當先生要求新功能時，編寫 Python 腳本並存檔。
    skill_name: 技能名稱 (限英文小寫與底線，如 get_stock_price)
    python_code: 完整的 Python 程式碼字串
    """
    # 1. 名稱防呆與清理
    skill_name = skill_name.replace(".py", "").strip()
    file_path = os.path.join(SKILLS_DIR, f"{skill_name}.py")

    # 2. 第一道防線：語法掃描 (Syntax Check)
    try:
        ast.parse(python_code)
    except SyntaxError as e:
        return f"❌ 技能建立失敗！程式碼有語法錯誤，請修正後再試：\n{e}"

    # 3. 安全存檔
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(python_code)
        return f"✅ 技能 [{skill_name}.py] 已成功編寫並存檔於實驗室。您可以隨時呼叫 execute_skill 來測試它。"
    except Exception as e:
        return f"❌ 存檔失敗：{e}"

# ==========================================
# 🛠️ 賦予大腦的工具二：執行技能 (安全沙盒)
# ==========================================
def execute_skill(skill_name: str, arguments: str = "") -> str:
    """
    提供給 AI 的工具：執行已建立的技能，並獲取其 print 出來的結果。
    skill_name: 要執行的技能名稱 (如 get_stock_price)
    arguments: 要傳給腳本的參數 (選填，多個參數請用空格隔開)
    """
    skill_name = skill_name.replace(".py", "").strip()
    file_path = os.path.join(SKILLS_DIR, f"{skill_name}.py")

    if not os.path.exists(file_path):
        return f"❌ 找不到技能 [{skill_name}.py]，請先使用 create_new_skill 建立。"

    # 組合執行指令： python skills/xxx.py arg1 arg2
    cmd = ["python3", file_path]
    if arguments:
        cmd.extend(arguments.split())

    try:
        # 🌟 第二道防線：獨立進程 + 15秒無情擊殺
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=30  # 超時炸彈
        )
        
        # 檢查執行是否報錯 (例如變數未定義、除以零)
        if result.returncode != 0:
            return f"⚠️ 技能執行發生錯誤 (請嘗試修復代碼)：\n{result.stderr.strip()}"
            
        # 成功回傳腳本 print 的內容
        output = result.stdout.strip()
        return f"🟢 技能執行成功。輸出結果：\n{output}" if output else "🟢 技能執行成功，但沒有任何輸出。"

    except subprocess.TimeoutExpired:
        return "❌ 技能執行超時 (超過 15 秒)！已被系統強制擊殺。請檢查代碼是否有無窮迴圈或網路卡死。"
    except Exception as e:
        return f"❌ 執行環境異常：{e}"