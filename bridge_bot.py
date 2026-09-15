"""RATHOD HUB VIP Bridge Bot.

This bot does not create quizzes. It reads public-safe app events and the
existing Telegram score tables, then sends delayed, friendly group updates.
It also supports /ask and private/mentioned chat using OpenRouter -> Gemini ->
local offline replies. Run as a separate Railway service with:
    python bridge_bot.py
"""
from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import random
import time
from datetime import datetime, timedelta, timezone
from urllib import error, parse, request

from telegram import BotCommand, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("rathod-vip-bridge")

BOT_NAME = "RATHOD SAKHI"
BOT_BYLINE = "Mujhe RATHOD HUB ke developer ne banaya hai 💙"
POLL_SECONDS = max(30, int(os.environ.get("BRIDGE_POLL_SECONDS", "60")))
SCORE_DELAY_MINUTES = max(30, int(os.environ.get("BRIDGE_SCORE_DELAY_MINUTES", "30")))
MOTIVATION_MINUTES = max(60, int(os.environ.get("BRIDGE_MOTIVATION_MINUTES", "180")))
SUPABASE_URL = (os.environ.get("SUPABASE_URL") or "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or ""
BOT_TOKEN = os.environ.get("BRIDGE_TELEGRAM_BOT_TOKEN") or ""
GROUP_CHAT_ID = (os.environ.get("BRIDGE_GROUP_CHAT_ID") or os.environ.get("APP_UPDATE_CHAT_ID") or "").strip()

OPENROUTER_KEYS = [x for x in [os.environ.get("OPENROUTER_API_KEY"), os.environ.get("OPENROUTER_API_KEY_2")] if x]
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/auto")
GEMINI_KEYS = [x for x in [os.environ.get("GEMINI_API_KEY"), os.environ.get("GEMINI_API_KEY_2")] if x]
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

MOTIVATION_LINES = [
    "📚 Aaj ka study page thoda khula hai, par story abhi baaki hai 😄 20 minute focus kar lo—motivation khud aa jayegi 💙✨",
    "🌱 Chhoti progress bhi progress hoti hai. Ek chapter, ek quiz, ek step—RATHOD family aapke saath hai 💪📖",
    "☕ Thoda paani, thoda focus aur ek honest attempt—bas itna hi aaj ke champion ko chahiye 🔥",
    "🌙 Sapne bade hain to aaj ka ek focused session unhe aur paas le aayega. You can do it, aspirant 👑",
    "🧬 Biology ka ek concept, Physics ka ek formula ya Chemistry ka ek reaction—daily consistency hi superpower hai ✨",
    "💙 Main yahin hoon aapko gently yaad dilane ke liye: perfect hona zaroori nahi, aaj kal se thoda better hona zaroori hai 📚",
    "🌸 Padhai ko punishment nahi, apne future self ke liye ek pyara sa gift samjho. Chalo 15 minute start karte hain 😊",
    "🏹 RATHOD warriors, leaderboard se pehle apni consistency jeeto. Rank baad me khud follow karegi 🔥🏆",
]
_last_motivation = 0.0
_last_line = ""
_score_baseline: dict[str, int] | None = None
_score_changed_at: float | None = None


def _headers() -> dict[str, str]:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _rest(method: str, path: str, params: dict[str, str] | None = None, body: object | None = None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing")
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if params:
        url += "?" + parse.urlencode(params)
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = request.Request(url, data=data, headers=_headers(), method=method)
    with request.urlopen(req, timeout=20) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else None


def _http_json(url: str, body: dict, headers: dict[str, str] | None = None) -> dict:
    req_headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req_headers.update(headers or {})
    req = request.Request(url, data=json.dumps(body).encode("utf-8"), headers=req_headers, method="POST")
    with request.urlopen(req, timeout=25) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _ai_system() -> str:
    return (
        "You are RATHOD SAKHI, a warm and respectful female study companion for RATHOD HUB. "
        "Reply in the user's language: Hindi, Hinglish, or English. Use feminine Hindi wording "
        "naturally, such as 'main samjha dungi', 'main help karungi', and 'main yaad dilati rahungi'. "
        "Be friendly, concise, encouraging, and use a few tasteful emojis. Teach NEET Biology, "
        "Physics, Chemistry, study planning, app navigation, XP, quizzes and focus habits. "
        "Never invent live scores or private user data. If asked who made you, say: 'Mujhe RATHOD HUB ke developer ne banaya hai.' "
        "Do not claim to be a human or a real romantic partner. Keep group replies short and useful."
    )


def _openrouter(prompt: str, key: str) -> str:
    result = _http_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "system", "content": _ai_system()}, {"role": "user", "content": prompt}],
            "temperature": 0.75,
            "max_tokens": 450,
        },
        {"Authorization": f"Bearer {key}", "HTTP-Referer": "https://teachnlogy7509-pixel.github.io/RATHOD-HUB/", "X-Title": "RATHOD SAKHI"},
    )
    return str(((result.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()


def _gemini(prompt: str, key: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{parse.quote(GEMINI_MODEL)}:generateContent?key={parse.quote(key)}"
    result = _http_json(
        url,
        {"system_instruction": {"parts": [{"text": _ai_system()}]}, "contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.75, "maxOutputTokens": 450}},
    )
    parts = (((result.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
    return "".join(str(part.get("text") or "") for part in parts).strip()


def _offline_reply(prompt: str) -> str:
    low = prompt.lower()
    if any(x in low for x in ["who made", "kisne banaya", "developer", "banaya"]):
        return "Mujhe RATHOD HUB ke developer ne banaya hai 💙 Main RATHOD HUB ki friendly study companion hoon."
    if any(x in low for x in ["motivation", "mann nahi", "padhne ka mann", "demotivat"]):
        return "Koi baat nahi, main hoon na 😊 Bas 15 minute ka small target rakho. Chhoti consistency hi bade result banati hai 📚✨"
    if any(x in low for x in ["plan", "schedule", "routine"]):
        return "Offline mode me simple plan: 25 min focused study, 5 min break, phir 10 MCQs. Start chhota rakho—main aapko motivate karti rahungi 💙"
    return "Abhi online AI connection thoda unavailable hai, lekin main yahin hoon 💙 15 minute ka focused study session start kar do; internet aate hi main detail me help kar dungi."


async def _ask_ai(prompt: str) -> str:
    question = str(prompt or "").strip()[:1800]
    for key in OPENROUTER_KEYS:
        try:
            answer = await asyncio.to_thread(_openrouter, question, key)
            if answer:
                return answer
        except Exception as exc:
            logger.warning("OpenRouter fallback: %s", str(exc)[:160])
    for key in GEMINI_KEYS:
        try:
            answer = await asyncio.to_thread(_gemini, question, key)
            if answer:
                return answer
        except Exception as exc:
            logger.warning("Gemini fallback: %s", str(exc)[:160])
    return _offline_reply(question)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_name(value: object) -> str:
    text = str(value or "RATHOD Aspirant").strip()
    return text[:60] or "RATHOD Aspirant"


def _group_id(update: Update | None = None) -> int | None:
    raw = str(getattr(update.effective_chat, "id", "") if update and update.effective_chat else GROUP_CHAT_ID).strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


async def _send(text: str, bot, chat_id: int | None = None) -> bool:
    target = chat_id or _group_id()
    if target is None:
        logger.warning("No BRIDGE_GROUP_CHAT_ID or APP_UPDATE_CHAT_ID configured")
        return False
    try:
        await bot.send_message(chat_id=target, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        return True
    except Exception:
        logger.exception("Bridge message failed")
        return False


def _fetch_pending(mode: str, cutoff: datetime | None = None) -> list[dict]:
    params = {"select": "id,event_type,delivery_mode,user_id,display_name,payload,created_at", "delivery_mode": f"eq.{mode}", "delivered_at": "is.null", "order": "created_at.asc", "limit": "200"}
    if cutoff:
        params["created_at"] = f"lt.{cutoff.isoformat()}"
    return _rest("GET", "rh_bridge_events", params) or []


def _fetch_scores() -> list[dict]:
    return _rest("GET", "telegram_quiz_scores", {"select": "telegram_user_id,telegram_name,total_xp,updated_at", "order": "total_xp.desc", "limit": "50"}) or []


def _mark(ids: list[int], label: str) -> None:
    if not ids:
        return
    _rest("PATCH", "rh_bridge_events", {"id": "in.(" + ",".join(str(int(x)) for x in ids) + ")"}, {"delivered_at": _now().isoformat(), "delivered_by": label[:80]})


def _event_payload(row: dict) -> dict:
    value = row.get("payload") or {}
    return value if isinstance(value, dict) else {}


def _digest(rows: list[dict]) -> str:
    total = len(rows)
    correct = sum(1 for r in rows if bool(_event_payload(r).get("is_correct")))
    xp = sum(int(_event_payload(r).get("xp_delta", 0) or 0) for r in rows)
    users: dict[str, int] = {}
    modes: dict[str, int] = {}
    for row in rows:
        name = _safe_name(row.get("display_name")); users[name] = users.get(name, 0) + 1
        mode = str(_event_payload(row).get("mode") or "Study Practice"); modes[mode] = modes.get(mode, 0) + 1
    top = sorted(users.items(), key=lambda item: (-item[1], item[0]))[:5]
    mode_text = " • ".join(f"{html.escape(k)}: {v}" for k, v in sorted(modes.items()))
    top_text = "\n".join(f"{i}. {html.escape(name)} — {count} solved" for i, (name, count) in enumerate(top, 1))
    return ("⏰ <b>RATHOD Study Update</b>\n\n" f"📚 Last {SCORE_DELAY_MINUTES} min me <b>{total}</b> questions solve hue\n" f"✅ Correct attempts: <b>{correct}</b>\n" f"⚡ XP recorded: <b>+{xp}</b>\n" f"🎯 Modes: {mode_text or 'Study Practice'}\n\n" f"<b>Active learners</b>\n{top_text or 'Aaj ki pehli study entry ka wait hai 😊'}\n\n" "Keep going, champions—small steps bhi NEET dream ke paas le jaate hain 💙📖")


def _score_signature(rows: list[dict]) -> dict[str, int]:
    return {str(row.get("telegram_user_id")): int(row.get("total_xp", 0) or 0) for row in rows if row.get("telegram_user_id") is not None}


def _score_message(rows: list[dict]) -> str:
    lines = []
    for index, row in enumerate(rows[:5], 1):
        medal = ["🥇", "🥈", "🥉"][index - 1] if index <= 3 else f"{index}."
        name = html.escape(_safe_name(row.get("telegram_name") or f"Aspirant {row.get('telegram_user_id')}"))
        lines.append(f"{medal} {name} — <b>{int(row.get('total_xp', 0) or 0)} XP</b>")
    return (f"🎯 <b>Telegram Quiz Score Update</b>\n\nLatest score ko approximately {SCORE_DELAY_MINUTES} minutes delay ke baad share kiya gaya hai ⏰\n\n" + ("\n".join(lines) if lines else "Abhi score board ready ho raha hai 😊") + "\n\n👏 Padhte raho, leaderboard kabhi bhi change ho sakta hai 🔥📚")


async def _process_score_digest(application: Application) -> None:
    global _score_baseline, _score_changed_at
    rows = await asyncio.to_thread(_fetch_scores); current = _score_signature(rows); now = time.time()
    if _score_baseline is None:
        _score_baseline = current; return
    if current != _score_baseline:
        if _score_changed_at is None: _score_changed_at = now
        if now - _score_changed_at >= SCORE_DELAY_MINUTES * 60:
            if await _send(_score_message(rows), application.bot): _score_baseline = current; _score_changed_at = None
    else:
        _score_changed_at = None


async def _process_events(application: Application) -> None:
    if not SUPABASE_URL or not SUPABASE_KEY or not GROUP_CHAT_ID:
        return
    immediate = await asyncio.to_thread(_fetch_pending, "immediate", None)
    for row in immediate[:20]:
        payload = _event_payload(row); title = str(payload.get("title") or "📢 RATHOD HUB Update"); body = str(payload.get("body") or "RATHOD HUB par nayi activity hui hai.")
        text = f"{html.escape(title)}\n\n{html.escape(body)}\n\n<i>— {BOT_NAME} 💙</i>"
        if await _send(text, application.bot): await asyncio.to_thread(_mark, [int(row["id"])], "immediate")
    cutoff = _now() - timedelta(minutes=SCORE_DELAY_MINUTES)
    digest_rows = await asyncio.to_thread(_fetch_pending, "digest", cutoff)
    if digest_rows:
        if await _send(_digest(digest_rows), application.bot): await asyncio.to_thread(_mark, [int(row["id"]) for row in digest_rows], "30-minute-digest")


async def _poll_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await _process_events(context.application)
        await _process_score_digest(context.application)
    except Exception:
        logger.exception("Bridge polling failed")


async def _motivation_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global _last_motivation, _last_line
    if time.time() - _last_motivation < MOTIVATION_MINUTES * 60: return
    choices = [line for line in MOTIVATION_LINES if line != _last_line] or MOTIVATION_LINES; line = random.choice(choices)
    if await _send(f"💌 <b>{BOT_NAME}</b> ki chhoti si reminder\n\n{html.escape(line)}\n\n<i>{BOT_BYLINE}</i>", context.application.bot): _last_line = line; _last_motivation = time.time()


async def _about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(f"👋 Namaste! Main <b>{BOT_NAME}</b> hoon—RATHOD HUB ki friendly female study companion.\n\n{BOT_BYLINE}\n\nMain quiz nahi banati; main app updates, score digest, winners aur motivation group tak laati hoon 📚✨", parse_mode=ParseMode.HTML)


async def _bridgehelp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("💙 <b>RATHOD SAKHI</b>\n\n• App updates\n• 30-minute score digest\n• NEET 720, Daily 9 PM aur Live Quiz activity\n• Winner/leaderboard messages\n• New member welcome\n• /ask se online AI ya offline fallback help\n\n" + BOT_BYLINE, parse_mode=ParseMode.HTML)


async def _ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = " ".join(context.args or []).strip()
    if not question:
        await update.effective_message.reply_text("Use: /ask apna sawal likhiye 💙")
        return
    wait = await update.effective_message.reply_text("💭 Sakhi soch rahi hoon…")
    answer = await _ask_ai(question)
    await wait.edit_text(html.escape(answer), parse_mode=ParseMode.HTML)


async def _chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text or message.text.startswith("/"):
        return
    if update.effective_chat and update.effective_chat.type == "private":
        question = message.text.strip()
    else:
        username = str(context.bot.username or "").lower()
        marker = f"@{username}" if username else ""
        if not marker or marker not in message.text.lower():
            return
        question = message.text.replace(marker, "").strip()
    if not question:
        await message.reply_text("Ji, poochhiye na 😊 Main help karungi.")
        return
    answer = await _ask_ai(question)
    await message.reply_text(html.escape(answer), parse_mode=ParseMode.HTML)


async def _welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.new_chat_members: return
    for member in update.message.new_chat_members[:8]:
        if member.is_bot: continue
        name = html.escape(member.first_name or "Aspirant")
        await _send(f"🎉 <b>Welcome {name}!</b>\n\nRATHOD HUB family me aapka bahut pyaara swagat hai 💙\nYahan daily quiz, NEET practice aur friendly study energy milegi 📚✨\n\n— RATHOD SAKHI 👋", context.bot, update.effective_chat.id)


async def _post_init(application: Application) -> None:
    existing = await application.bot.get_my_commands(); known = {item.command for item in existing}
    additions = [BotCommand("about", "Who made the VIP bridge bot"), BotCommand("bridgehelp", "Bridge bot features"), BotCommand("ask", "Ask RATHOD SAKHI")]
    await application.bot.set_my_commands(list(existing) + [x for x in additions if x.command not in known])
    if application.job_queue:
        application.job_queue.run_repeating(_poll_job, interval=POLL_SECONDS, first=8, name="rh-bridge-poll")
        application.job_queue.run_repeating(_motivation_job, interval=60, first=120, name="rh-bridge-motivation")


def main() -> None:
    if not BOT_TOKEN: raise SystemExit("BRIDGE_TELEGRAM_BOT_TOKEN is missing")
    if not SUPABASE_URL or not SUPABASE_KEY: raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    app = Application.builder().token(BOT_TOKEN).post_init(_post_init).build()
    app.add_handler(CommandHandler("about", _about))
    app.add_handler(CommandHandler("bridgehelp", _bridgehelp))
    app.add_handler(CommandHandler("ask", _ask_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, _welcome))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, _chat_message))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, _chat_message))
    logger.info("%s started; score delay=%sm; poll=%ss; OpenRouter=%s; Gemini=%s", BOT_NAME, SCORE_DELAY_MINUTES, POLL_SECONDS, bool(OPENROUTER_KEYS), bool(GEMINI_KEYS))
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
