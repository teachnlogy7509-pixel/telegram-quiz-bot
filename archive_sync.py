"""Write Telegram quiz questions to the shared archive event table."""
from __future__ import annotations

import json
import logging
import os
from urllib import error, request

log = logging.getLogger(__name__)


def record_questions(topic: str, mode: str, questions: list[dict]) -> int:
    """Make generated Telegram questions available to the PDF worker."""
    url = (os.getenv("SUPABASE_URL", "") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or ""
    if not url or not key or not questions:
        return 0

    topic_text = str(topic or "Quiz").strip()[:120]
    rows = []
    for question in questions:
        options = question.get("options") if isinstance(question, dict) else None
        text = str(question.get("question") or "").strip() if isinstance(question, dict) else ""
        if not text or not isinstance(options, list) or len(options) != 4:
            continue
        rows.append({
            "event_type": "quiz_question",
            "delivery_mode": "digest",
            "display_name": "Telegram Quiz",
            "payload": {
                "archive": True,
                "source": "telegram",
                "mode": str(mode or "Quiz"),
                "quiz_name": topic_text,
                "question": text,
                "options": [str(option) for option in options],
                "correct_index": question.get("correct_index"),
            },
        })

    if not rows:
        return 0

    req = request.Request(
        f"{url}/rest/v1/rh_bridge_events",
        data=json.dumps(rows, ensure_ascii=False).encode("utf-8"),
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=25):
            pass
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        log.warning("Question archive enqueue failed HTTP %s: %s", exc.code, detail)
        return 0
    except Exception as exc:
        log.warning("Question archive enqueue failed: %s", str(exc)[:300])
        return 0
    return len(rows)
