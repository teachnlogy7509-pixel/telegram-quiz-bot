"""RATHOD SAKHI VIP Bridge Bot.
Separate service start command: python bridge_bot.py
It announces app activity, delayed scores and answers /ask or mentions.
Online AI fallback order: OpenRouter -> Gemini -> Groq -> local offline reply.
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
from urllib import parse, request

from telegram import BotCommand, Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", level=logging.INFO)
logger = logging.getLogger("rathod-vip-bridge")

BOT_NAME = "RATHOD SAKHI"
BOT_BYLINE = "Mujhe RATHOD HUB ke developer ne banaya hai 💙"
BOT_TOKEN = os.environ.get("BRIDGE_TELEGRAM_BOT_TOKEN", "")
GROUP_CHAT_ID = (os.environ.get("BRIDGE_GROUP_CHAT_ID") or os.environ.get("APP_UPDATE_CHAT_ID") or "").strip()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
POLL_SECONDS = max(30, int(os.environ.get("BRIDGE_POLL_SECONDS", "60")))
SCORE_DELAY_MINUTES = max(30, int(os.environ.get("BRIDGE_SCORE_DELAY_MINUTES", "30")))
MOTIVATION_MINUTES = max(60, int(os.environ.get("BRIDGE_MOTIVATION_MINUTES", "180")))
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL", "openrouter/auto")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

MOTIVATION_LINES = [
    "📚 Aaj ka study page thoda khula hai, par story abhi baaki hai 😄 20 minute focus kar lo—motivation khud aa jayegi 💙✨",
    "🌱 Chhoti progress bhi progress hoti hai. Ek chapter, ek quiz, ek step—RATHOD family aapke saath hai 💪📖",
    "☕ Thoda paani, thoda focus aur ek honest attempt—bas itna hi aaj ke champion ko chahiye 🔥",
    "🌙 Sapne bade hain to aaj ka ek focused session unhe aur paas le aayega. You can do it, aspirant 👑",
    "🧬 Biology ka ek concept, Physics ka ek formula ya Chemistry ka ek reaction—daily consistency hi superpower hai ✨",
    "💙 Main yahin hoon aapko gently yaad dilane ke liye: perfect hona zaroori nahi, aaj kal se thoda better hona zaroori hai 📚",
    "🌸 Padhai ko punishment nahi, future self ke liye ek pyara gift samjho. Chalo 15 minute start karte hain 😊",
    "🏹 RATHOD warriors, leaderboard se pehle apni consistency jeeto. Rank baad me khud follow karegi 🔥🏆",
]
last_motivation = 0.0
last_line = ""
score_baseline: dict[str, int] | None = None
score_changed_at: float | None = None


def _rest(method: str, path: str, params: dict[str, str] | None = None, body: object | None = None):
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing")
    url = f"{SUPABASE_URL}/rest/v1/{path}"
    if params:
        url += "?" + parse.urlencode(params)
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}", "Content-Type": "application/json", "Accept": "application/json"}
    data = None if body is None else json.dumps(body).encode("utf-8")
    with request.urlopen(request.Request(url, data=data, headers=headers, method=method), timeout=20) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else None


def _post_json(url: str, body: dict, headers: dict[str, str] | None = None) -> dict:
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    h.update(headers or {})
    req = request.Request(url, data=json.dumps(body).encode("utf-8"), headers=h, method="POST")
    with request.urlopen(req, timeout=25) as response:
        raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def _ai_system() -> str:
    return ("You are RATHOD SAKHI, a warm and respectful female study companion for RATHOD HUB. "
            "Reply in Hindi, Hinglish, or English according to the user. Use feminine wording naturally, "
            "such as 'main samjha dungi' and 'main help karungi'. Be friendly, concise, encouraging, and "
            "use a few tasteful emojis. Teach NEET subjects, app navigation, study planning and focus. "
            "Never invent live scores or private data. If asked who made you, say: 'Mujhe RATHOD HUB ke developer ne banaya hai.' "
            "Do not claim to be human or a real romantic partner.")


def _messages(prompt: str) -> list[dict[str, str]]:
    return [{"role": "system", "content": _ai_system()}, {"role": "user", "content": prompt}]


def _openrouter(prompt: str) -> str:
    data = _post_json("https://openrouter.ai/api/v1/chat/completions", {
        "model": OPENROUTER_MODEL, "messages": _messages(prompt), "temperature": 0.75, "max_tokens": 450,
    }, {"Authorization": f"Bearer {OPENROUTER_KEY}", "HTTP-Referer": "https://teachnlogy7509-pixel.github.io/RATHOD-HUB/", "X-Title": "RATHOD SAKHI"})
    return str(((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()


def _gemini(prompt: str) -> str:
    model = parse.quote(GEMINI_MODEL, safe="")
    secret = parse.quote(GEMINI_KEY, safe="")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={secret}"
    data = _post_json(url, {
        "system_instruction": {"parts": [{"text": _ai_system()}]},
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.75, "maxOutputTokens": 450},
    })
    parts = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
    return "".join(str(part.get("text") or "") for part in parts).strip()


def _groq(prompt: str) -> str:
    data = _post_json("https://api.groq.com/openai/v1/chat/completions", {
        "model": GROQ_MODEL, "messages": _messages(prompt), "temperature": 0.75, "max_tokens": 450,
    }, {"Authorization": f"Bearer {GROQ_KEY}"})
    return str(((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()


def _offline_reply(prompt: str) -> str:
    low = prompt.lower()
    if any(x in low for x in ("who made", "kisne banaya", "developer", "banaya")):
        return "Mujhe RATHOD HUB ke developer ne banaya hai 💙 Main RATHOD HUB ki friendly study companion hoon."
    if any(x in low for x in ("motivation", "mann nahi", "padhne ka mann", "demotivat")):
        return "Koi baat nahi, main hoon na 😊 Bas 15 minute ka small target rakho. Chhoti consistency hi bade result banati hai 📚✨"
    if any(x in low for x in ("plan", "schedule", "routine")):
        return "Offline mode me simple plan: 25 min focused study, 5 min break, phir 10 MCQs. Start chhota rakho—main aapko motivate karti rahungi 💙"
    return "Abhi online AI connection unavailable hai, lekin main yahin hoon 💙 15 minute ka focused session start kar do; internet aate hi main detail me help kar dungi."


async def ask_ai(prompt: str) -> str:
    question = str(prompt or "").strip()[:1800]
    providers = []
    if OPENROUTER_KEY: providers.append(("OpenRouter", lambda: _openrouter(question)))
    if GEMINI_KEY: providers.append(("Gemini", lambda: _gemini(question)))
    if GROQ_KEY: providers.append(("Groq", lambda: _groq(question)))
    for name, provider in providers:
        try:
            answer = await asyncio.to_thread(provider)
            if answer:
                return answer
        except Exception as exc:
            logger.warning("%s fallback: %s", name, str(exc)[:160])
    return _offline_reply(question)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_name(value: object) -> str:
    return (str(value or "RATHOD Aspirant").strip()[:60] or "RATHOD Aspirant")


def _target(update: Update | None = None) -> int | None:
    raw = str(getattr(update.effective_chat, "id", "") if update and update.effective_chat else GROUP_CHAT_ID).strip()
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


async def send_text(text: str, bot, chat_id: int | None = None) -> bool:
    target = chat_id or _target()
    if target is None:
        logger.warning("No BRIDGE_GROUP_CHAT_ID or APP_UPDATE_CHAT_ID configured")
        return False
    try:
        await bot.send_message(chat_id=target, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        return True
    except Exception:
        logger.exception("Bridge message failed")
        return False


def _pending(mode: str, cutoff: datetime | None = None) -> list[dict]:
    params = {"select": "id,event_type,delivery_mode,display_name,payload,created_at", "delivery_mode": f"eq.{mode}", "delivered_at": "is.null", "order": "created_at.asc", "limit": "200"}
    if cutoff:
        params["created_at"] = f"lt.{cutoff.isoformat()}"
    return _rest("GET", "rh_bridge_events", params) or []


def _scores() -> list[dict]:
    return _rest("GET", "telegram_quiz_scores", {"select": "telegram_user_id,telegram_name,total_xp,updated_at", "order": "total_xp.desc", "limit": "50"}) or []


def _mark(ids: list[int], label: str) -> None:
    if ids:
        _rest("PATCH", "rh_bridge_events", {"id": "in.(" + ",".join(str(int(x)) for x in ids) + ")"}, {"delivered_at": _now().isoformat(), "delivered_by": label[:80]})


def _payload(row: dict) -> dict:
    return row.get("payload") if isinstance(row.get("payload"), dict) else {}


def _event_digest(rows: list[dict]) -> str:
    users: dict[str, int] = {}; modes: dict[str, int] = {}; correct = 0; xp = 0
    for row in rows:
        p = _payload(row); name = _safe_name(row.get("display_name")); users[name] = users.get(name, 0) + 1
        mode = str(p.get("mode") or "Study Practice"); modes[mode] = modes.get(mode, 0) + 1
        correct += 1 if p.get("is_correct") is True else 0; xp += int(p.get("xp_delta", 0) or 0)
    top = sorted(users.items(), key=lambda x: (-x[1], x[0]))[:5]
    top_text = "\n".join(f"{i}. {html.escape(n)} — {c} solved" for i, (n, c) in enumerate(top, 1))
    mode_text = " • ".join(f"{html.escape(k)}: {v}" for k, v in sorted(modes.items()))
    return (f"⏰ <b>RATHOD Study Update</b>\n\n📚 Last {SCORE_DELAY_MINUTES} min me <b>{len(rows)}</b> questions solve hue\n"
            f"✅ Correct attempts: <b>{correct}</b>\n⚡ XP recorded: <b>+{xp}</b>\n🎯 Modes: {mode_text or 'Study Practice'}\n\n"
            f"<b>Active learners</b>\n{top_text or 'Aaj ki pehli study entry ka wait hai 😊'}\n\nSmall steps bhi NEET dream ke paas le jaate hain 💙📖")


def _score_signature(rows: list[dict]) -> dict[str, int]:
    return {str(x.get("telegram_user_id")): int(x.get("total_xp", 0) or 0) for x in rows if x.get("telegram_user_id") is not None}


def _score_message(rows: list[dict]) -> str:
    lines = []
    for i, row in enumerate(rows[:5], 1):
        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        lines.append(f"{medal} {html.escape(_safe_name(row.get('telegram_name')))} — <b>{int(row.get('total_xp', 0) or 0)} XP</b>")
    return (f"🎯 <b>Telegram Quiz Score Update</b>\n\nScore ko approximately {SCORE_DELAY_MINUTES} minutes delay ke baad share kiya gaya hai ⏰\n\n"
            + ("\n".join(lines) if lines else "Abhi score board ready ho raha hai 😊") + "\n\n👏 Padhte raho, leaderboard kabhi bhi change ho sakta hai 🔥📚")


async def process_scores(app: Application) -> None:
    global score_baseline, score_changed_at
    rows = await asyncio.to_thread(_scores); current = _score_signature(rows); now = time.time()
    if score_baseline is None:
        score_baseline = current; return
    if current != score_baseline:
        if score_changed_at is None: score_changed_at = now
        if now - score_changed_at >= SCORE_DELAY_MINUTES * 60 and await send_text(_score_message(rows), app.bot):
            score_baseline = current; score_changed_at = None
    else:
        score_changed_at = None


async def process_events(app: Application) -> None:
    if not (SUPABASE_URL and SUPABASE_KEY and GROUP_CHAT_ID):
        return
    for row in (await asyncio.to_thread(_pending, "immediate", None))[:20]:
        p = _payload(row); title = str(p.get("title") or "📢 RATHOD HUB Update"); body = str(p.get("body") or "Nayi app activity hui hai.")
        if await send_text(f"{html.escape(title)}\n\n{html.escape(body)}\n\n<i>— {BOT_NAME} 💙</i>", app.bot):
            await asyncio.to_thread(_mark, [int(row["id"])], "immediate")
    cutoff = _now() - timedelta(minutes=SCORE_DELAY_MINUTES)
    rows = await asyncio.to_thread(_pending, "digest", cutoff)
    if rows and await send_text(_event_digest(rows), app.bot):
        await asyncio.to_thread(_mark, [int(x["id"]) for x in rows], "30-minute-digest")


async def poll_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await process_events(context.application); await process_scores(context.application)
    except Exception:
        logger.exception("Bridge polling failed")


async def motivation_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global last_motivation, last_line
    if time.time() - last_motivation < MOTIVATION_MINUTES * 60:
        return
    choices = [x for x in MOTIVATION_LINES if x != last_line] or MOTIVATION_LINES; line = random.choice(choices)
    if await send_text(f"💌 <b>{BOT_NAME}</b> ki chhoti si reminder\n\n{html.escape(line)}\n\n<i>{BOT_BYLINE}</i>", context.application.bot):
        last_line = line; last_motivation = time.time()


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(f"👋 Namaste! Main <b>{BOT_NAME}</b> hoon—RATHOD HUB ki friendly female study companion.\n\n{BOT_BYLINE}\n\nMain quiz nahi banati; main app updates, score digest, winners aur motivation group tak laati hoon 📚✨", parse_mode=ParseMode.HTML)


async def bridgehelp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("💙 <b>RATHOD SAKHI</b>\n\n• App updates\n• 30-minute score digest\n• NEET 720, Daily 9 PM aur Live Quiz activity\n• Winners/leaderboard\n• New member welcome\n• /ask se online AI ya offline fallback help\n\n" + BOT_BYLINE, parse_mode=ParseMode.HTML)


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = " ".join(context.args or []).strip()
    if not question:
        await update.effective_message.reply_text("Use: /ask apna sawal likhiye 💙")
        return
    wait = await update.effective_message.reply_text("💭 Sakhi soch rahi hoon…")
    await wait.edit_text(html.escape(await ask_ai(question)), parse_mode=ParseMode.HTML)


async def chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text or message.text.startswith("/"):
        return
    if update.effective_chat and update.effective_chat.type == "private":
        question = message.text.strip()
    else:
        username = str(context.bot.username or "").lower(); marker = f"@{username}" if username else ""
        if not marker or marker not in message.text.lower():
            return
        question = message.text.replace(marker, "").strip()
    if not question:
        await message.reply_text("Ji, poochhiye na 😊 Main help karungi.")
        return
    await message.reply_text(html.escape(await ask_ai(question)), parse_mode=ParseMode.HTML)


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.new_chat_members:
        return
    for member in update.message.new_chat_members[:8]:
        if not member.is_bot:
            await send_text(f"🎉 <b>Welcome {html.escape(member.first_name or 'Aspirant')}!</b>\n\nRATHOD HUB family me aapka pyaara swagat hai 💙\nDaily quiz, NEET practice aur friendly study energy milegi 📚✨\n\n— RATHOD SAKHI 👋", context.bot, update.effective_chat.id)


async def post_init(app: Application) -> None:
    existing = await app.bot.get_my_commands(); known = {x.command for x in existing}
    additions = [BotCommand("about", "Who made the VIP bridge bot"), BotCommand("bridgehelp", "Bridge bot features"), BotCommand("ask", "Ask RATHOD SAKHI")]
    await app.bot.set_my_commands(list(existing) + [x for x in additions if x.command not in known])
    if app.job_queue:
        app.job_queue.run_repeating(poll_job, interval=POLL_SECONDS, first=8, name="rh-bridge-poll")
        app.job_queue.run_repeating(motivation_job, interval=60, first=120, name="rh-bridge-motivation")


def main() -> None:
    if not BOT_TOKEN: raise SystemExit("BRIDGE_TELEGRAM_BOT_TOKEN is missing")
    if not SUPABASE_URL or not SUPABASE_KEY: raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("about", about)); app.add_handler(CommandHandler("bridgehelp", bridgehelp)); app.add_handler(CommandHandler("ask", ask_command))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, chat_message))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, chat_message))
    logger.info("%s started; score delay=%sm; poll=%ss; OpenRouter=%s; Gemini=%s; Groq=%s", BOT_NAME, SCORE_DELAY_MINUTES, POLL_SECONDS, bool(OPENROUTER_KEY), bool(GEMINI_KEY), bool(GROQ_KEY))
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
