import os
import sqlite3
import time

DB_FILE = os.getenv("JARVIS_DB_FILE", "jarvis_queue.db")

STATUS_PENDING = "PENDING"
STATUS_PROCESSING = "PROCESSING"
STATUS_COMPLETED = "COMPLETED"
STATUS_SENDING = "SENDING"
STATUS_SEND_FAILED = "SEND_FAILED"
STATUS_FAILED = "FAILED"


def get_conn():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def _get_existing_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _ensure_column(cursor, table_name, column_name, definition):
    existing_columns = _get_existing_columns(cursor, table_name)
    if column_name not in existing_columns:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")


def init_db():
    now = time.time()

    with get_conn() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS bot_state (
                id INTEGER PRIMARY KEY,
                status TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                message_id INTEGER,
                text TEXT,
                task_type TEXT,
                status TEXT,
                response TEXT,
                created_at REAL,
                updated_at REAL DEFAULT 0,
                next_retry_at REAL DEFAULT 0,
                last_error TEXT,
                process_retry_count INTEGER DEFAULT 0,
                send_retry_count INTEGER DEFAULT 0,
                processing_started_at REAL,
                sending_started_at REAL,
                completed_at REAL
            )
        """)

        # 舊版 DB 自動補欄位
        _ensure_column(c, "tasks", "updated_at", "REAL DEFAULT 0")
        _ensure_column(c, "tasks", "next_retry_at", "REAL DEFAULT 0")
        _ensure_column(c, "tasks", "last_error", "TEXT")
        _ensure_column(c, "tasks", "process_retry_count", "INTEGER DEFAULT 0")
        _ensure_column(c, "tasks", "send_retry_count", "INTEGER DEFAULT 0")
        _ensure_column(c, "tasks", "processing_started_at", "REAL")
        _ensure_column(c, "tasks", "sending_started_at", "REAL")
        _ensure_column(c, "tasks", "completed_at", "REAL")

        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status_next_retry_created
            ON tasks(status, next_retry_at, created_at)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status_created
            ON tasks(status, created_at)
        """)

        c.execute("SELECT COUNT(*) FROM bot_state")
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO bot_state (id, status) VALUES (1, "IDLE")')

        # 啟動時做狀態修復
        c.execute("""
            UPDATE tasks
            SET status = ?, processing_started_at = NULL, updated_at = ?
            WHERE status = ?
        """, (STATUS_PENDING, now, STATUS_PROCESSING))

        c.execute("""
            UPDATE tasks
            SET status = ?, sending_started_at = NULL, updated_at = ?
            WHERE status = ?
        """, (STATUS_COMPLETED, now, STATUS_SENDING))

        c.execute("""
            UPDATE tasks
            SET status = ?
            WHERE status IS NULL OR status = ''
        """, (STATUS_PENDING,))

        c.execute("""
            UPDATE tasks
            SET next_retry_at = COALESCE(next_retry_at, created_at, ?)
        """, (now,))

        c.execute("""
            UPDATE tasks
            SET updated_at = COALESCE(updated_at, created_at, ?)
        """, (now,))

        c.execute("""
            UPDATE tasks
            SET process_retry_count = COALESCE(process_retry_count, 0),
                send_retry_count = COALESCE(send_retry_count, 0)
        """)

        c.execute('UPDATE bot_state SET status = "IDLE" WHERE id = 1')
        conn.commit()


def get_state():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("SELECT status FROM bot_state WHERE id = 1")
        row = c.fetchone()
        return row["status"] if row else "IDLE"


def set_state(new_state):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("UPDATE bot_state SET status = ? WHERE id = 1", (new_state,))
        conn.commit()


def add_task(chat_id, message_id, text, task_type="chat"):
    now = time.time()
    clean_text = (text or "").strip()

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO tasks (
                chat_id, message_id, text, task_type, status, response,
                created_at, updated_at, next_retry_at, last_error,
                process_retry_count, send_retry_count,
                processing_started_at, sending_started_at, completed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            message_id,
            clean_text,
            task_type,
            STATUS_PENDING,
            None,
            now,
            now,
            now,
            None,
            0,
            0,
            None,
            None,
            None,
        ))
        conn.commit()


def claim_next_pending_task():
    conn = get_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        c = conn.cursor()
        now = time.time()

        c.execute("""
            SELECT *
            FROM tasks
            WHERE status = ?
              AND COALESCE(next_retry_at, 0) <= ?
            ORDER BY created_at ASC
            LIMIT 1
        """, (STATUS_PENDING, now))
        row = c.fetchone()

        if row is None:
            conn.commit()
            return None

        c.execute("""
            UPDATE tasks
            SET status = ?, processing_started_at = ?, updated_at = ?
            WHERE id = ? AND status = ?
        """, (STATUS_PROCESSING, now, now, row["id"], STATUS_PENDING))

        if c.rowcount != 1:
            conn.commit()
            return None

        conn.commit()
        task = dict(row)
        task["status"] = STATUS_PROCESSING
        task["processing_started_at"] = now
        task["updated_at"] = now
        return task

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_next_pending_task():
    # 保留舊介面名稱，內部改成原子 claim
    return claim_next_pending_task()


def mark_task_processing(task_id):
    now = time.time()
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE tasks
            SET status = ?, processing_started_at = ?, updated_at = ?
            WHERE id = ?
        """, (STATUS_PROCESSING, now, now, task_id))
        conn.commit()


def mark_task_completed(task_id, response, error=None):
    now = time.time()
    response_text = response if isinstance(response, str) and response.strip() else "⚠️ 任務已完成，但沒有可回覆的內容。"

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE tasks
            SET status = ?,
                response = ?,
                last_error = ?,
                completed_at = ?,
                next_retry_at = ?,
                updated_at = ?,
                processing_started_at = NULL,
                sending_started_at = NULL
            WHERE id = ?
        """, (
            STATUS_COMPLETED,
            response_text,
            error,
            now,
            now,
            now,
            task_id,
        ))
        conn.commit()


def requeue_task(task_id, delay_seconds=10, error=None, increment_retry=True):
    now = time.time()
    next_retry_at = now + max(0, int(delay_seconds))

    sql = """
        UPDATE tasks
        SET status = ?,
            last_error = ?,
            next_retry_at = ?,
            updated_at = ?,
            processing_started_at = NULL,
            sending_started_at = NULL
    """
    params = [STATUS_PENDING, error, next_retry_at, now]

    if increment_retry:
        sql += ", process_retry_count = COALESCE(process_retry_count, 0) + 1"

    sql += " WHERE id = ?"
    params.append(task_id)

    with get_conn() as conn:
        c = conn.cursor()
        c.execute(sql, tuple(params))
        conn.commit()


def claim_next_outgoing_task():
    conn = get_conn()
    try:
        conn.execute("BEGIN IMMEDIATE")
        c = conn.cursor()
        now = time.time()

        c.execute("""
            SELECT *
            FROM tasks
            WHERE status IN (?, ?)
              AND COALESCE(next_retry_at, 0) <= ?
            ORDER BY COALESCE(completed_at, created_at) ASC, created_at ASC
            LIMIT 1
        """, (STATUS_COMPLETED, STATUS_SEND_FAILED, now))
        row = c.fetchone()

        if row is None:
            conn.commit()
            return None

        c.execute("""
            UPDATE tasks
            SET status = ?, sending_started_at = ?, updated_at = ?
            WHERE id = ? AND status IN (?, ?)
        """, (
            STATUS_SENDING,
            now,
            now,
            row["id"],
            STATUS_COMPLETED,
            STATUS_SEND_FAILED,
        ))

        if c.rowcount != 1:
            conn.commit()
            return None

        conn.commit()
        task = dict(row)
        task["status"] = STATUS_SENDING
        task["sending_started_at"] = now
        task["updated_at"] = now
        return task

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_send_failed(task_id, error, delay_seconds=10, permanent=False):
    now = time.time()

    with get_conn() as conn:
        c = conn.cursor()

        if permanent:
            c.execute("""
                UPDATE tasks
                SET status = ?,
                    last_error = ?,
                    updated_at = ?,
                    sending_started_at = NULL,
                    next_retry_at = NULL
                WHERE id = ?
            """, (STATUS_FAILED, error, now, task_id))
        else:
            next_retry_at = now + max(0, int(delay_seconds))
            c.execute("""
                UPDATE tasks
                SET status = ?,
                    last_error = ?,
                    updated_at = ?,
                    next_retry_at = ?,
                    sending_started_at = NULL,
                    send_retry_count = COALESCE(send_retry_count, 0) + 1
                WHERE id = ?
            """, (STATUS_SEND_FAILED, error, now, next_retry_at, task_id))

        conn.commit()


def get_completed_tasks():
    # 保留舊介面，必要時仍可用
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT *
            FROM tasks
            WHERE status = ?
            ORDER BY COALESCE(completed_at, created_at) ASC, created_at ASC
        """, (STATUS_COMPLETED,))
        return [dict(row) for row in c.fetchall()]


def delete_task(task_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()


init_db()