"""Read Telegram quiz scoreboards from Supabase so Railway redeploys cannot reset them."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from urllib import error, parse, request

import config

logger = logging.getLogger(__name__)
_INSTALLED = False


def _configured() -> bool:
    return bool((getattr(config, "SUPABASE_URL", "") or "").strip() and (getattr(config, "SUPABASE_SERVICE_ROLE_KEY", "") or "").strip())


def _get(params: dict) -> list[dict] | None:
    if not _configured():
        return None
    base = str(config.SUPABASE_URL).rstrip("/")
    key = str(config.SUPABASE_SERVICE_ROLE_KEY)
    url = f"{base}/rest/v1/telegram_quiz_scores?{parse.urlencode(params, safe='.,:*()-')}"
    req = request.Request(url, headers={"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/json"})
    try:
        with request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8") or "[]")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        logger.warning("Persistent score read failed (%s): %s", exc.code, detail)
    except Exception as exc:
        logger.warning("Persistent score read failed: %s", exc)
    return None


def _shape(row: dict) -> dict:
    correct = int(row.get("correct_count") or 0)
    wrong = int(row.get("wrong_count") or 0)
    answers = int(row.get("answer_count") or correct + wrong)
    score = int(row.get("total_xp") or 0)
    return {
        "user_id": int(row.get("telegram_user_id") or 0),
        "chat_id": int(row.get("last_chat_id") or 0),
        "username": row.get("telegram_username") or "",
        "name": row.get("telegram_name") or row.get("telegram_username") or "Telegram User",
        "xp": score,
        "total_score": score,
        "correct": correct,
        "wrong": wrong,
        "unanswered": max(0, answers - correct - wrong),
        "total_quizzes": 0,
        "best_score": score,
        "last_quiz_score": score,
        "streak": 0,
        "last_active": row.get("last_answered_at") or row.get("updated_at"),
    }


def _leaderboard(chat_id: int, limit: int = 10) -> list[dict] | None:
    rows = _get({"select": "*", "last_chat_id": f"eq.{int(chat_id)}", "order": "total_xp.desc", "limit": str(int(limit))})
    return None if rows is None else [_shape(x) for x in rows]


def _user(user_id: int, chat_id: int) -> dict | None:
    rows = _get({"select": "*", "telegram_user_id": f"eq.{int(user_id)}", "limit": "1"})
    if rows is None:
        return None
    return _shape(rows[0]) if rows else {}


def _rank(user_id: int, chat_id: int) -> int | None:
    rows = _get({"select": "telegram_user_id,total_xp", "last_chat_id": f"eq.{int(chat_id)}", "order": "total_xp.desc", "limit": "2000"})
    if rows is None:
        return None
    for index, row in enumerate(rows, 1):
        if int(row.get("telegram_user_id") or 0) == int(user_id):
            return index
    return max(1, len(rows) + 1)


def _today(chat_id: int, limit: int = 10) -> list[dict] | None:
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    rows = _get({"select": "*", "last_chat_id": f"eq.{int(chat_id)}", "last_answered_at": f"gte.{start}", "order": "total_xp.desc", "limit": str(int(limit))})
    if rows is None:
        return None
    shaped = [_shape(x) for x in rows]
    for row in shaped:
        row["score"] = row["total_score"]
    return shaped


def install(db_module, leaderboard_module, quiz_module):
    """Prefer Supabase reads; retain SQLite as an offline fallback."""
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True
    local_leaderboard = db_module.get_leaderboard
    local_user = db_module.get_user
    local_rank = db_module.get_rank
    local_today = db_module.get_today_top

    def get_leaderboard(chat_id: int, limit: int = 10):
        cloud = _leaderboard(chat_id, limit)
        return local_leaderboard(chat_id, limit) if cloud is None else cloud

    def get_user(user_id: int, chat_id: int):
        cloud = _user(user_id, chat_id)
        if cloud is None:
            return local_user(user_id, chat_id)
        return cloud or local_user(user_id, chat_id)

    def get_rank(user_id: int, chat_id: int):
        cloud = _rank(user_id, chat_id)
        return local_rank(user_id, chat_id) if cloud is None else cloud

    def get_today_top(chat_id: int, limit: int = 10):
        cloud = _today(chat_id, limit)
        return local_today(chat_id, limit) if cloud is None else cloud

    db_module.get_leaderboard = get_leaderboard
    db_module.get_user = get_user
    db_module.get_rank = get_rank
    db_module.get_today_top = get_today_top
    # leaderboard.py imported these functions by name, so replace its references too.
    leaderboard_module.get_leaderboard = get_leaderboard
    leaderboard_module.get_user = get_user
    leaderboard_module.get_rank = get_rank
    leaderboard_module.get_today_top = get_today_top
    # Quiz result cards ask quiz.py for rank through its imported reference.
    quiz_module.get_rank = get_rank
    logger.info("Supabase persistent Telegram score reader installed (configured=%s)", _configured())
