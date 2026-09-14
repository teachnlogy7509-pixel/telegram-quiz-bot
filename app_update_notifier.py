"""Announce new RATHOD HUB APK builds to a configured Telegram group."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
from urllib import request

logger = logging.getLogger(__name__)
REPO = "teachnlogy7509-pixel/RATHOD-HUB"
CHECK_SECONDS = 120
STATE_FILE = Path(".rathod_last_release_sha")
_task = None


def target_chat_id() -> int | None:
    raw = (os.environ.get("APP_UPDATE_CHAT_ID") or "").strip()
    try:
        return int(raw) if raw else None
    except ValueError:
        logger.error("APP_UPDATE_CHAT_ID must be a numeric Telegram chat ID")
        return None


def _json(url: str):
    req = request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "RATHOD-HUB-Telegram-Notifier"})
    with request.urlopen(req, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _latest_release_commit() -> dict | None:
    rows = _json(f"https://api.github.com/repos/{REPO}/commits?path=releases&per_page=1")
    if not rows:
        return None
    row = rows[0]
    sha = row.get("sha") or ""
    detail = _json(f"https://api.github.com/repos/{REPO}/commits/{sha}")
    apk = next((f for f in detail.get("files", []) if str(f.get("filename", "")).lower().endswith(".apk")), None)
    if not apk:
        return None
    path = apk["filename"]
    return {
        "sha": sha,
        "message": str(row.get("commit", {}).get("message") or "RATHOD HUB update").splitlines()[0],
        "path": path,
        "download": f"https://raw.githubusercontent.com/{REPO}/main/{path}",
        "commit": row.get("html_url") or f"https://github.com/{REPO}/commit/{sha}",
    }


def _read_state() -> str:
    try:
        return STATE_FILE.read_text().strip()
    except Exception:
        return ""


def _write_state(sha: str):
    try:
        STATE_FILE.write_text(sha)
    except Exception as exc:
        logger.warning("Update notifier state write failed: %s", exc)


def message(info: dict, test: bool = False) -> str:
    title = "🧪 RATHOD HUB Notification Test" if test else "🚀 RATHOD HUB NEW UPDATE"
    return (
        f"{title}\n\n"
        f"✅ {info.get('message', 'New APK available')}\n"
        f"📦 {Path(info.get('path', 'RATHOD-HUB.apk')).name}\n\n"
        f"📥 Download APK:\n{info.get('download')}\n\n"
        f"🔗 Update details:\n{info.get('commit')}"
    )


async def check_once(bot, *, force: bool = False, test: bool = False) -> bool:
    chat_id = target_chat_id()
    if chat_id is None:
        return False
    info = await asyncio.to_thread(_latest_release_commit)
    if not info:
        return False
    previous = _read_state()
    if not force and not previous:
        _write_state(info["sha"])
        logger.info("Update notifier baseline set to %s", info["sha"][:8])
        return False
    if not force and previous == info["sha"]:
        return False
    await bot.send_message(chat_id=chat_id, text=message(info, test=test), disable_web_page_preview=False)
    _write_state(info["sha"])
    return True


async def _loop(application):
    while True:
        try:
            await check_once(application.bot)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("App update check failed: %s", exc)
        await asyncio.sleep(CHECK_SECONDS)


def init(application):
    global _task
    if target_chat_id() is None:
        logger.warning("App update notifier disabled: APP_UPDATE_CHAT_ID is missing")
        return
    if _task is None or _task.done():
        _task = asyncio.create_task(_loop(application), name="rathod-app-update-notifier")
        logger.info("App update notifier active for chat %s", target_chat_id())
