import sqlite3
import time
import os

DB_FILE = "jarvis_queue.db"


def get_conn():
    return sqlite3.connect(DB_FILE, timeout=10)


def init_db():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS bot_state (id INTEGER PRIMARY KEY, status TEXT)''')
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
        c.execute('SELECT count(*) FROM bot_state')
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO bot_state (id, status) VALUES (1, "IDLE")')

        c.execute('UPDATE tasks SET status="PENDING" WHERE status="PROCESSING"')
        c.execute('UPDATE bot_state SET status="IDLE" WHERE id=1')
        conn.commit()


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
        # 🌟 修正 Bug：先將資料存入變數，再判斷，避免游標被消耗
        row = c.fetchone()
        return dict(row) if row else None


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


init_db()