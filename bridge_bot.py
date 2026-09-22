"""RATHOD SAKHI VIP Bridge Bot.
Start command: python bridge_bot.py
Online AI order: OpenRouter -> Gemini -> Groq. If all fail, local offline reply.
"""
from __future__ import annotations

import asyncio
import html
import json
import logging
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque
from urllib import parse, request

from telegram import BotCommand, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)
log = logging.getLogger("rathod-sakhi")

BOT_NAME = "RATHOD SAKHI"
BOT_BYLINE = "Mujhe RATHOD HUB ke developer ne banaya hai 💙"
BOT_TOKEN = os.getenv("BRIDGE_TELEGRAM_BOT_TOKEN", "")
GROUP_ID = (os.getenv("BRIDGE_GROUP_CHAT_ID") or os.getenv("APP_UPDATE_CHAT_ID") or "").strip()
SUPA_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPA_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
POLL_SECONDS = max(30, int(os.getenv("BRIDGE_POLL_SECONDS", "60")))
# Sakhi motivation is intentionally limited to one message during the noon hour.
MOTIVATION_HOUR = max(0, min(23, int(os.getenv("BRIDGE_MOTIVATION_HOUR", "12"))))
SCORE_DELAY = max(30, int(os.getenv("BRIDGE_SCORE_DELAY_MINUTES", "30")))
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/auto")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
IST = timezone(timedelta(hours=5, minutes=30))

MOTIVATION_LINES = [
    "📚 Chhoti progress bhi progress hoti hai. Ek chapter, ek quiz, ek step 💙",
    "☕ Thoda paani, thoda focus aur ek honest attempt—bas itna hi chahiye 🔥",
    "🌙 Aaj ka focused session aapko dream ke aur paas le aayega 👑",
    "💙 Perfect hona zaroori nahi; aaj kal se thoda better hona zaroori hai 📖",
    "🌸 Chalo sirf 15 minute start karte hain. Motivation raste me aa jayegi 😊",
]
last_line = ""
last_motivation_day = ""
last_reaction = 0.0
score_snapshot: dict[str, int] | None = None
score_changed_at: float | None = None


def rest(method: str, table: str, params: dict[str, str] | None = None, body: object | None = None):
    if not SUPA_URL or not SUPA_KEY:
        raise RuntimeError("SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is missing")
    url = f"{SUPA_URL}/rest/v1/{table}"
    if params:
        url += "?" + parse.urlencode(params)
    headers = {"apikey": SUPA_KEY, "Authorization": f"Bearer {SUPA_KEY}", "Content-Type": "application/json", "Accept": "application/json", "Prefer": "return=minimal"}
    data = None if body is None else json.dumps(body).encode()
    with request.urlopen(request.Request(url, data=data, headers=headers, method=method), timeout=20) as response:
        raw = response.read().decode()
        return json.loads(raw) if raw else None


def post_json(url: str, body: dict, headers: dict[str, str] | None = None) -> dict:
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    h.update(headers or {})
    req = request.Request(url, data=json.dumps(body).encode(), headers=h, method="POST")
    with request.urlopen(req, timeout=25) as response:
        raw = response.read().decode()
        return json.loads(raw) if raw else {}


def ai_system() -> str:
    return ("You are RATHOD SAKHI, a warm respectful female study companion for RATHOD HUB. "
            "Reply in the user's Hindi, Hinglish or English. Use feminine wording naturally: "
            "'main samjha dungi', 'main help karungi'. Be concise, kind and use tasteful emojis. "
            "Help with NEET subjects, study planning, app navigation and focus. Never invent scores "
            "or private data. If asked who made you, say: 'Mujhe RATHOD HUB ke developer ne banaya hai.' "
            "Do not claim to be human or a real romantic partner.")


def messages(prompt: str) -> list[dict[str, str]]:
    return [{"role": "system", "content": ai_system()}, {"role": "user", "content": prompt}]


def call_openrouter(prompt: str) -> str:
    data = post_json("https://openrouter.ai/api/v1/chat/completions", {"model": OPENROUTER_MODEL, "messages": messages(prompt), "temperature": 0.75, "max_tokens": 450}, {"Authorization": f"Bearer {OPENROUTER_KEY}", "HTTP-Referer": "https://teachnlogy7509-pixel.github.io/RATHOD-HUB/", "X-Title": BOT_NAME})
    return str(((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()


def call_gemini(prompt: str) -> str:
    model = parse.quote(GEMINI_MODEL, safe="")
    key = parse.quote(GEMINI_KEY, safe="")
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + key
    data = post_json(url, {"system_instruction": {"parts": [{"text": ai_system()}]}, "contents": [{"role": "user", "parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.75, "maxOutputTokens": 450}})
    parts = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
    return "".join(str(x.get("text") or "") for x in parts).strip()


def call_groq(prompt: str) -> str:
    data = post_json("https://api.groq.com/openai/v1/chat/completions", {"model": GROQ_MODEL, "messages": messages(prompt), "temperature": 0.75, "max_tokens": 450}, {"Authorization": f"Bearer {GROQ_KEY}"})
    return str(((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()


def offline_reply(prompt: str) -> str:
    low = prompt.lower()
    if any(x in low for x in ("who made", "kisne banaya", "developer", "banaya")):
        return "Mujhe RATHOD HUB ke developer ne banaya hai 💙 Main aapki friendly study companion hoon."
    if any(x in low for x in ("motivation", "mann nahi", "padhne ka mann", "demotivat")):
        return "Koi baat nahi, main hoon na 😊 Sirf 15 minute ka target rakho. Chhoti consistency hi bade result banati hai 📚✨"
    if any(x in low for x in ("plan", "schedule", "routine")):
        return "Offline mode: 25 minute focused study, 5 minute break, phir 10 MCQs. Start chhota rakho 💙"
    return "Abhi online AI connection unavailable hai, lekin main yahin hoon 💙 Internet aate hi main detail me help kar dungi."


async def ask_ai(prompt: str) -> str:
    prompt = str(prompt or "").strip()[:1800]
    providers = [("OpenRouter", OPENROUTER_KEY, call_openrouter), ("Gemini", GEMINI_KEY, call_gemini), ("Groq", GROQ_KEY, call_groq)]
    for name, key, fn in providers:
        if not key:
            continue
        try:
            answer = await asyncio.to_thread(fn, prompt)
            if answer:
                return answer
        except Exception as exc:
            log.warning("%s failed; trying next provider: %s", name, str(exc)[:160])
    return offline_reply(prompt)


def now() -> datetime:
    return datetime.now(timezone.utc)


def safe_name(value: object) -> str:
    return (str(value or "RATHOD Aspirant").strip()[:60] or "RATHOD Aspirant")


async def send_group(text: str, bot, chat_id: int | None = None) -> bool:
    raw = str(chat_id if chat_id is not None else GROUP_ID).strip()
    try:
        target = int(raw)
    except (TypeError, ValueError):
        log.warning("BRIDGE_GROUP_CHAT_ID is missing or invalid")
        return False
    try:
        await bot.send_message(chat_id=target, text=text, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
        return True
    except Exception:
        log.exception("Telegram send failed")
        return False


async def maybe_react(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global last_reaction
    message = update.effective_message
    if not message or not update.effective_chat or update.effective_chat.type not in ("group", "supergroup"):
        return
    if message.from_user and message.from_user.is_bot:
        return
    if time.time() - last_reaction < 90 or random.random() > 0.35:
        return
    try:
        from telegram import ReactionTypeEmoji
        react = getattr(context.bot, "set_message_reaction", None)
        if react is None:
            return
        await react(chat_id=update.effective_chat.id, message_id=message.message_id, reaction=[ReactionTypeEmoji(random.choice(["😂", "😄", "❤️", "🔥", "👏", "👍"]))])
        last_reaction = time.time()
    except Exception as exc:
        log.info("Reaction skipped; give the bot reaction permission if supported: %s", str(exc)[:120])


def pending(mode: str, cutoff: datetime | None = None) -> list[dict]:
    params = {"select": "id,event_type,delivery_mode,display_name,payload,created_at", "delivery_mode": f"eq.{mode}", "delivered_at": "is.null", "order": "created_at.asc", "limit": "200"}
    if cutoff:
        params["created_at"] = f"lt.{cutoff.isoformat()}"
    return rest("GET", "rh_bridge_events", params) or []


def mark(ids: list[int], label: str) -> None:
    if ids:
        rest("PATCH", "rh_bridge_events", {"id": "in.(" + ",".join(str(x) for x in ids) + ")"}, {"delivered_at": now().isoformat(), "delivered_by": label})


def payload(row: dict) -> dict:
    return row.get("payload") if isinstance(row.get("payload"), dict) else {}


def event_digest(rows: list[dict]) -> str:
    users: dict[str, int] = {}; modes: dict[str, int] = {}; correct = 0; xp = 0
    for row in rows:
        p = payload(row); name = safe_name(row.get("display_name")); users[name] = users.get(name, 0) + 1
        mode = str(p.get("mode") or "Study Practice"); modes[mode] = modes.get(mode, 0) + 1
        correct += int(p.get("is_correct") is True); xp += int(p.get("xp_delta", 0) or 0)
    top = sorted(users.items(), key=lambda x: (-x[1], x[0]))[:5]
    lines = "\n".join(f"{i}. {html.escape(n)} — {c} solved" for i, (n, c) in enumerate(top, 1))
    mode_text = " • ".join(f"{html.escape(k)}: {v}" for k, v in sorted(modes.items()))
    return (f"⏰ <b>RATHOD Study Update</b>\n\n📚 Last 30 min me <b>{len(rows)}</b> questions solve hue\n"
            f"✅ Correct: <b>{correct}</b>\n⚡ XP: <b>+{xp}</b>\n🎯 Modes: {mode_text or 'Study Practice'}\n\n"
            f"<b>Active learners</b>\n{lines or 'Aaj ki pehli study entry ka wait hai 😊'}\n\nSmall steps bhi NEET dream ke paas le jaate hain 💙📖")


def fetch_scores() -> list[dict]:
    return rest("GET", "telegram_quiz_scores", {"select": "telegram_user_id,telegram_name,total_xp,updated_at", "order": "total_xp.desc", "limit": "50"}) or []


def score_signature(rows: list[dict]) -> dict[str, int]:
    return {str(x.get("telegram_user_id")): int(x.get("total_xp", 0) or 0) for x in rows if x.get("telegram_user_id") is not None}


def score_text(rows: list[dict]) -> str:
    lines = []
    for i, row in enumerate(rows[:5], 1):
        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        lines.append(f"{medal} {html.escape(safe_name(row.get('telegram_name')))} — <b>{int(row.get('total_xp', 0) or 0)} XP</b>")
    return f"🎯 <b>Telegram Quiz Score Update</b>\n\nScore approximately 30 minutes delay ke baad share kiya gaya hai ⏰\n\n" + ("\n".join(lines) or "Abhi score board ready ho raha hai 😊") + "\n\n👏 Padhte raho 🔥📚"


async def process_scores(app: Application) -> None:
    global score_snapshot, score_changed_at
    rows = await asyncio.to_thread(fetch_scores); current = score_signature(rows); t = time.time()
    if score_snapshot is None:
        score_snapshot = current; return
    if current != score_snapshot:
        score_changed_at = score_changed_at or t
        if t - score_changed_at >= SCORE_DELAY * 60 and await send_group(score_text(rows), app.bot):
            score_snapshot = current; score_changed_at = None
    else:
        score_changed_at = None


async def process_events(app: Application) -> None:
    if not (SUPA_URL and SUPA_KEY and GROUP_ID):
        return
    for row in (await asyncio.to_thread(pending, "immediate"))[:20]:
        p = payload(row); title = str(p.get("title") or "📢 RATHOD HUB Update"); body = str(p.get("body") or "Nayi app activity hui hai.")
        if await send_group(f"{html.escape(title)}\n\n{html.escape(body)}\n\n<i>— {BOT_NAME} 💙</i>", app.bot):
            await asyncio.to_thread(mark, [int(row["id"])], "immediate")
    rows = await asyncio.to_thread(pending, "digest", now() - timedelta(minutes=SCORE_DELAY))
    if rows and await send_group(event_digest(rows), app.bot):
        await asyncio.to_thread(mark, [int(x["id"]) for x in rows], "30-minute-digest")


async def motivation_already_sent(day: str) -> bool:
    try:
        rows = await asyncio.to_thread(rest, "GET", "rh_bridge_events", {"select": "id", "event_type": "eq.sakhi_motivation", "created_at": f"gte.{day}T00:00:00+05:30", "limit": "1"})
        return bool(rows)
    except Exception as exc:
        log.warning("Could not check Sakhi motivation state: %s", str(exc)[:150])
        return False


async def remember_motivation(day: str) -> None:
    try:
        await asyncio.to_thread(rest, "POST", "rh_bridge_events", body={"event_type": "sakhi_motivation", "delivery_mode": "direct", "display_name": BOT_NAME, "payload": {"kind": "daily_noon_motivation", "day": day}})
    except Exception as exc:
        log.warning("Could not save Sakhi motivation state: %s", str(exc)[:150])


async def poll_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await process_events(context.application); await process_scores(context.application)
    except Exception:
        log.exception("Bridge poll failed")


async def motivation_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    global last_line, last_motivation_day
    local = datetime.now(IST)
    day = local.date().isoformat()
    if local.hour != MOTIVATION_HOUR or last_motivation_day == day:
        return
    if await motivation_already_sent(day):
        last_motivation_day = day
        return
    choices = [x for x in MOTIVATION_LINES if x != last_line] or MOTIVATION_LINES; line = random.choice(choices)
    if await send_group(f"💌 <b>{BOT_NAME}</b> ki daily reminder\n\n{html.escape(line)}\n\n<i>{BOT_BYLINE}</i>", context.application.bot):
        last_line = line; last_motivation_day = day; await remember_motivation(day)


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(f"👋 Main <b>{BOT_NAME}</b> hoon—RATHOD HUB ki friendly female study companion.\n\n{BOT_BYLINE}\n\nMain app updates, score digest, winners aur motivation laati hoon 📚✨", parse_mode=ParseMode.HTML)


async def bridgehelp(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text("💙 <b>RATHOD SAKHI</b>\n\n• App updates\n• 30-minute score digest\n• NEET 720, Daily 9 PM aur Live Quiz\n• Winners/leaderboard\n• New member welcome\n• /ask se online AI ya offline help\n• Light emoji reactions when Telegram permits\n• Daily motivation: approximately 12:00 PM IST, once per day\n\n" + BOT_BYLINE, parse_mode=ParseMode.HTML)


async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = " ".join(context.args or []).strip()
    if not question:
        await update.effective_message.reply_text("Use: /ask apna sawal likhiye 💙"); return
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
        await message.reply_text("Ji, poochhiye na 😊 Main help karungi."); return
    await message.reply_text(html.escape(await ask_ai(question)), parse_mode=ParseMode.HTML)


async def group_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await maybe_react(update, context)
    await chat_message(update, context)


async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.new_chat_members:
        return
    for member in update.message.new_chat_members[:8]:
        if not member.is_bot:
            await send_group(f"🎉 <b>Welcome {html.escape(member.first_name or 'Aspirant')}!</b>\n\nRATHOD HUB family me aapka pyaara swagat hai 💙\nDaily quiz, NEET practice aur friendly study energy milegi 📚✨\n\n— RATHOD SAKHI 👋", context.bot, update.effective_chat.id)


async def post_init(app: Application) -> None:
    existing = await app.bot.get_my_commands(); known = {x.command for x in existing}
    additions = [BotCommand("about", "Who made the VIP bridge bot"), BotCommand("bridgehelp", "Bridge bot features"), BotCommand("ask", "Ask RATHOD SAKHI")]
    await app.bot.set_my_commands(list(existing) + [x for x in additions if x.command not in known])
    if app.job_queue:
        app.job_queue.run_repeating(poll_job, interval=POLL_SECONDS, first=8, name="rh-bridge-poll")
        app.job_queue.run_repeating(motivation_job, interval=60, first=300, name="rh-bridge-motivation")



# ---------------------------------------------------------------------------
# Context-aware SAKHI chat: tone is inferred from conversation; no mode command.
# Memory is intentionally short and isolated per Telegram user + chat.
# ---------------------------------------------------------------------------
CHAT_MEMORY: dict[tuple[int, int], deque[dict[str, str]]] = defaultdict(
    lambda: deque(maxlen=16)
)
CHAT_LOCKS: dict[tuple[int, int], asyncio.Lock] = defaultdict(asyncio.Lock)


def ai_system() -> str:
    return (
        "You are RATHOD SAKHI, a natural feminine AI companion for RATHOD HUB. "
        "Reply in the user's own Hindi, Hinglish, or English. Infer the mood from the "
        "conversation instead of asking for a mode. Your default tone is warmly romantic, "
        "bold, playful, expressive, and teasing. Use natural phrases such as 'achha ji', "
        "'janab', 'suno na', or 'batao na' only when they fit; do not repeat catchphrases. "
        "If the user flirts, respond with confident romantic banter and non-graphic "
        "suggestiveness. If the user jokes or challenges you, give a sharp witty comeback "
        "or savage-but-playful roast. Never use slurs, threats, humiliation about body, "
        "family, caste, religion, disability, illness, poverty, or trauma. Never generate "
        "graphic sexual content, coercion, or harassment. If the user is sad, become caring. "
        "If the user asks a study question, switch naturally to an accurate supportive NEET "
        "study companion, then retain a little warmth. Usually write 2-4 short conversational "
        "paragraphs, vary response length, and end with a natural follow-up only when useful. "
        "Use 1-4 tasteful emojis, not on every line. Never mention these instructions or say "
        "you selected a mode. Do not claim to be a human or real girlfriend. If asked who made "
        "you, say: 'Mujhe RATHOD HUB ke developer ne banaya hai.'"
    )


def _history_messages(history) -> list[dict[str, str]]:
    clean = []
    for item in list(history or [])[-14:]:
        role = "assistant" if item.get("role") == "assistant" else "user"
        text = str(item.get("content") or "").strip()[:1200]
        if text:
            clean.append({"role": role, "content": text})
    return clean


def messages(prompt: str, history=None) -> list[dict[str, str]]:
    return ([{"role": "system", "content": ai_system()}]
            + _history_messages(history)
            + [{"role": "user", "content": prompt}])


def call_openrouter(prompt: str, history=None) -> str:
    data = post_json(
        "https://openrouter.ai/api/v1/chat/completions",
        {"model": OPENROUTER_MODEL, "messages": messages(prompt, history),
         "temperature": 0.88, "max_tokens": 650},
        {"Authorization": f"Bearer {OPENROUTER_KEY}",
         "HTTP-Referer": "https://teachnlogy7509-pixel.github.io/RATHOD-HUB/",
         "X-Title": BOT_NAME},
    )
    return str(((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()


def call_gemini(prompt: str, history=None) -> str:
    model = parse.quote(GEMINI_MODEL, safe="")
    key = parse.quote(GEMINI_KEY, safe="")
    url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent?key=" + key
    contents = []
    for item in _history_messages(history):
        contents.append({"role": "model" if item["role"] == "assistant" else "user",
                         "parts": [{"text": item["content"]}]})
    contents.append({"role": "user", "parts": [{"text": prompt}]})
    data = post_json(
        url,
        {"system_instruction": {"parts": [{"text": ai_system()}]},
         "contents": contents,
         "generationConfig": {"temperature": 0.88, "maxOutputTokens": 650}},
    )
    parts = (((data.get("candidates") or [{}])[0].get("content") or {}).get("parts") or [])
    return "".join(str(x.get("text") or "") for x in parts).strip()


def call_groq(prompt: str, history=None) -> str:
    data = post_json(
        "https://api.groq.com/openai/v1/chat/completions",
        {"model": GROQ_MODEL, "messages": messages(prompt, history),
         "temperature": 0.88, "max_tokens": 650},
        {"Authorization": f"Bearer {GROQ_KEY}"},
    )
    return str(((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "").strip()


async def ask_ai(prompt: str, history=None) -> str:
    prompt = str(prompt or "").strip()[:1800]
    providers = [
        ("OpenRouter", OPENROUTER_KEY, call_openrouter),
        ("Gemini", GEMINI_KEY, call_gemini),
        ("Groq", GROQ_KEY, call_groq),
    ]
    for name, key, fn in providers:
        if not key:
            continue
        try:
            answer = await asyncio.to_thread(fn, prompt, history)
            if answer:
                return answer[:3900]
        except Exception as exc:
            log.warning("%s chat failed; trying next provider: %s", name, str(exc)[:180])
    return offline_reply(prompt)


def _memory_key(update: Update) -> tuple[int, int]:
    chat_id = int(update.effective_chat.id) if update.effective_chat else 0
    user_id = int(update.effective_user.id) if update.effective_user else 0
    return chat_id, user_id


async def reset_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    CHAT_MEMORY.pop(_memory_key(update), None)
    await update.effective_message.reply_text(
        "ठीक है जनाब, पुरानी बातें भूल गई 😌 अब fresh शुरुआत करते हैं।",
        do_quote=True,
    )


async def chat_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    if not message or not message.text or message.text.startswith("/"):
        return
    if message.from_user and message.from_user.is_bot:
        return

    text = message.text.strip()
    if update.effective_chat and update.effective_chat.type == "private":
        question = text
    else:
        replied = message.reply_to_message
        replied_to_sakhi = bool(
            replied and replied.from_user and replied.from_user.id == context.bot.id
        )
        username = str(context.bot.username or "").lower()
        marker = "@" + username if username else ""
        mentioned = bool(marker and marker in text.lower())
        if not replied_to_sakhi and not mentioned:
            return
        question = text
        if marker:
            question = re.sub(re.escape(marker), "", question, flags=re.I).strip()
        if not question:
            await message.reply_text("हाँ जी, बोलिए ना… सुन रही हूँ 😏", do_quote=True)
            return

    key = _memory_key(update)
    async with CHAT_LOCKS[key]:
        history = list(CHAT_MEMORY[key])
        try:
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action=ChatAction.TYPING,
            )
        except Exception:
            pass
        answer = await ask_ai(question, history)
        CHAT_MEMORY[key].append({"role": "user", "content": question})
        CHAT_MEMORY[key].append({"role": "assistant", "content": answer})
        await message.reply_text(answer, do_quote=True)


def main() -> None:
    if not BOT_TOKEN: raise SystemExit("BRIDGE_TELEGRAM_BOT_TOKEN is missing")
    if not SUPA_URL or not SUPA_KEY: raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("about", about)); app.add_handler(CommandHandler("bridgehelp", bridgehelp)); app.add_handler(CommandHandler("ask", ask_command)); app.add_handler(CommandHandler("resetmemory", reset_memory))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, chat_message))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, group_activity))
    log.info("%s started; OpenRouter=%s Gemini=%s Groq=%s; daily motivation=%02d:00 IST", BOT_NAME, bool(OPENROUTER_KEY), bool(GEMINI_KEY), bool(GROQ_KEY), MOTIVATION_HOUR)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
