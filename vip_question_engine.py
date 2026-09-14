"""VIP question diversity and persistent anti-repeat layer for RATHOD Telegram Bot."""
from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import re
import sqlite3
import time
import unicodedata
from difflib import SequenceMatcher

import config

logger = logging.getLogger(__name__)
_INSTALLED = False

QUESTION_TYPES = (
    "NCERT line/fact recall with a close distractor",
    "deep conceptual mechanism",
    "Statement I and Statement II",
    "Assertion–Reason",
    "multiple statements: choose the correct combination/count",
    "match-the-following converted into four option combinations",
    "correct biological/physical/chemical sequence or order",
    "identify the incorrect statement",
    "case/application based question",
    "numerical or data-interpretation question when the topic permits",
    "NEET PYQ-inspired conceptual trap without copying copyrighted wording",
    "diagram/graph described in words",
)


def _connect():
    conn = sqlite3.connect(getattr(config, "DB_PATH", "scores.db"), timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS vip_question_history (
            fingerprint TEXT PRIMARY KEY,
            topic_key TEXT NOT NULL,
            style TEXT NOT NULL,
            question TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_vip_history_topic ON vip_question_history(topic_key, created_at DESC)")
    conn.commit()
    return conn


def _normalise(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    value = re.sub(r"[^\w\s]", " ", value, flags=re.UNICODE)
    return re.sub(r"\s+", " ", value).strip()


def _fingerprint(question: str) -> str:
    return hashlib.sha256(_normalise(question).encode("utf-8")).hexdigest()


def _topic_key(topic: str) -> str:
    clean = _normalise(topic)
    return hashlib.sha1(clean[:300].encode("utf-8")).hexdigest()


def _recent(topic: str, limit: int = 350) -> list[str]:
    key = _topic_key(topic)
    with _connect() as conn:
        rows = conn.execute(
            "SELECT question FROM vip_question_history WHERE topic_key=? ORDER BY created_at DESC LIMIT ?",
            (key, limit),
        ).fetchall()
    return [str(row["question"]) for row in rows]


def _valid_question(q: dict) -> bool:
    if not isinstance(q, dict):
        return False
    question = str(q.get("question") or "").strip()
    options = q.get("options")
    if len(question) < 12 or not isinstance(options, list) or len(options) != 4:
        return False
    normal_options = [_normalise(x) for x in options]
    if any(not x for x in normal_options) or len(set(normal_options)) != 4:
        return False
    try:
        return int(q.get("correct_index")) in (0, 1, 2, 3)
    except (TypeError, ValueError):
        return False


def _too_similar(question: str, previous: list[str]) -> bool:
    candidate = _normalise(question)
    if not candidate:
        return True
    for old in previous:
        known = _normalise(old)
        if candidate == known:
            return True
        # Catch paraphrases that only change punctuation, order labels, or a few words.
        if min(len(candidate), len(known)) >= 35 and SequenceMatcher(None, candidate, known).ratio() >= 0.86:
            return True
    return False


def _save(topic: str, style: str, questions: list[dict]):
    now = int(time.time())
    key = _topic_key(topic)
    with _connect() as conn:
        conn.executemany(
            "INSERT OR IGNORE INTO vip_question_history(fingerprint,topic_key,style,question,created_at) VALUES(?,?,?,?,?)",
            [(_fingerprint(q["question"]), key, style, str(q["question"]), now) for q in questions],
        )
        # Keep storage bounded while retaining a large global anti-repeat memory.
        conn.execute("DELETE FROM vip_question_history WHERE fingerprint IN (SELECT fingerprint FROM vip_question_history ORDER BY created_at DESC LIMIT -1 OFFSET 25000)")
        conn.commit()


def _vip_topic(topic: str, count: int, attempt: int, exclusions: list[str]) -> str:
    modes = list(QUESTION_TYPES)
    random.SystemRandom().shuffle(modes)
    selected = modes[: min(len(modes), max(4, count))]
    avoid = "\n".join(f"- {x[:240]}" for x in exclusions[-24:]) or "- none yet"
    nonce = hashlib.sha1(f"{time.time_ns()}:{attempt}:{random.random()}".encode()).hexdigest()[:12]
    return f"""{topic}

RATHOD VIP QUESTION ENGINE — variant {nonce}, attempt {attempt + 1}.
Create fresh, exam-valid questions in Hindi/Hinglish unless the user explicitly requested English. Keep scientific terms accurate and NCERT-focused for NEET topics. Distribute this batch across these formats:
{chr(10).join(f'- {mode}' for mode in selected)}
Every question must test a different fact, mechanism, step, formula, exception, or application. Options must be distinct, plausible, grammatically parallel and have exactly one unambiguous correct answer. Vary the correct option position. Do not repeat or lightly paraphrase any avoided question.
AVOIDED PREVIOUS QUESTIONS:
{avoid}
""".strip()


def install(quiz_module):
    """Patch the existing generator without changing Telegram session/scoring code."""
    global _INSTALLED
    if _INSTALLED or getattr(quiz_module, "_vip_unique_installed", False):
        return
    _INSTALLED = True
    quiz_module._vip_unique_installed = True
    original_generate = quiz_module.generate_questions
    original_pdf = quiz_module.generate_questions_from_pdf

    async def generate_questions(topic: str, count: int, style: str = "quiz") -> list[dict]:
        previous = _recent(topic)
        accepted: list[dict] = []
        seen = list(previous)
        last_error = None
        for attempt in range(6):
            if len(accepted) >= count:
                break
            needed = count - len(accepted)
            request_count = min(10, max(needed, min(10, needed + 3)))
            prompt_topic = _vip_topic(topic, request_count, attempt, seen)
            try:
                batch = await original_generate(prompt_topic, request_count, style)
            except Exception as exc:
                last_error = exc
                logger.warning("VIP generation attempt %s failed: %s", attempt + 1, exc)
                await asyncio.sleep(min(1 + attempt, 4))
                continue
            for q in batch:
                if not _valid_question(q) or _too_similar(str(q.get("question", "")), seen):
                    continue
                clean = {
                    "question": str(q["question"]).strip(),
                    "options": [str(x).strip() for x in q["options"]],
                    "correct_index": int(q["correct_index"]),
                }
                accepted.append(clean)
                seen.append(clean["question"])
                if len(accepted) >= count:
                    break
        if len(accepted) < count:
            raise RuntimeError(f"VIP engine found only {len(accepted)}/{count} genuinely unique questions. Retry once. Last AI error: {last_error}")
        result = accepted[:count]
        _save(topic, style, result)
        return result

    async def generate_questions_from_pdf(pdf_bytes: bytes, pdf_name: str, count: int) -> list[dict]:
        topic = f"PDF:{pdf_name}"
        previous = _recent(topic)
        accepted: list[dict] = []
        seen = list(previous)
        last_error = None
        for attempt in range(5):
            if len(accepted) >= count:
                break
            needed = count - len(accepted)
            variant_name = f"{pdf_name} — VIP unique variant {attempt + 1}"
            try:
                batch = await original_pdf(pdf_bytes, variant_name, needed)
            except Exception as exc:
                last_error = exc
                continue
            for q in batch:
                if _valid_question(q) and not _too_similar(str(q.get("question", "")), seen):
                    clean = {"question": str(q["question"]).strip(), "options": [str(x).strip() for x in q["options"]], "correct_index": int(q["correct_index"])}
                    accepted.append(clean);seen.append(clean["question"])
                    if len(accepted) >= count:
                        break
        if len(accepted) < count:
            raise RuntimeError(f"PDF VIP engine found only {len(accepted)}/{count} unique questions. Last error: {last_error}")
        result = accepted[:count];_save(topic, "pdf", result);return result

    quiz_module.generate_questions = generate_questions
    quiz_module.generate_questions_from_pdf = generate_questions_from_pdf
    logger.info("RATHOD VIP unique question engine installed")
