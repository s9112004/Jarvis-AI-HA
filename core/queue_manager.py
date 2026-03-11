import sqlite3
import time
import os

DB_FILE = "jarvis_queue.db"


def get_conn():
    """獲取資料庫連線，設定 timeout 避免鎖死"""
    return sqlite3.connect(DB_FILE, timeout=10)


def init_db():
    """初始化資料庫與資料表"""
    with get_conn() as conn:
        c = conn.cursor()
        # 1. 狀態鎖資料表 (永遠只有一筆紀錄)
        c.execute('''CREATE TABLE IF NOT EXISTS bot_state (id INTEGER PRIMARY KEY, status TEXT)''')
        # 2. 任務排隊資料表
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        message_id INTEGER,
                        text TEXT,
                        task_type TEXT,
                        status TEXT,
                        response TEXT,
                        created_at REAL
                    )''')

        # 確保狀態表有初始值
        c.execute('SELECT count(*) FROM bot_state')
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO bot_state (id, status) VALUES (1, "IDLE")')

        # 每次重啟系統時，將卡住的任務重置，並解開大腦鎖
        c.execute('UPDATE tasks SET status="PENDING" WHERE status="PROCESSING"')
        c.execute('UPDATE bot_state SET status="IDLE" WHERE id=1')
        conn.commit()


# --- 狀態鎖 (State Lock) 模組 ---
def get_state():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('SELECT status FROM bot_state WHERE id=1')
        return c.fetchone()[0]


def set_state(new_state):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('UPDATE bot_state SET status=? WHERE id=1', (new_state,))
        conn.commit()


# --- 任務佇列 (Task Queue) 模組 ---
def add_task(chat_id, message_id, text, task_type="chat"):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO tasks (chat_id, message_id, text, task_type, status, created_at) 
                     VALUES (?, ?, ?, ?, "PENDING", ?)''',
                  (chat_id, message_id, text, task_type, time.time()))
        conn.commit()


def get_next_pending_task():
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM tasks WHERE status="PENDING" ORDER BY created_at ASC LIMIT 1')
        return dict(c.fetchone()) if c.fetchone() else None


def mark_task_processing(task_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('UPDATE tasks SET status="PROCESSING" WHERE id=?', (task_id,))
        conn.commit()


def mark_task_completed(task_id, response):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('UPDATE tasks SET status="COMPLETED", response=? WHERE id=?', (response, task_id))
        conn.commit()


def get_completed_tasks():
    with get_conn() as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM tasks WHERE status="COMPLETED"')
        return [dict(row) for row in c.fetchall()]


def delete_task(task_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('DELETE FROM tasks WHERE id=?', (task_id,))
        conn.commit()


# 檔案被載入時，自動初始化資料庫
init_db()