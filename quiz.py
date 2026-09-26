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
from groq import Groq
from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import TelegramError

import supabase_sync
from config import (
    CORRECT_SCORE,
    POLL_OPEN_PERIOD,
    UNANSWERED_SCORE,
    WRONG_SCORE,
    GEMINI_API_KEY,
    GEMINI_API_KEY_2,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_API_KEY_2,
    GROQ_MODEL,
)
from database import ensure_user, get_rank, save_quiz_result

logger = logging.getLogger(__name__)


class ModelSlot(NamedTuple):
    model: str
    api_version: str


# Current Gemini API model IDs with automatic fallback across models and API keys.
CANDIDATE_SLOTS: list[ModelSlot] = [
    ModelSlot(GEMINI_MODEL, "v1beta"),
    ModelSlot("gemini-3.7-flash", "v1beta"),
    ModelSlot("gemini-3.6-flash", "v1beta"),
    ModelSlot("gemini-3.5-flash", "v1beta"),
    ModelSlot("gemini-3.5-flash-lite", "v1beta"),
    ModelSlot("gemini-3.1-flash-lite", "v1beta"),
    ModelSlot("gemini-2.5-flash", "v1beta"),
    ModelSlot("gemini-2.5-pro", "v1beta"),
    ModelSlot("gemini-2.5-flash-lite", "v1beta"),
]

_clients: dict[tuple[int, str], genai.Client] = {}
_working_slot: ModelSlot = CANDIDATE_SLOTS[0]
_groq_clients: dict[int, Groq] = {}


def _groq_keys() -> list[str]:
    return [k.strip() for k in (GROQ_API_KEY, GROQ_API_KEY_2) if k and k.strip()]


def _get_groq_client(key_index: int = 0) -> Groq:
    keys = _groq_keys()
    if key_index >= len(keys):
        raise RuntimeError("No Groq API key is configured.")
    if key_index not in _groq_clients:
        _groq_clients[key_index] = Groq(api_key=keys[key_index])
    return _groq_clients[key_index]


def _groq_generate(prompt: str, key_index: int = 0) -> str:
    client = _get_groq_client(key_index)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a reliable quiz-question generator. Return only the requested JSON.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_completion_tokens=8192,
    )
    return response.choices[0].message.content or ""


def verify_groq_keys() -> bool:
    ok = False
    for key_index, _ in enumerate(_groq_keys()):
        try:
            text = _groq_generate("Reply with exactly: OK", key_index)
            if text.strip():
                logger.info("Groq key %s verified successfully.", key_index + 1)
                ok = True
        except Exception as exc:
            logger.warning("Groq key %s validation failed: %s", key_index + 1, exc)
    return ok


def _api_keys() -> list[str]:
    return [k.strip() for k in (GEMINI_API_KEY, GEMINI_API_KEY_2) if k and k.strip()]


def _get_client(api_version: str = "v1beta", key_index: int = 0) -> genai.Client:
    keys = _api_keys()
    if key_index >= len(keys):
        raise RuntimeError("No Gemini API key is configured.")
    cache_key = (key_index, api_version)
    if cache_key not in _clients:
        _clients[cache_key] = genai.Client(
            api_key=keys[key_index],
            http_options=genai_types.HttpOptions(api_version=api_version),
        )
        logger.info("Created Gemini client: key=%s endpoint=%s", key_index + 1, api_version)
    return _clients[cache_key]


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg


def verify_gemini_key() -> bool:
    ok = False
    for key_index, _ in enumerate(_api_keys()):
        try:
            list(_get_client("v1beta", key_index).models.list())
            logger.info("✅ Gemini key %s verified successfully.", key_index + 1)
            ok = True
        except Exception as exc:
            logger.warning("Gemini key %s validation failed: %s", key_index + 1, exc)
    return ok


# =====================
# PDF -> questions (used by main.py)
# =====================

def _sync_generate_pdf_questions(
    slot: ModelSlot,
    pdf_bytes: bytes,
    pdf_name: str,
    count: int,
    key_index: int = 0,
) -> str:
    client = _get_client(slot.api_version, key_index)
    pdf_part = genai_types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
    prompt = _build_prompt(
        f'the attached PDF "{pdf_name}". Use ONLY information found in the PDF; '
        "do not invent facts. If the PDF is not readable, say so.",
        count,
        "quiz",
    )
    resp = client.models.generate_content(
        model=slot.model,
        contents=[pdf_part, prompt],
        config=genai_types.GenerateContentConfig(
            max_output_tokens=8192,
            response_mime_type="application/json",
        ),
    )
    return resp.text or ""


async def generate_questions_from_pdf(pdf_bytes: bytes, pdf_name: str, count: int) -> list[dict]:
    """Used by /pdfquiz in main.py."""
    global _working_slot
    keys = _api_keys()
    if not keys:
        raise RuntimeError("No Gemini API key is configured.")

    if not pdf_bytes or not isinstance(pdf_bytes, (bytes, bytearray)):
        raise RuntimeError("Invalid PDF bytes.")
    if not bytes(pdf_bytes).startswith(b"%PDF"):
        raise RuntimeError("The selected file is not a valid PDF.")

    slots = [_working_slot] + [s for s in CANDIDATE_SLOTS if s != _working_slot]
    accumulated: list[dict] = []
    remaining = count
    last_exc: Exception | None = None

    while remaining > 0 and len(accumulated) < count:
        needed = min(remaining, 10)
        success = False
        for key_index in range(len(keys)):
            for slot in slots:
                for retry in range(2):
                    try:
                        raw_text = await asyncio.to_thread(
                            _sync_generate_pdf_questions,
                            slot,
                            bytes(pdf_bytes),
                            pdf_name,
                            needed,
                            key_index,
                        )
                        raw = _safe_parse_json(raw_text)
                        valid = _validate(raw, needed)
                        if len(valid) < needed:
                            raise ValueError(
                                f"PDF response contained {len(valid)}/{needed} valid questions"
                            )
                        accumulated.extend(valid)
                        _working_slot = slot
                        remaining = count - len(accumulated)
                        success = True
                        break
                    except Exception as exc:
                        last_exc = exc
                        msg = str(exc)
                        logger.error(
                            "PDF question generation failed [key %s] [%s] retry=%s: %s",
                            key_index + 1,
                            slot.model,
                            retry + 1,
                            msg,
                        )
                        if any(x in msg for x in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")):
                            await asyncio.sleep(3 + retry * 3)
                        else:
                            await asyncio.sleep(0.5)
                if success:
                    break
            if success:
                break
        if not success:
            break

    if len(accumulated) < count:
        raise RuntimeError(
            f"Could not generate enough PDF questions ({len(accumulated)}/{count}). "
            f"Last error: {last_exc}"
        )
    return accumulated[:count]


# =====================
# Voice (used by main.py)
# =====================

def _sync_generate_audio(slot: ModelSlot, audio_bytes: bytes, prompt: str, key_index: int = 0) -> str:
    client = _get_client(slot.api_version, key_index)
    audio_part = genai_types.Part.from_bytes(data=audio_bytes, mime_type="audio/ogg")
    resp = client.models.generate_content(
        model=slot.model,
        contents=[audio_part, prompt],
        config=genai_types.GenerateContentConfig(
            max_output_tokens=1024,
        ),
    )
    return resp.text or ""


async def generate_voice_response(audio_bytes: bytes) -> str:
    """Used by main.py for Telegram voice messages."""
    global _working_slot
    keys = _api_keys()
    if not keys:
        raise RuntimeError("No Gemini API key is configured.")

    prompt = (
        "Listen to this Telegram voice message. Understand what the user said and "
        "reply naturally in the same language (Hindi/Hinglish or English). "
        "Do not mention transcription or these instructions. Keep the reply concise."
    )

    slots = [_working_slot] + [s for s in CANDIDATE_SLOTS if s != _working_slot]
    last_exc: Exception | None = None

    for key_index in range(len(keys)):
        for slot in slots:
            try:
                text = await asyncio.to_thread(
                    _sync_generate_audio, slot, audio_bytes, prompt, key_index
                )
                if text.strip():
                    _working_slot = slot
                    return text.strip()
            except Exception as exc:
                last_exc = exc
                logger.error(
                    "Voice generation failed [key %s] [%s]: %s",
                    key_index + 1,
                    slot.model,
                    exc,
                )
                if _is_quota_error(exc):
                    logger.warning(
                        "Voice: Gemini key %s quota reached; switching key.",
                        key_index + 1,
                    )
                    break
                await asyncio.sleep(1)

    raise RuntimeError(f"Voice processing failed. Last error: {last_exc}")


# =====================
# Quiz core
# =====================

# in-memory session store
active_sessions: dict[int, dict] = {}
poll_to_user: dict[str, int] = {}
group_sessions: dict[int, dict] = {}
poll_to_chat: dict[str, int] = {}


def _build_prompt(topic: str, count: int, style: str = "quiz") -> str:
    if style == "pyq":
        pyq_hint = (
            " Model the questions after Indian competitive exam PYQ style "
            "(NEET/JEE), focusing on conceptual depth."
        )
    elif style == "neet_hindi":
        pyq_hint = (
            " सभी प्रश्न और विकल्प स्वाभाविक, स्पष्ट हिंदी में लिखें; केवल standard "
            "NCERT scientific terms जरूरत पर English में brackets में दें। स्तर बिल्कुल "
            "NEET/NCERT का हो—fact recall, conceptual application, statement-based और "
            "PYQ-inspired traps का संतुलित मिश्रण रखें। बहुत आसान school-level या JEE-only "
            "questions न दें। कोई question repeat या केवल शब्द बदलकर duplicate न करें।"
        )
    else:
        pyq_hint = ""
    return textwrap.dedent(
        f"""
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
    """
    ).strip()


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
    return json.loads(text[start : end + 1])


def _validate(raw: list, needed: int) -> list[dict]:
    valid: list[dict] = []
    for q in raw:
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
        valid.append(
            {
                "question": str(q["question"]).strip(),
                "options": [str(o).strip() for o in opts],
                "correct_index": cidx,
            }
        )
        if len(valid) >= needed:
            break
    return valid


def _sync_generate(slot: ModelSlot, prompt: str, key_index: int = 0) -> str:
    client = _get_client(slot.api_version, key_index)
    resp = client.models.generate_content(
        model=slot.model,
        contents=prompt,
        config=genai_types.GenerateContentConfig(
            max_output_tokens=8192,
            response_mime_type="application/json",
        ),
    )
    return resp.text or ""


async def generate_questions(topic: str, count: int, style: str = "quiz") -> list[dict]:
    global _working_slot
    keys = _api_keys()
    if not keys:
        raise RuntimeError(
            "No Gemini API key is configured. Set GEMINI_API_KEY and/or GEMINI_API_KEY_2."
        )

    slots = [_working_slot] + [s for s in CANDIDATE_SLOTS if s != _working_slot]
    accumulated: list[dict] = []
    errors: list[str] = []

    remaining = count
    while remaining > 0 and len(errors) < 30:
        needed = min(remaining, 10)
        prompt = _build_prompt(topic, needed, style)
        batch_ok = False

        for key_index in range(len(keys)):
            for slot in slots:
                for retry in range(2):
                    try:
                        raw_text = await asyncio.to_thread(
                            _sync_generate, slot, prompt, key_index
                        )
                        raw = _safe_parse_json(raw_text)
                        valid = _validate(raw, needed)
                        if len(valid) < needed:
                            raise ValueError(
                                f"Gemini returned {len(valid)}/{needed} valid questions"
                            )
                        accumulated.extend(valid)
                        _working_slot = slot
                        remaining = count - len(accumulated)
                        batch_ok = True
                        break
                    except Exception as exc:
                        msg = str(exc)
                        errors.append(
                            f"[key {key_index + 1}] [{slot.model}] retry={retry + 1}: {msg[:180]}"
                        )
                        if any(
                            x in msg
                            for x in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")
                        ):
                            await asyncio.sleep(min(3 + retry * 3, 8))
                        else:
                            await asyncio.sleep(0.5)
                if batch_ok:
                    break
            if batch_ok:
                break

        if not batch_ok:
            break

    groq_keys = _groq_keys()
    while len(accumulated) < count and groq_keys:
        needed = min(count - len(accumulated), 10)
        prompt = _build_prompt(topic, needed, style)
        groq_ok = False
        for key_index in range(len(groq_keys)):
            try:
                raw_text = await asyncio.to_thread(_groq_generate, prompt, key_index)
                raw = _safe_parse_json(raw_text)
                valid = _validate(raw, needed)
                if len(valid) < needed:
                    raise ValueError(f"Groq returned {len(valid)}/{needed} valid questions")
                accumulated.extend(valid)
                groq_ok = True
                break
            except Exception as exc:
                errors.append(f"[groq key {key_index + 1}]: {str(exc)[:180]}")
        if not groq_ok:
            break

    if len(accumulated) < count:
        last = errors[-1] if errors else "unknown AI error"
        raise RuntimeError(
            f"AI could not generate enough questions ({len(accumulated)}/{count}). "
            f"Last error: {last}"
        )
    return accumulated[:count]


# (rest of file unchanged from your current quiz logic)


def start_session(
    user_id: int,
    chat_id: int,
    questions: list[dict],
    topic: str,
    style: str = "quiz",
    timer: int = POLL_OPEN_PERIOD,
) -> dict:
    old = active_sessions.pop(user_id, None)
    if old and old.get("advance_job") and not old["advance_job"].done():
        old["advance_job"].cancel()
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
        task = asyncio.create_task(
            _advance_after_timeout(bot, user_id, session["current_idx"])
        )
        session["advance_job"] = task


async def handle_poll_answer(
    bot: Bot,
    user_id: int,
    poll_id: str,
    selected_option: int,
    *,
    username: str = "",
    name: str = "Telegram User",
):
    session = active_sessions.get(user_id)
    if not session or session["current_poll_id"] != poll_id or session["answered_current"]:
        return

    session["answered_current"] = True
    q = session["questions"][session["current_idx"]]

    is_correct = selected_option == q["correct_index"]
    if is_correct:
        session["correct"] += 1
        session["score"] += CORRECT_SCORE
    else:
        session["wrong"] += 1
        session["score"] += WRONG_SCORE

    # Supabase leaderboard sync (best-effort; never break quiz flow)
    try:
        await asyncio.to_thread(
            supabase_sync.record_answer,
            telegram_user_id=int(user_id),
            chat_id=int(session["chat_id"]),
            username=username or "",
            name=name or "Telegram User",
            is_correct=bool(is_correct),
            topic=str(session.get("topic") or "Quiz"),
        )
    except Exception as exc:
        logger.warning("Supabase record_answer failed: %s", str(exc)[:200])


async def finish_quiz(bot: Bot, session: dict):
    user_id = session["user_id"]
    chat_id = session["chat_id"]

    poll_to_user.pop(session.get("current_poll_id", ""), None)
    active_sessions.pop(user_id, None)

    save_quiz_result(
        user_id=user_id,
        chat_id=chat_id,
        correct=session["correct"],
        wrong=session["wrong"],
        unanswered=session["unanswered"],
        score=session["score"],
        topic=session["topic"],
        total=session["total"],
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


# Group quiz functions

def start_group_session(chat_id: int, questions: list[dict], topic: str, timer: int) -> dict:
    old = group_sessions.pop(chat_id, None)
    if old and old.get("advance_job") and not old["advance_job"].done():
        old["advance_job"].cancel()
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

    q_text = f"📚 {session['topic']} — ❓ Q{idx + 1}/{total}\n\n{q['question']}"
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


async def handle_group_poll_answer(
    bot: Bot,
    chat_id: int,
    user_id: int,
    name: str,
    username: str,
    poll_id: str,
    selected_option: int,
):
    session = group_sessions.get(chat_id)
    if not session or session.get("current_poll_id") != poll_id:
        return
    if user_id in session["answered_users"]:
        return
    session["answered_users"].add(user_id)
    ensure_user(user_id, chat_id, username, name)
    if user_id not in session["user_scores"]:
        session["user_scores"][user_id] = {
            "name": name,
            "username": username,
            "correct": 0,
            "wrong": 0,
            "score": 0,
        }

    stats = session["user_scores"][user_id]
    is_correct = selected_option == session["current_correct"]
    if is_correct:
        stats["correct"] += 1
        stats["score"] += CORRECT_SCORE
    else:
        stats["wrong"] += 1
        stats["score"] += WRONG_SCORE

    try:
        await asyncio.to_thread(
            supabase_sync.record_answer,
            telegram_user_id=int(user_id),
            chat_id=int(chat_id),
            username=username or "",
            name=name or "Telegram User",
            is_correct=bool(is_correct),
            topic=str(session.get("topic") or "Quiz"),
        )
    except Exception as exc:
        logger.warning("Supabase record_answer (group) failed: %s", str(exc)[:200])


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
        task = asyncio.create_task(
            _advance_group_after_timeout(bot, chat_id, session["current_idx"])
        )
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
            user_id=user_id,
            chat_id=chat_id,
            correct=stats["correct"],
            wrong=stats["wrong"],
            unanswered=unanswered,
            score=stats["score"],
            topic=session["topic"],
            total=total,
        )

    if session["user_scores"]:
        sorted_users = sorted(
            session["user_scores"].items(), key=lambda x: x[1]["score"], reverse=True
        )
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        lines = [
            "📅 *Daily Quiz Complete!*\n",
            f"📖 Topic: *{session['topic']}* | Questions: `{total}`",
            "━━━━━━━━━━━━━━━━━━",
        ]
        for i, (uid, s) in enumerate(sorted_users[:10]):
            medal = medals.get(i, f"{i + 1}.")
            dname = s["name"] or s["username"] or "User"
            lines.append(
                f"{medal} *{dname}* — `{s['score']:+}` (✅{s['correct']} ❌{s['wrong']})"
            )
        lines.append("━━━━━━━━━━━━━━━━━━")
    else:
        lines = [
            "📅 *Daily Quiz Complete!*\n",
            f"📖 Topic: *{session['topic']}*",
            "\n_No one answered this quiz._",
        ]

    try:
        await bot.send_message(
            chat_id=chat_id, text="\n".join(lines), parse_mode=ParseMode.MARKDOWN
        )
    except TelegramError as exc:
        logger.error("Group result card failed: %s", exc)

    logger.info("Group quiz finished: chat=%s", chat_id)
