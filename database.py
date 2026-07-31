import sqlite3
import json
import logging
from datetime import datetime
from config import DB_PATH

logger = logging.getLogger(__name__)


def _create_users_table(c):
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id       INTEGER NOT NULL,
            chat_id       INTEGER NOT NULL DEFAULT 0,
            username      TEXT,
            name          TEXT,
            total_score   INTEGER DEFAULT 0,
            correct       INTEGER DEFAULT 0,
            wrong         INTEGER DEFAULT 0,
            unanswered    INTEGER DEFAULT 0,
            total_quizzes INTEGER DEFAULT 0,
            best_score    INTEGER DEFAULT 0,
            last_quiz_score INTEGER DEFAULT 0,
            last_activity   TEXT,
            quiz_history    TEXT DEFAULT '[]',
            PRIMARY KEY (user_id, chat_id)
        )
    ''')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # ── Migrate old single-PK users table → composite (user_id, chat_id) PK ──
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if c.fetchone():
        c.execute("PRAGMA table_info(users)")
        cols = [row[1] for row in c.fetchall()]
        if 'chat_id' not in cols:
            logger.info("Migrating users table to composite PK (user_id, chat_id)…")
            c.execute("ALTER TABLE users RENAME TO _users_v1")
            _create_users_table(c)
            # Carry old rows forward with chat_id = 0
            c.execute('''
                INSERT OR IGNORE INTO users
                    (user_id, chat_id, username, name,
                     total_score, correct, wrong, unanswered,
                     total_quizzes, best_score, last_quiz_score,
                     last_activity, quiz_history)
                SELECT user_id, 0, username, name,
                       total_score, correct, wrong, unanswered,
                       total_quizzes, best_score, last_quiz_score,
                       last_activity, quiz_history
                FROM _users_v1
            ''')
    else:
        _create_users_table(c)

    # ── quiz_results: one row per completed quiz, used for /toptoday ──────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS quiz_results (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            chat_id    INTEGER NOT NULL,
            username   TEXT,
            name       TEXT,
            correct    INTEGER DEFAULT 0,
            wrong      INTEGER DEFAULT 0,
            unanswered INTEGER DEFAULT 0,
            score      INTEGER DEFAULT 0,
            topic      TEXT,
            total      INTEGER DEFAULT 0,
            date       TEXT NOT NULL   -- UTC date YYYY-MM-DD
        )
    ''')
    c.execute('''
        CREATE INDEX IF NOT EXISTS idx_qr_chat_date
        ON quiz_results (chat_id, date)
    ''')

    # ── group_settings: per-group quiz timer ─────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS group_settings (
            chat_id       INTEGER PRIMARY KEY,
            timer_seconds INTEGER NOT NULL DEFAULT 30
        )
    ''')

    # ── schedules: daily automatic quiz per group ─────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            chat_id INTEGER PRIMARY KEY,
            topic   TEXT    NOT NULL,
            count   INTEGER NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1
        )
    ''')
    # ── PDF Storage ─────────────────────────────────────────────
    c.execute('''
        CREATE TABLE IF NOT EXISTS pdfs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            uploaded_by INTEGER,
            uploaded_at TEXT
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialised at %s", DB_PATH)


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_user(user_id: int, chat_id: int, username: str, name: str):
    """Insert user for this group if not exists; update name/username."""
    conn = _connect()
    try:
        conn.execute('''
            INSERT INTO users (user_id, chat_id, username, name, last_activity)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, chat_id) DO UPDATE SET
                username      = excluded.username,
                name          = excluded.name,
                last_activity = excluded.last_activity
        ''', (user_id, chat_id, username or "", name or "User",
              datetime.utcnow().isoformat()))
        conn.commit()
    finally:
        conn.close()


def save_quiz_result(user_id: int, chat_id: int, correct: int, wrong: int,
                     unanswered: int, score: int, topic: str, total: int):
    """Persist quiz result and update cumulative stats for this group."""
    conn = _connect()
    try:
        row = conn.execute(
            'SELECT * FROM users WHERE user_id = ? AND chat_id = ?',
            (user_id, chat_id)
        ).fetchone()
        if not row:
            return

        new_total_score   = row['total_score'] + score
        new_correct       = row['correct'] + correct
        new_wrong         = row['wrong'] + wrong
        new_unanswered    = row['unanswered'] + unanswered
        new_total_quizzes = row['total_quizzes'] + 1
        new_best          = max(row['best_score'], score)

        history = json.loads(row['quiz_history'] or '[]')
        history.append({
            'topic': topic,
            'total': total,
            'correct': correct,
            'wrong': wrong,
            'unanswered': unanswered,
            'score': score,
            'date': datetime.utcnow().isoformat()
        })
        history = history[-50:]

        conn.execute('''
            UPDATE users SET
                total_score   = ?,
                correct       = ?,
                wrong         = ?,
                unanswered    = ?,
                total_quizzes = ?,
                best_score    = ?,
                last_quiz_score = ?,
                last_activity   = ?,
                quiz_history    = ?
            WHERE user_id = ? AND chat_id = ?
        ''', (
            new_total_score, new_correct, new_wrong, new_unanswered,
            new_total_quizzes, new_best, score,
            datetime.utcnow().isoformat(), json.dumps(history),
            user_id, chat_id
        ))

        # Record individual quiz for today's-score queries
        today = datetime.utcnow().date().isoformat()
        conn.execute('''
            INSERT INTO quiz_results
                (user_id, chat_id, username, name, correct, wrong, unanswered,
                 score, topic, total, date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, chat_id, row['username'], row['name'],
              correct, wrong, unanswered, score, topic, total, today))

        conn.commit()
    finally:
        conn.close()


def get_user(user_id: int, chat_id: int):
    conn = _connect()
    try:
        return conn.execute(
            'SELECT * FROM users WHERE user_id = ? AND chat_id = ?',
            (user_id, chat_id)
        ).fetchone()
    finally:
        conn.close()


def get_leaderboard(chat_id: int, limit: int = 10):
    conn = _connect()
    try:
        rows = conn.execute('''
            SELECT user_id, name, username, total_score, correct, wrong,
                   unanswered, total_quizzes
            FROM users
            WHERE chat_id = ?
            ORDER BY total_score DESC
            LIMIT ?
        ''', (chat_id, limit)).fetchall()
        return rows
    finally:
        conn.close()


def get_rank(user_id: int, chat_id: int):
    """Return the 1-based rank of the user in this group by total_score."""
    conn = _connect()
    try:
        result = conn.execute('''
            SELECT COUNT(*) + 1 AS rank
            FROM users
            WHERE chat_id = ?
              AND total_score > (
                  SELECT COALESCE(total_score, 0) FROM users
                  WHERE user_id = ? AND chat_id = ?
              )
        ''', (chat_id, user_id, chat_id)).fetchone()
        return result['rank'] if result else 1
    finally:
        conn.close()


def reset_score(user_id: int, chat_id: int):
    """Reset all scores for this user in this group."""
    conn = _connect()
    try:
        conn.execute('''
            UPDATE users SET
                total_score   = 0,
                correct       = 0,
                wrong         = 0,
                unanswered    = 0,
                total_quizzes = 0,
                best_score    = 0,
                last_quiz_score = 0,
                quiz_history    = '[]'
            WHERE user_id = ? AND chat_id = ?
        ''', (user_id, chat_id))
        conn.execute(
            'DELETE FROM quiz_results WHERE user_id = ? AND chat_id = ?',
            (user_id, chat_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_group_timer(chat_id: int) -> int:
    """Return the quiz timer in seconds for this group (default 30)."""
    conn = _connect()
    try:
        row = conn.execute(
            'SELECT timer_seconds FROM group_settings WHERE chat_id = ?', (chat_id,)
        ).fetchone()
        return int(row['timer_seconds']) if row else 30
    finally:
        conn.close()


def set_group_timer(chat_id: int, seconds: int):
    conn = _connect()
    try:
        conn.execute('''
            INSERT INTO group_settings (chat_id, timer_seconds) VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET timer_seconds = excluded.timer_seconds
        ''', (chat_id, seconds))
        conn.commit()
    finally:
        conn.close()


def set_schedule(chat_id: int, topic: str, count: int):
    conn = _connect()
    try:
        conn.execute('''
            INSERT INTO schedules (chat_id, topic, count, enabled) VALUES (?, ?, ?, 1)
            ON CONFLICT(chat_id) DO UPDATE SET
                topic   = excluded.topic,
                count   = excluded.count,
                enabled = 1
        ''', (chat_id, topic, count))
        conn.commit()
    finally:
        conn.close()


def remove_schedule(chat_id: int):
    conn = _connect()
    try:
        conn.execute('DELETE FROM schedules WHERE chat_id = ?', (chat_id,))
        conn.commit()
    finally:
        conn.close()


def get_schedule(chat_id: int):
    conn = _connect()
    try:
        return conn.execute(
            'SELECT * FROM schedules WHERE chat_id = ? AND enabled = 1', (chat_id,)
        ).fetchone()
    finally:
        conn.close()


def get_all_schedules() -> list:
    conn = _connect()
    try:
        return conn.execute(
            'SELECT * FROM schedules WHERE enabled = 1'
        ).fetchall()
    finally:
        conn.close()


def get_today_stats(chat_id: int, limit: int = 10):
    """Return today's aggregated stats per user in this group, best score first."""
    today = datetime.utcnow().date().isoformat()
    conn = _connect()
    try:
        rows = conn.execute('''
            SELECT qr.user_id,
                   COALESCE(u.name,     qr.name)     AS name,
                   COALESCE(u.username, qr.username) AS username,
                   SUM(qr.correct)    AS correct,
                   SUM(qr.wrong)      AS wrong,
                   SUM(qr.unanswered) AS unanswered,
                   SUM(qr.score)      AS today_score,
                   COUNT(*)           AS quizzes
            FROM quiz_results qr
            LEFT JOIN users u
              ON u.user_id = qr.user_id AND u.chat_id = qr.chat_id
            WHERE qr.chat_id = ? AND qr.date = ?
            GROUP BY qr.user_id
            ORDER BY today_score DESC
            LIMIT ?
        ''', (chat_id, today, limit)).fetchall()
        return rows
    finally:
        conn.close()
# --- ADMIN PDF FILE MANAGER DATABASE CODE ---
import sqlite3
from datetime import datetime

# बोट स्टार्ट होने पर इसे कॉल करना होगा
def init_pdf_db():
    conn = sqlite3.connect('scores.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pdf_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            file_id TEXT,
            uploader_id INTEGER,
            upload_date TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_pdf(name, file_id, uploader_id):
    conn = sqlite3.connect('scores.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO pdf_files (name, file_id, uploader_id, upload_date) VALUES (?, ?, ?, ?)",
            (name.lower(), file_id, uploader_id, datetime.now())
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # नाम पहले से मौजूद है
    finally:
        conn.close()

def get_pdf(name):
    conn = sqlite3.connect('scores.db')
    cursor = conn.cursor()
    cursor.execute("SELECT file_id FROM pdf_files WHERE name = ?", (name.lower(),))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def list_pdfs():
    conn = sqlite3.connect('scores.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM pdf_files ORDER BY name")
    results = cursor.fetchall()
    conn.close()
    return [row[0] for row in results]
