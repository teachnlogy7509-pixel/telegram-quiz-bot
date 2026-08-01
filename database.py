"""
Database operations using SQLite for NEET SuperBot.
Supports multi-group isolation, scores, ranks, streaks, schedules, and PDFs.
"""
import sqlite3
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
DB_NAME = "bot_database.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table with group isolation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            chat_id INTEGER,
            username TEXT,
            name TEXT,
            xp INTEGER DEFAULT 0,
            total_score INTEGER DEFAULT 0,
            correct INTEGER DEFAULT 0,
            wrong INTEGER DEFAULT 0,
            unanswered INTEGER DEFAULT 0,
            total_quizzes INTEGER DEFAULT 0,
            best_score INTEGER DEFAULT 0,
            last_quiz_score INTEGER DEFAULT 0,
            streak INTEGER DEFAULT 0,
            last_active TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
    """)

    # Group settings (timers)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_settings (
            chat_id INTEGER PRIMARY KEY,
            timer INTEGER DEFAULT 30
        )
    """)

    # Schedules table for daily quizzes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            chat_id INTEGER PRIMARY KEY,
            topic TEXT,
            count INTEGER
        )
    """)

    # PDF storage table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdf_files (
            file_name TEXT PRIMARY KEY,
            file_id TEXT,
            uploader_id INTEGER
        )
    """)

    conn.commit()
    conn.close()
    logger.info("Database initialized successfully.")

def ensure_user(user_id: int, chat_id: int, username: str, name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, chat_id, username, name, last_active)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(user_id, chat_id) DO UPDATE SET
            username = excluded.username,
            name = excluded.name,
            last_active = datetime('now')
    """, (user_id, chat_id, username or "", name or "User"))
    conn.commit()
    conn.close()

def add_xp(user_id: int, chat_id: int, amount: int = 1):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET xp = xp + ? WHERE user_id = ? AND chat_id = ?
    """, (amount, user_id, chat_id))
    conn.commit()
    conn.close()

def save_quiz_result(user_id: int, chat_id: int, correct: int, wrong: int, unanswered: int, score: int, topic: str, total: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT total_score, best_score, correct, wrong, unanswered, total_quizzes, streak 
        FROM users WHERE user_id = ? AND chat_id = ?
    """, (user_id, chat_id))
    row = cursor.fetchone()
    
    if row:
        new_total_score = row["total_score"] + score
        new_correct = row["correct"] + correct
        new_wrong = row["wrong"] + wrong
        new_unanswered = row["unanswered"] + unanswered
        new_quizzes = row["total_quizzes"] + 1
        new_best = max(row["best_score"], score)
        new_streak = row["streak"] + 1 if score > 0 else 0
        
        cursor.execute("""
            UPDATE users SET 
                total_score = ?, correct = ?, wrong = ?, unanswered = ?, 
                total_quizzes = ?, best_score = ?, last_quiz_score = ?, streak = ?, last_active = datetime('now')
            WHERE user_id = ? AND chat_id = ?
        """, (new_total_score, new_correct, new_wrong, new_unanswered, new_quizzes, new_best, score, new_streak, user_id, chat_id))
    
    conn.commit()
    conn.close()

def get_leaderboard(chat_id: int, limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM users WHERE chat_id = ? 
        ORDER BY total_score DESC LIMIT ?
    """, (chat_id, limit))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_user(user_id: int, chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ? AND chat_id = ?", (user_id, chat_id))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_rank(user_id: int, chat_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) + 1 as rank FROM users 
        WHERE chat_id = ? AND total_score > (
            SELECT COALESCE(total_score, 0) FROM users WHERE user_id = ? AND chat_id = ?
        )
    """, (chat_id, user_id, chat_id))
    res = cursor.fetchone()
    conn.close()
    return res["rank"] if res else 1

def get_today_top(chat_id: int, limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *, last_quiz_score as score FROM users 
        WHERE chat_id = ? AND date(last_active) = date('now')
        ORDER BY last_quiz_score DESC LIMIT ?
    """, (chat_id, limit))
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_latest_group_for_user(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT chat_id FROM users WHERE user_id = ? AND chat_id < 0 
        ORDER BY last_active DESC LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row["chat_id"] if row else None

def set_group_timer(chat_id: int, timer: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO group_settings (chat_id, timer) VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET timer = excluded.timer
    """, (chat_id, timer))
    conn.commit()
    conn.close()

def get_group_timer(chat_id: int) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT timer FROM group_settings WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row["timer"] if row and row["timer"] else 30

# Scheduler Functions (Missing functions added here)
def get_all_schedules():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id, topic, count FROM schedules")
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def save_schedule(chat_id: int, topic: str, count: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO schedules (chat_id, topic, count) VALUES (?, ?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET topic = excluded.topic, count = excluded.count
    """, (chat_id, topic, count))
    conn.commit()
    conn.close()

def remove_schedule_db(chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()

# PDF Management Functions
def init_pdf_db():
    pass

def save_pdf(file_name: str, file_id: str, uploader_id: int) -> bool:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO pdf_files (file_name, file_id, uploader_id) VALUES (?, ?, ?)", (file_name, file_id, uploader_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def get_pdf(file_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_id FROM pdf_files WHERE file_name LIKE ?", (f"%{file_name}%",))
    row = cursor.fetchone()
    conn.close()
    return row["file_id"] if row else None

def list_pdfs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_name FROM pdf_files")
    rows = cursor.fetchall()
    conn.close()
    return [r["file_name"] for r in rows]

def reset_score(user_id: int, chat_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET total_score = 0, correct = 0, wrong = 0, unanswered = 0, total_quizzes = 0, best_score = 0, streak = 0
        WHERE user_id = ? AND chat_id = ?
    """, (user_id, chat_id))
    conn.commit()
    conn.close()
