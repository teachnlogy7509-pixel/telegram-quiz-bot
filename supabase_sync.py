"""Secure Supabase bridge for Telegram quiz scores."""
import json
import logging
from urllib import request, error
import config

logger = logging.getLogger(__name__)


def _rpc(name: str, payload: dict) -> dict:
    base = (getattr(config, "SUPABASE_URL", "") or "").rstrip("/")
    key = getattr(config, "SUPABASE_SERVICE_ROLE_KEY", "") or ""
    if not base or not key:
        return {"success": False, "error": "Supabase sync is not configured on Railway."}
    req = request.Request(
        f"{base}/rest/v1/rpc/{name}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=15) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {"success": True}
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        logger.error("Supabase RPC %s failed (%s): %s", name, exc.code, detail)
        return {
            "success": False,
            "error": f"Supabase HTTP {exc.code}",
            "detail": detail,
        }
    except Exception as exc:
        logger.exception("Supabase RPC %s failed", name)
        return {"success": False, "error": str(exc)[:250]}


def confirm_link(code: str, telegram_user_id: int, username: str, name: str) -> dict:
    return _rpc(
        "confirm_telegram_link",
        {
            "p_code": (code or "").strip().upper(),
            "p_telegram_user_id": int(telegram_user_id),
            "p_username": username or "",
            "p_name": name or "Telegram User",
        },
    )


def record_answer(telegram_user_id: int, chat_id: int, username: str, name: str, is_correct: bool, topic: str, correct_score: int = 20, wrong_score: int = -10) -> dict:
    # SCORE_RPC_COMPAT_V2
    # patch_bot compatibility marker: "p_is_correct": bool(is_correct), "p_topic": (topic or "Quiz")[:250], "p_correct_score": int(correct_score), "p_wrong_score": int(wrong_score)
    legacy_payload = {
        "p_telegram_user_id": int(telegram_user_id),
        "p_chat_id": int(chat_id),
        "p_username": username or "",
        "p_name": name or "Telegram User",
        "p_is_correct": bool(is_correct),
        "p_topic": (topic or "Quiz")[:250],
    }
    result = _rpc(
        "record_telegram_quiz_answer",
        {
            **legacy_payload,
            "p_correct_score": int(correct_score),
            "p_wrong_score": int(wrong_score),
        },
    )
    # The app's current SQL exposes the original 6-argument RPC. Fall back only
    # when PostgREST says the scoring-v2 overload is missing, avoiding duplicate XP.
    detail = f"{result.get('error', '')} {result.get('detail', '')}"
    if not result.get("success") and (
        "HTTP 404" in detail or "PGRST202" in detail
    ):
        logger.warning(
            "Scoring-v2 RPC unavailable; retrying legacy Telegram score RPC"
        )
        result = _rpc("record_telegram_quiz_answer", legacy_payload)
    if not result.get("success"):
        logger.error("Telegram score update failed: %s", result)
    return result


def grant_bonus_xp(
    target: str, amount: int, reason: str, admin_telegram_user_id: int
) -> dict:
    return _rpc(
        "admin_grant_bonus_xp",
        {
            "p_target": (target or "").strip(),
            "p_amount": int(amount),
            "p_reason": (reason or "").strip()[:300],
            "p_admin_telegram_user_id": int(admin_telegram_user_id),
        },
    )
