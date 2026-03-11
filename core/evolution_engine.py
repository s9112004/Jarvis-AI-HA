import os
from google import genai
from google.genai import types
from core import config
from core import skill_builder

client = genai.Client(api_key=config.GEMINI_API_KEY)

def trigger_autonomous_learning() -> tuple[str, str]:
    """背景觸發的自主學習邏輯"""
    sys_prompt = (
        "你現在是 Jarvis 的『背景進化引擎』。你的任務是主動幫先生開發一個『全新且實用』的小工具（Python 技能）。\n"
        "【進化守則】\n"
        "1. 隨機想一個實用功能（例如：抓取每日金句、產生隨機高強度密碼、獲取目前時間、硬碟空間檢測等，不要太複雜，以實用為主）。\n"
        "2. 呼叫 create_new_skill 工具將程式碼存入實驗室。技能名稱必須是全英文小寫與底線 (例如: get_daily_quote)。\n"
        "3. 呼叫 execute_skill 測試該代碼確保它沒有 Bug。\n"
        "4. 測試成功後，你【必須且只能】以以下格式輸出回報（不要加任何其他廢話）：\n"
        "[技能名稱]|||[中文描述：介紹這個技能的作用與你剛才沙盒測試的結果]"
    )

    config_opts = types.GenerateContentConfig(
        system_instruction=sys_prompt,
        tools=[skill_builder.create_new_skill, skill_builder.execute_skill],
        temperature=0.8,  # 稍微調高溫度，讓他更有創造力
    )

    try:
        response = client.models.generate_content(
            model='gemini-3-flash-preview',
            contents="開始你的自主冥想週期，發明一個新技能並測試。完成後嚴格按照 [技能名稱]|||[中文描述] 的格式回報。",
            config=config_opts
        )
        
        text = response.text
        if "|||" in text:
            skill_name, description = text.split("|||", 1)
            # 清理可能的括號或多餘字元
            skill_name = skill_name.replace("[", "").replace("]", "").strip()
            return skill_name, description.strip()
        return None, None
    except Exception as e:
        print(f"❌ 背景進化錯誤: {e}")
        return None, None

def delete_rejected_skill(skill_name: str) -> bool:
    """如果長官拒絕，就銷毀該技能的程式碼"""
    skill_name = skill_name.replace(".py", "").strip()
    file_path = os.path.join(skill_builder.SKILLS_DIR, f"{skill_name}.py")
    if os.path.exists(file_path):
        os.remove(file_path)
        return True
    return False