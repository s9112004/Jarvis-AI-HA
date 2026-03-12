import os
import logging
from logging.handlers import TimedRotatingFileHandler

# 1. 自動建立 logs 資料夾 (在專案根目錄)
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
LOG_DIR = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, 'jarvis.log')

# 2. 終端機顏色格式化器 (讓您看 Terminal 時依然有顏色提示)
class ColorFormatter(logging.Formatter):
    COLORS = {
        'INFO': '\033[94m',       # 藍色
        'WARNING': '\033[93m',    # 黃色
        'ERROR': '\033[91m',      # 紅色
        'CRITICAL': '\033[91m\033[1m' # 粗體紅色
    }
    RESET = '\033[0m'

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        format_str = f"{log_color}[%(asctime)s] [%(levelname)s] %(message)s{self.RESET}"
        formatter = logging.Formatter(format_str, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

def setup_logger():
    logger = logging.getLogger("Jarvis")
    
    # 避免重複綁定
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(logging.INFO)

    # 🌟 3. 檔案日誌處理器 (每天午夜切割，保留 60 天)
    file_handler = TimedRotatingFileHandler(
        filename=LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=60,  # 長官指定的 60 天輪轉銷毀機制
        encoding="utf-8"
    )
    file_handler.suffix = "%Y-%m-%d" # 切割後的檔名後綴 (例如 jarvis.log.2026-03-12)
    
    # 檔案寫入格式 (加入發生錯誤的檔案名稱與行號，方便抓戰犯)
    file_formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # 4. 終端機日誌處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColorFormatter())

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# 實例化，供其他檔案直接 import
logger = setup_logger()