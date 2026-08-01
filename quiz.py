"""
Quiz session management + Gemini question generation.
"""
import asyncio
import json
import logging
import os
import re
import textwrap
from datetime import datetime
from typing import NamedTuple

from google import genai
from google.genai import types as genai_types
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

from config import (CORRECT_SCORE, POLL_OPEN_PERIOD,
                     UNANSWERED_SCORE, WRONG_SCORE)
from database import ensure_user, get_rank, save_quiz_result

logger = logging.getLogger(__name__)

class ModelSlot(NamedTuple):
    model: str
    api_version: str

CANDIDATE_SLOTS: list[ModelSlot] = [
    ModelSlot("gemini-2.5-flash", "v1beta"),
    ModelSlot("gemini-2.0-flash", "v1beta"),
    ModelSlot("gemini-flash-latest", "v1beta"),
]

_clients: dict[str, genai.Client] = {}
_working_slot: ModelSlot = ModelSlot("gemini-2.5-flash", "v1beta")

def _get_client(api_version: str = "v1beta") -> genai.Client:
    if api_version not in _clients:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set in environment variables.")
        _clients[api_version] = genai.Client(
            api_key=api_key,
            http_options=genai_types.HttpOptions(api_version=api_version),
        )
        logger.info("Created Gemini client for endpoint: %s", api_version)
    return _clients[api_version]

def _parse_retry_after(exc: Exception) -> float:
    msg = str(exc)
    m = re.search(r"retryDelay['\": ]+(\d+\.?\d*)s", msg)
    if m:
        return float(m.group(1))
    return 60.0

def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg

def verify_gemini_key() -> bool:
    try:
        client = _get_client("v1beta")
        models = list(client.models.list())
        logger.info("✅ Gemini key verified successfully.")
        return True
    except Exception as exc:
        logger.error("❌ Gemini key validation failed: %s", exc)
        return False

# in-memory session store
active_sessions: dict[int, dict] = {}
poll_to_user: dict[str, int] = {}
group_sessions: dict[int, dict] = {}
poll_to_chat: dict[str, int] = {}

def _build_prompt(topic: str, count: int, style: str = "quiz") -> str:
    pyq_hint = (
        " Model the questions after Indian competitive exam PYQ style "
        "(NEET/JEE), focusing on conceptual depth."
        if style == "pyq" else ""
    )
    return textwrap.dedent(f"""
        Generate exactly {count} multiple-choice questions about: "{topic}".{pyq_hint}

        MANDATORY RULES:
        1. Each question MUST have EXACTLY 4 answer options.
        2. correct_index MUST be 0, 1, 2, or 3 (0-based index).
        3. Output ONLY a valid JSON array with no markdown formatting, no code fences.
        4. The response MUST start with '[' and end with ']'.

        JSON format:
        [
          {{
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": 0
          }}
        ]
    """).strip()

def _safe_parse_json(text: str) -> list:
    if not text:
        raise ValueError("Empty response from Gemini")
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON array found. Response: {text[:200]!r}")
    return json.loads(text[start:end + 1])

def _validate(raw: list, needed: int) -> list[dict]:
    valid: list[dict] = []
    for i, q in enumerate(raw):
        if not isinstance(q, dict):
            continue
        if not str(q.get("question", "")).strip():
            continue
        opts = q.get("options", [])
        if not isinstance(opts, list) or len(opts) != 4:
            continue
        try:
            cidx = int(q["correct_index"])
        except (KeyError, TypeError, ValueError):
            continue
        if cidx not in (0, 1, 2, 3):
            continue
        valid.append({
            "question": str(q["question"]).strip(),
            "options": [str(o).strip() for o in opts],
            "correct_index": cidx,
        })
        if len(valid) >= needed:
            break
    return valid

def _sync_generate(slot: ModelSlot, prompt: str) -> str:
    client = _get_client(slot.api_version)
    resp = client.models.generate_content(
        model=slot.model,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=8192,
        ),
    )
    return resp.text or ""

async def generate_questions(topic: str, count: int, style: str = "quiz") -> list[dict]:
    global _working_slot
    base_slot = _working_slot
    remaining = [base_slot] + [s for s in CANDIDATE_SLOTS if s != base_slot]
    slots_queue = remaining * 2

    accumulated: list[dict] = []
    last_exc: Exception | None = None

    for attempt, slot in enumerate(slots_queue, start=1):
        needed = count - len(accumulated)
        if needed <= 0:
            break

        prompt = _build_prompt(topic, needed, style)
        label = f"#{attempt} [{slot.model}]"

        try:
            raw_text = await asyncio.to_thread(_sync_generate, slot, prompt)
        except Exception as exc:
            last_exc = exc
            logger.error("Attempt %s FAILED: %s", label, exc)
            if _is_quota_error(exc):
                await asyncio.sleep(5)
            else:
                await asyncio.sleep(1)
            continue

        try:
            raw = _safe_parse_json(raw_text)
        except ValueError as parse_exc:
            last_exc = parse_exc
            logger.warning("Attempt %s parse error: %s", label, parse_exc)
            continue

        valid = _validate(raw, needed)
        accumulated.extend(valid)
        if valid:
            _working_slot = slot

        if len(accumulated) >= count:
            break
        await asyncio.sleep(0.5)

    if not accumulated:
        raise RuntimeError(f"Failed to generate questions. Last error: {last_exc}")

    return accumulated[:count]

def start_session(user_id: int, chat_id: int, questions: list[dict], topic: str, style: str = "quiz", timer: int = POLL_OPEN_PERIOD) -> dict:
    old = active_sessions.pop(user_id, None)
    if old and old.get("current_poll_id"):
        poll_to_user.pop(old["current_poll_id"], None)

    session: dict = {
        "user_id": user_id,
        "chat_id": chat_id,
        "topic": topic,
        "style": style,
        "questions": questions,
        "total": len(questions),
        "current_idx": 0,
        "correct": 0,
        "wrong": 0,
        "unanswered": 0,
        "score": 0,
        "timer": timer,
        "start_time": datetime.utcnow(),
        "current_poll_id": None,
        "answered_current": False,
        "advance_job": None,
    }
    active_sessions[user_id] = session
    return session

async def send_question(bot: Bot, session: dict):
    idx = session["current_idx"]
    q = session["questions"][idx]
    total = session["total"]
    user_id = session["user_id"]
    chat_id = session["chat_id"]

    q_text = f"❓ Question {idx + 1}/{total}\n\n{q['question']}"
    if len(q_text) > 300:
        q_text = q_text[:297] + "…"
    options = [str(o)[:100] for o in q["options"]]

    try:
        msg = await bot.send_poll(
            chat_id=chat_id,
            question=q_text,
            options=options,
            type="quiz",
            correct_option_id=q["correct_index"],
            is_anonymous=False,
            open_period=session.get("timer", POLL_OPEN_PERIOD),
        
        )
        poll_id = msg.poll.id
        session["current_poll_id"] = poll_id
        session["answered_current"] = False
        poll_to_user[poll_id] = user_id
    except TelegramError as exc:
        logger.error("Poll send failed: %s", exc)

async def _advance_after_timeout(bot: Bot, user_id: int, question_index: int):
    session = active_sessions.get(user_id)
    timer = session.get("timer", POLL_OPEN_PERIOD) if session else POLL_OPEN_PERIOD
    await asyncio.sleep(timer + 1)

    session = active_sessions.get(user_id)
    if not session or session["current_idx"] != question_index:
        return
    if not session["answered_current"]:
        session["unanswered"] += 1
        session["score"] += UNANSWERED_SCORE

    await _next_or_finish(bot, session)

async def _next_or_finish(bot: Bot, session: dict):
    session["current_idx"] += 1
    user_id = session["user_id"]
    if session["current_idx"] >= session["total"]:
        await finish_quiz(bot, session)
    else:
        await send_question(bot, session)
        task = asyncio.create_task(_advance_after_timeout(bot, user_id, session["current_idx"]))
        session["advance_job"] = task

async def handle_poll_answer(bot: Bot, user_id: int, poll_id: str, selected_option: int):
    session = active_sessions.get(user_id)
    if not session or session["current_poll_id"] != poll_id or session["answered_current"]:
        return

    session["answered_current"] = True
    q = session["questions"][session["current_idx"]]

    if selected_option == q["correct_index"]:
        session["correct"] += 1
        session["score"] += CORRECT_SCORE
    else:
        session["wrong"] += 1
        session["score"] += WRONG_SCORE

async def finish_quiz(bot: Bot, session: dict):
    user_id = session["user_id"]
    chat_id = session["chat_id"]

    poll_to_user.pop(session.get("current_poll_id", ""), None)
    active_sessions.pop(user_id, None)

    save_quiz_result(
        user_id=user_id, chat_id=chat_id,
        correct=session["correct"], wrong=session["wrong"],
        unanswered=session["unanswered"], score=session["score"],
        topic=session["topic"], total=session["total"],
    )

    rank = get_rank(user_id, chat_id)
    duration = (datetime.utcnow() - session["start_time"]).seconds
    mins, secs = divmod(duration, 60)
    answered = session["correct"] + session["wrong"]
    accuracy = f"{session['correct'] / answered * 100:.1f}%" if answered > 0 else "0.0%"

    text = (
        f"🎉 *QUIZ COMPLETE!*\n\n"
        f"📖 Topic: *{session['topic']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 Total: `{session['total']}`\n"
        f"✅ Correct: `{session['correct']}`\n"
        f"❌ Wrong: `{session['wrong']}`\n"
        f"⏭ Unanswered: `{session['unanswered']}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⭐ Score: `{session['score']:+}`\n"
        f"🎯 Accuracy: `{accuracy}`\n"
        f"🏅 Rank: `#{rank}`\n"
        f"⏱ Time: `{mins}m {secs}s`\n"
    )
    try:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.MARKDOWN)
    except TelegramError as exc:
        logger.error("Result card failed: %s", exc)

def start_group_session(chat_id: int, questions: list[dict], topic: str, timer: int) -> dict:
    old = group_sessions.pop(chat_id, None)
    if old and old.get("current_poll_id"):
        poll_to_chat.pop(old["current_poll_id"], None)

    session: dict = {
        "chat_id": chat_id,
        "topic": topic,
        "questions": questions,
        "total": len(questions),
        "current_idx": 0,
        "timer": timer,
        "current_poll_id": None,
        "current_correct": None,
        "advance_job": None,
        "answered_users": set(),
        "user_scores": {},
    }
    group_sessions[chat_id] = session
    return session

async def send_group_question(bot: Bot, session: dict):
    idx = session["current_idx"]
    q = session["questions"][idx]
    total = session["total"]
    chat_id = session["chat_id"]

    q_text = f"📅 Daily Quiz — ❓ Q{idx + 1}/{total}\n\n{q['question']}"
    if len(q_text) > 300:
        q_text = q_text[:297] + "…"
    options = [str(o)[:100] for o in q["options"]]

    try:
        msg = await bot.send_poll(
            chat_id=chat_id,
            question=q_text,
            options=options,
            type="quiz",
            correct_option_id=q["correct_index"],
            is_anonymous=False,
            open_period=session["timer"],
        )
        session["current_poll_id"] = msg.poll.id
        session["current_correct"] = q["correct_index"]
        session["answered_users"] = set()
        poll_to_chat[msg.poll.id] = chat_id
    except TelegramError as exc:
        logger.error("Group poll send failed: %s", exc)

async def handle_group_poll_answer(bot: Bot, chat_id: int, user_id: int, name: str, username: str, poll_id: str, selected_option: int):
    session = group_sessions.get(chat_id)
    if not session or session.get("current_poll_id") != poll_id:
        return
    if user_id in session["answered_users"]:
        return
    session["answered_users"].add(user_id)
    ensure_user(user_id, chat_id, username, name)
    if user_id not in session["user_scores"]:
        session["user_scores"][user_id] = {"name": name, "username": username, "correct": 0, "wrong": 0, "score": 0}

    stats = session["user_scores"][user_id]
    if selected_option == session["current_correct"]:
        stats["correct"] += 1
        stats["score"] += CORRECT_SCORE
    else:
        stats["wrong"] += 1
        stats["score"] += WRONG_SCORE

async def _advance_group_after_timeout(bot: Bot, chat_id: int, question_index: int):
    session = group_sessions.get(chat_id)
    timer = session.get("timer", POLL_OPEN_PERIOD) if session else POLL_OPEN_PERIOD
    await asyncio.sleep(timer + 1)

    session = group_sessions.get(chat_id)
    if not session or session["current_idx"] != question_index:
        return
    await _next_or_finish_group(bot, session)

async def _next_or_finish_group(bot: Bot, session: dict):
    session["current_idx"] += 1
    chat_id = session["chat_id"]
    if session["current_idx"] >= session["total"]:
        await finish_group_quiz(bot, session)
    else:
        await send_group_question(bot, session)
        task = asyncio.create_task(_advance_group_after_timeout(bot, chat_id, session["current_idx"]))
        session["advance_job"] = task

async def finish_group_quiz(bot: Bot, session: dict):
    chat_id = session["chat_id"]
    poll_to_chat.pop(session.get("current_poll_id", ""), None)
    group_sessions.pop(chat_id, None)

    total = session["total"]
    for user_id, stats in session["user_scores"].items():
        ensure_user(user_id, chat_id, stats["username"], stats["name"])
        unanswered = total - stats["correct"] - stats["wrong"]
        save_quiz_result(
            user_id=user_id, chat_id=chat_id,
            correct=stats["correct"], wrong=stats["wrong"],
            unanswered=unanswered, score=stats["score"],
            topic=session["topic"], total=total,
        )

    if session["user_scores"]:
        sorted_users = sorted(session["user_scores"].items(), key=lambda x: x[1]["score"], reverse=True)
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        lines = [f"📅 *Daily Quiz Complete!*\n", f"📖 Topic: *{session['topic']}* | Questions: `{total}`", "━━━━━━━━━━━━━━━━━━"]
        for i, (uid, s) in enumerate(sorted_users[:10]):
            medal = medals.get(i, f"{i + 1}.")
            dname = s["name"] or s["username"] or "User"
            lines.append(f"{medal} *{dname}* — `{s['score']:+}` (✅{s['correct']} ❌{s['wrong']})")
        lines.append("━━━━━━━━━━━━━━━━━━")
    else:
        lines = [f"📅 *Daily Quiz Complete!*\n", f"📖 Topic: *{session['topic']}*", "\n_No one answered this quiz._"]

    try:
        await bot.send_message(chat_id=chat_id, text="\n".join(lines), parse_mode=ParseMode.MARKDOWN)
    except TelegramError as exc:
        logger.error("Group result card failed: %s", exc)
