import os
import sqlite3
import time
import uuid

DB_FILE = os.getenv("JARVIS_DB_FILE", "jarvis_queue.db")

STATUS_PENDING = "PENDING"
STATUS_PROCESSING = "PROCESSING"
STATUS_COMPLETED = "COMPLETED"
STATUS_SENDING = "SENDING"
STATUS_SEND_FAILED = "SEND_FAILED"
STATUS_FAILED = "FAILED"

DEFAULT_PRIORITY = {
    "switch_model": 100,
    "evolution_decision": 90,
    "smart_home": 80,
    "chat": 50,
    "job": 30,
}


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
                trace_id TEXT,
                chat_id INTEGER,
                message_id INTEGER,
                text TEXT,
                task_type TEXT,
                source TEXT,
                priority INTEGER,
                status TEXT,
                response TEXT,
                created_at REAL,
                updated_at REAL DEFAULT 0,
                next_retry_at REAL DEFAULT 0,
                last_error TEXT,
                process_retry_count INTEGER DEFAULT 0,
                send_retry_count INTEGER DEFAULT 0,
                first_started_at REAL,
                last_attempt_at REAL,
                last_send_at REAL,
                processing_started_at REAL,
                sending_started_at REAL,
                completed_at REAL,
                finished_reason TEXT
            )
        """)

        # 舊版 DB 自動補欄位
        _ensure_column(c, "tasks", "trace_id", "TEXT")
        _ensure_column(c, "tasks", "source", 'TEXT DEFAULT "telegram"')
        _ensure_column(c, "tasks", "priority", "INTEGER DEFAULT 50")
        _ensure_column(c, "tasks", "updated_at", "REAL DEFAULT 0")
        _ensure_column(c, "tasks", "next_retry_at", "REAL DEFAULT 0")
        _ensure_column(c, "tasks", "last_error", "TEXT")
        _ensure_column(c, "tasks", "process_retry_count", "INTEGER DEFAULT 0")
        _ensure_column(c, "tasks", "send_retry_count", "INTEGER DEFAULT 0")
        _ensure_column(c, "tasks", "first_started_at", "REAL")
        _ensure_column(c, "tasks", "last_attempt_at", "REAL")
        _ensure_column(c, "tasks", "last_send_at", "REAL")
        _ensure_column(c, "tasks", "processing_started_at", "REAL")
        _ensure_column(c, "tasks", "sending_started_at", "REAL")
        _ensure_column(c, "tasks", "completed_at", "REAL")
        _ensure_column(c, "tasks", "finished_reason", "TEXT")

        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_status_retry_priority_created
            ON tasks(status, next_retry_at, priority DESC, created_at ASC)
        """)
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_tasks_trace_id
            ON tasks(trace_id)
        """)

        c.execute("SELECT COUNT(*) FROM bot_state")
        if c.fetchone()[0] == 0:
            c.execute('INSERT INTO bot_state (id, status) VALUES (1, "IDLE")')

        # 啟動時修復中間狀態
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
            SET priority = COALESCE(priority, 50),
                process_retry_count = COALESCE(process_retry_count, 0),
                send_retry_count = COALESCE(send_retry_count, 0),
                source = COALESCE(source, 'telegram')
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


def _default_priority(task_type: str):
    return DEFAULT_PRIORITY.get(task_type, 50)


def add_task(chat_id, message_id, text, task_type="chat", source="telegram", priority=None, trace_id=None):
    now = time.time()
    trace_id = trace_id or str(uuid.uuid4())[:8]
    priority = _default_priority(task_type) if priority is None else int(priority)
    clean_text = (text or "").strip()

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO tasks (
                trace_id, chat_id, message_id, text, task_type, source, priority,
                status, response, created_at, updated_at, next_retry_at,
                last_error, process_retry_count, send_retry_count,
                first_started_at, last_attempt_at, last_send_at,
                processing_started_at, sending_started_at, completed_at, finished_reason
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trace_id,
            chat_id,
            message_id,
            clean_text,
            task_type,
            source,
            priority,
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
            None,
            None,
            None,
            None,
        ))
        task_id = c.lastrowid
        conn.commit()

    return {"id": task_id, "trace_id": trace_id}


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
            ORDER BY priority DESC, created_at ASC
            LIMIT 1
        """, (STATUS_PENDING, now))
        row = c.fetchone()

        if row is None:
            conn.commit()
            return None

        first_started_at = row["first_started_at"] or now

        c.execute("""
            UPDATE tasks
            SET status = ?,
                processing_started_at = ?,
                first_started_at = ?,
                last_attempt_at = ?,
                updated_at = ?
            WHERE id = ? AND status = ?
        """, (
            STATUS_PROCESSING,
            now,
            first_started_at,
            now,
            now,
            row["id"],
            STATUS_PENDING,
        ))

        if c.rowcount != 1:
            conn.commit()
            return None

        conn.commit()

        task = dict(row)
        task["status"] = STATUS_PROCESSING
        task["processing_started_at"] = now
        task["first_started_at"] = first_started_at
        task["last_attempt_at"] = now
        task["updated_at"] = now
        return task

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_next_pending_task():
    # 舊介面保留
    return claim_next_pending_task()


def mark_task_processing(task_id):
    now = time.time()
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE tasks
            SET status = ?, processing_started_at = ?, last_attempt_at = ?, updated_at = ?
            WHERE id = ?
        """, (STATUS_PROCESSING, now, now, now, task_id))
        conn.commit()


def mark_task_completed(task_id, response, error=None, finished_reason="completed"):
    now = time.time()
    response_text = response if isinstance(response, str) and response.strip() else "⚠️ 任務已完成，但沒有可回覆的內容。"

    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE tasks
            SET status = ?,
                response = ?,
                last_error = ?,
                finished_reason = ?,
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
            finished_reason,
            now,
            now,
            now,
            task_id,
        ))
        conn.commit()


def mark_task_failed(task_id, error, finished_reason="failed"):
    now = time.time()
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE tasks
            SET status = ?,
                last_error = ?,
                finished_reason = ?,
                updated_at = ?,
                next_retry_at = NULL,
                processing_started_at = NULL,
                sending_started_at = NULL
            WHERE id = ?
        """, (
            STATUS_FAILED,
            str(error),
            finished_reason,
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
            ORDER BY completed_at ASC, created_at ASC
            LIMIT 1
        """, (STATUS_COMPLETED, STATUS_SEND_FAILED, now))
        row = c.fetchone()

        if row is None:
            conn.commit()
            return None

        c.execute("""
            UPDATE tasks
            SET status = ?, sending_started_at = ?, last_send_at = ?, updated_at = ?
            WHERE id = ? AND status IN (?, ?)
        """, (
            STATUS_SENDING,
            now,
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
        task["last_send_at"] = now
        task["updated_at"] = now
        return task

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def mark_send_failed(task_id, error, delay_seconds=10, permanent=False, increment_retry=True):
    now = time.time()

    with get_conn() as conn:
        c = conn.cursor()

        if permanent:
            c.execute("""
                UPDATE tasks
                SET status = ?,
                    last_error = ?,
                    finished_reason = ?,
                    updated_at = ?,
                    sending_started_at = NULL,
                    next_retry_at = NULL
                WHERE id = ?
            """, (
                STATUS_FAILED,
                str(error),
                "send_failed_permanent",
                now,
                task_id,
            ))
        else:
            sql = """
                UPDATE tasks
                SET status = ?,
                    last_error = ?,
                    finished_reason = ?,
                    updated_at = ?,
                    next_retry_at = ?,
                    sending_started_at = NULL
            """
            params = [
                STATUS_SEND_FAILED,
                str(error),
                "send_retry_pending",
                now,
                now + max(0, int(delay_seconds)),
            ]

            if increment_retry:
                sql += ", send_retry_count = COALESCE(send_retry_count, 0) + 1"

            sql += " WHERE id = ?"
            params.append(task_id)

            c.execute(sql, tuple(params))

        conn.commit()


def get_completed_tasks():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT *
            FROM tasks
            WHERE status = ?
            ORDER BY completed_at ASC, created_at ASC
        """, (STATUS_COMPLETED,))
        return [dict(row) for row in c.fetchall()]


def get_failed_tasks(limit=20):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT *
            FROM tasks
            WHERE status = ?
            ORDER BY updated_at DESC
            LIMIT ?
        """, (STATUS_FAILED, limit))
        return [dict(row) for row in c.fetchall()]


def get_queue_stats():
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT status, COUNT(*) AS cnt
            FROM tasks
            GROUP BY status
        """)
        rows = c.fetchall()
        stats = {row["status"]: row["cnt"] for row in rows}
        stats["state"] = get_state()
        return stats


def delete_task(task_id):
    with get_conn() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()


init_db()