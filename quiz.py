"""
Quiz session management + Gemini question generation.

Key design: probes BOTH v1beta (newer models) and v1 (stable models) endpoints
at startup so we always find a working model regardless of which tier/quota the
API key has access to.
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

from config import (CORRECT_SCORE, GEMINI_API_KEY, POLL_OPEN_PERIOD,
                    UNANSWERED_SCORE, WRONG_SCORE)
from database import ensure_user, get_rank, save_quiz_result

logger = logging.getLogger(__name__)

# ── Model candidate list (model_name, api_version) ───────────────────────────
# Ordered most-likely-to-work first.  Both v1beta (new) and v1 (stable) are
# tried so the bot works regardless of which models the API key can reach.

class ModelSlot(NamedTuple):
    model: str
    api_version: str   # "v1beta" or "v1"

CANDIDATE_SLOTS: list[ModelSlot] = [
    # ── Confirmed working on this key (probed 2026-07-29) ─────────────────
    # All use v1beta; v1 endpoint returns 404 for all models on this key.
    ModelSlot("gemini-flash-latest",      "v1beta"),   # alias → always tracks latest flash
    ModelSlot("gemini-flash-lite-latest", "v1beta"),   # lighter / more quota-generous
    ModelSlot("gemini-3.5-flash-lite",    "v1beta"),
    ModelSlot("gemini-3.1-flash-lite",    "v1beta"),
    ModelSlot("gemini-3.5-flash",         "v1beta"),
    ModelSlot("gemini-3.6-flash",         "v1beta"),
    ModelSlot("gemini-3-flash-preview",   "v1beta"),
    ModelSlot("gemma-4-31b-it",           "v1beta"),
    ModelSlot("gemma-4-26b-a4b-it",       "v1beta"),
    # ── Known quota-exhausted — keep as last resort if quota resets ────────
    ModelSlot("gemini-2.0-flash-lite",    "v1beta"),
    ModelSlot("gemini-2.0-flash",         "v1beta"),
    ModelSlot("gemini-2.0-flash-001",     "v1beta"),
]

# ── Runtime state ─────────────────────────────────────────────────────────────
_clients: dict[str, genai.Client] = {}   # api_version -> Client
# Pre-set to the confirmed working model so the bot is immediately usable.
# generate_questions() falls back through CANDIDATE_SLOTS if this ever fails.
_working_slot: ModelSlot = ModelSlot("gemini-flash-latest", "v1beta")


def _get_client(api_version: str = "v1beta") -> genai.Client:
    if api_version not in _clients:
        api_key = GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not set.")
        _clients[api_version] = genai.Client(
            api_key=api_key,
            http_options=genai_types.HttpOptions(api_version=api_version),
        )
        logger.info("Created Gemini client for endpoint: %s", api_version)
    return _clients[api_version]


def _parse_retry_after(exc: Exception) -> float:
    """Extract retry-after seconds from a 429 error string."""
    msg = str(exc)
    m = re.search(r"retryDelay['\": ]+(\d+\.?\d*)s", msg)
    if m:
        return float(m.group(1))
    m = re.search(r"retry in (\d+\.?\d*)s", msg, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return 60.0


def _is_quota_error(exc: Exception) -> bool:
    msg = str(exc)
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg


def _is_not_found(exc: Exception) -> bool:
    msg = str(exc)
    return "404" in msg or "NOT_FOUND" in msg


def verify_gemini_key() -> bool:
    """
    Validate the API key by listing models (no generation call = no quota used).
    The working slot is already pre-set to gemini-flash-latest which was confirmed
    working. generate_questions() will auto-fallback if it ever fails.
    """
    try:
        client = _get_client("v1beta")
        models = list(client.models.list())
        gc_names = [
            m.name.replace("models/", "")
            for m in models
            if m.supported_actions and "generateContent" in m.supported_actions
        ]
        logger.info(
            "✅ Gemini key valid. %d models with generateContent support. "
            "Default model: %s",
            len(gc_names), _working_slot.model
        )
        logger.info("Available generateContent models: %s", gc_names[:15])
        return True
    except Exception as exc:
        logger.error("❌ Gemini key validation failed: %s", exc)
        return False


def _get_slot() -> ModelSlot:
    return _working_slot


# ── in-memory session store ───────────────────────────────────────────────────
active_sessions: dict[int, dict] = {}   # user_id  → personal quiz session
poll_to_user:    dict[str, int]  = {}   # poll_id  → user_id  (personal quizzes)
group_sessions:  dict[int, dict] = {}   # chat_id  → group quiz session
poll_to_chat:    dict[str, int]  = {}   # poll_id  → chat_id  (group/scheduled quizzes)


# ── Question generation ───────────────────────────────────────────────────────

def _build_prompt(topic: str, count: int, style: str = "quiz") -> str:
    pyq_hint = (
        " Model the questions after Indian competitive exam PYQ style "
        "(NEET/JEE/UPSC), focusing on conceptual depth and real exam patterns."
        if style == "pyq" else ""
    )
    return textwrap.dedent(f"""
        Generate exactly {count} multiple-choice questions about: "{topic}".{pyq_hint}

        MANDATORY RULES — follow all of them strictly:
        1. Each question MUST have EXACTLY 4 answer options (no more, no less).
        2. correct_index MUST be 0, 1, 2, or 3 (0-based index of the correct option).
        3. All {count} questions must be completely different — no repetition.
        4. Output ONLY a JSON array with no markdown, no code fences, no explanation.
        5. The response MUST start with '[' and end with ']'.
        6. Do NOT include any text before '[' or after ']'.

        JSON format:
        [
          {{
            "question": "Question text here?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_index": 0
          }}
        ]

        Start immediately with '['. Produce exactly {count} items.
    """).strip()


def _safe_parse_json(text: str) -> list:
    """Robustly extract a JSON array from Gemini response text."""
    if not text:
        raise ValueError("Empty response from Gemini")
    text = text.strip()
    # Strip markdown code fences if present
    text = re.sub(r"^```[a-zA-Z]*\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s*```\s*$", "", text, flags=re.MULTILINE)
    text = text.strip()
    # Find outermost JSON array
    start = text.find("[")
    end   = text.rfind("]")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON array found. Response: {text[:200]!r}")
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON decode failed: {exc}. Snippet: {text[start:start+200]!r}") from exc


def _validate(raw: list, needed: int) -> list[dict]:
    """Return up to `needed` structurally valid question dicts."""
    valid: list[dict] = []
    for i, q in enumerate(raw):
        if not isinstance(q, dict):
            continue
        if not str(q.get("question", "")).strip():
            continue
        opts = q.get("options", [])
        if not isinstance(opts, list) or len(opts) != 4:
            logger.debug("Q%d: bad options count=%d", i, len(opts) if isinstance(opts, list) else -1)
            continue
        try:
            cidx = int(q["correct_index"])
        except (KeyError, TypeError, ValueError):
            logger.debug("Q%d: bad correct_index", i)
            continue
        if cidx not in (0, 1, 2, 3):
            logger.debug("Q%d: correct_index %d out of range", i, cidx)
            continue
        valid.append({
            "question":      str(q["question"]).strip(),
            "options":       [str(o).strip() for o in opts],
            "correct_index": cidx,
        })
        if len(valid) >= needed:
            break
    return valid


def _sync_generate(slot: ModelSlot, prompt: str) -> str:
    """Blocking Gemini call — run inside asyncio.to_thread."""
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


async def generate_questions(topic: str, count: int,
                             style: str = "quiz") -> list[dict]:
    """
    Return exactly `count` validated MCQ questions.

    Strategy:
    - Start with the known-working slot from verify_gemini_key().
    - On 429 (quota), wait the retry-after delay then try the NEXT slot.
    - On 404 or parse failure, move to the next slot immediately.
    - Accumulate valid questions across attempts until we have `count`.
    - Give up after trying every slot twice.
    """
    global _working_slot

    # Build an ordered list of slots to try, starting with the known-good one
    base_slot = _get_slot()
    remaining = [base_slot] + [s for s in CANDIDATE_SLOTS if s != base_slot]
    # Allow two full passes through the list
    slots_queue = remaining * 2

    accumulated: list[dict] = []
    last_exc: Exception | None = None

    for attempt, slot in enumerate(slots_queue, start=1):
        needed = count - len(accumulated)
        if needed <= 0:
            break

        prompt  = _build_prompt(topic, needed, style)
        label   = f"#{attempt} [{slot.api_version}/{slot.model}]"
        logger.info("Generation attempt %s — need %d more questions", label, needed)

        try:
            raw_text = await asyncio.to_thread(_sync_generate, slot, prompt)
        except Exception as exc:
            last_exc = exc
            logger.error("Attempt %s FAILED: %s", label, exc)

            if _is_quota_error(exc):
                wait = min(_parse_retry_after(exc), 65)
                logger.warning(
                    "Quota error on %s/%s — waiting %.0fs, then trying next model",
                    slot.api_version, slot.model, wait
                )
                await asyncio.sleep(wait)
            elif _is_not_found(exc):
                logger.warning("Model %s not found on %s — skipping",
                               slot.model, slot.api_version)
                # no sleep needed
            else:
                await asyncio.sleep(2)
            continue

        # Parse + validate
        try:
            raw = _safe_parse_json(raw_text)
        except ValueError as parse_exc:
            last_exc = parse_exc
            logger.warning("Attempt %s parse error: %s", label, parse_exc)
            await asyncio.sleep(1)
            continue

        valid = _validate(raw, needed)
        accumulated.extend(valid)
        logger.info("Attempt %s: got %d/%d valid (total %d/%d)",
                    label, len(valid), needed, len(accumulated), count)

        # Update the working slot if this one succeeded
        if valid:
            _working_slot = slot

        if len(accumulated) >= count:
            break

        await asyncio.sleep(1)

    if not accumulated:
        quota_hint = (
            "\n\nYour Gemini API key has no available quota. "
            "Check https://ai.google.dev/rate-limits or wait for the quota to reset."
            if last_exc and _is_quota_error(last_exc) else ""
        )
        raise RuntimeError(
            f"Failed to generate questions after {len(slots_queue)} attempts."
            f"{quota_hint}\nLast error: {last_exc}"
        )

    if len(accumulated) < count:
        logger.warning("Best effort: returning %d/%d questions",
                       len(accumulated), count)
    return accumulated[:count]


# ── Session management ────────────────────────────────────────────────────────

def start_session(user_id: int, chat_id: int, questions: list[dict],
                  topic: str, style: str = "quiz",
                  timer: int = POLL_OPEN_PERIOD) -> dict:
    # Cleanly discard any stale session so old state never leaks in
    old = active_sessions.pop(user_id, None)
    if old:
        if old.get("current_poll_id"):
            poll_to_user.pop(old["current_poll_id"], None)
        job = old.get("advance_job")
        if job and not job.done():
            job.cancel()

    session: dict = {
        "user_id":          user_id,
        "chat_id":          chat_id,
        "topic":            topic,
        "style":            style,
        "questions":        questions,
        "total":            len(questions),
        "current_idx":      0,
        "correct":          0,
        "wrong":            0,
        "unanswered":       0,
        "score":            0,
        "timer":            timer,
        "start_time":       datetime.utcnow(),
        "current_poll_id":  None,
        "answered_current": False,
        "advance_job":      None,
    }
    active_sessions[user_id] = session
    return session


def end_session(user_id: int):
    session = active_sessions.pop(user_id, None)
    if session and session.get("current_poll_id"):
        poll_to_user.pop(session["current_poll_id"], None)
    return session


# ── Poll sending & auto-advance ───────────────────────────────────────────────

async def send_question(bot: Bot, session: dict):
    idx     = session["current_idx"]
    q       = session["questions"][idx]
    total   = session["total"]
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
        session["current_poll_id"]  = poll_id
        session["answered_current"] = False
        poll_to_user[poll_id]       = user_id
        logger.info("Poll sent: user=%d q=%d/%d poll=%s",
                    user_id, idx + 1, total, poll_id)
    except TelegramError as exc:
        logger.error("Poll send failed (user=%d q=%d): %s", user_id, idx + 1, exc)


async def _advance_after_timeout(bot: Bot, user_id: int, question_index: int):
    """Auto-advances after session timer + 1 seconds."""
    session = active_sessions.get(user_id)
    timer   = session.get("timer", POLL_OPEN_PERIOD) if session else POLL_OPEN_PERIOD
    await asyncio.sleep(timer + 1)

    session = active_sessions.get(user_id)
    if not session or session["current_idx"] != question_index:
        return
    if not session["answered_current"]:
        session["unanswered"] += 1
        session["score"]      += UNANSWERED_SCORE
        logger.info("Q%d unanswered — user=%d", question_index + 1, user_id)

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


async def handle_poll_answer(bot: Bot, user_id: int, poll_id: str,
                              selected_option: int):
    """Called by PollAnswerHandler in main.py."""
    session = active_sessions.get(user_id)
    if not session:
        return
    if session["current_poll_id"] != poll_id or session["answered_current"]:
        return

    session["answered_current"] = True
    q = session["questions"][session["current_idx"]]

    if selected_option == q["correct_index"]:
        session["correct"] += 1
        session["score"]   += CORRECT_SCORE
        result = "CORRECT"
    else:
        session["wrong"] += 1
        session["score"] += WRONG_SCORE
        result = "WRONG"

    logger.info("Answer: user=%d q=%d %s score=%+d",
                user_id, session["current_idx"] + 1, result, session["score"])


# ── Quiz finish ───────────────────────────────────────────────────────────────

async def finish_quiz(bot: Bot, session: dict):
    user_id = session["user_id"]
    chat_id = session["chat_id"]

    poll_to_user.pop(session.get("current_poll_id", ""), None)
    active_sessions.pop(user_id, None)

    save_quiz_result(
        user_id    = user_id,
        chat_id    = chat_id,
        correct    = session["correct"],
        wrong      = session["wrong"],
        unanswered = session["unanswered"],
        score      = session["score"],
        topic      = session["topic"],
        total      = session["total"],
    )

    rank     = get_rank(user_id, chat_id)
    duration = (datetime.utcnow() - session["start_time"]).seconds
    mins, secs = divmod(duration, 60)
    answered  = session["correct"] + session["wrong"]
    accuracy  = (f"{session['correct'] / answered * 100:.1f}%"
                 if answered > 0 else "0.0%")

    text = (
        f"🎉 *QUIZ COMPLETE!*\n\n"
        f"📖 Topic: *{session['topic']}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📊 Total:       `{session['total']}`\n"
        f"✅ Correct:     `{session['correct']}`\n"
        f"❌ Wrong:       `{session['wrong']}`\n"
        f"⏭ Unanswered:  `{session['unanswered']}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⭐ Score:       `{session['score']:+}`\n"
        f"🎯 Accuracy:    `{accuracy}`\n"
        f"🏅 Rank:        `#{rank}`\n"
        f"⏱ Time:        `{mins}m {secs}s`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"_(+4 correct / −1 wrong / 0 unanswered)_"
    )
    try:
        await bot.send_message(chat_id=chat_id, text=text,
                               parse_mode=ParseMode.MARKDOWN)
        logger.info("Result card sent: user=%d score=%+d rank=#%d",
                    user_id, session["score"], rank)
    except TelegramError as exc:
        logger.error("Result card failed (user=%d): %s", user_id, exc)


# ── Group / scheduled quiz session management ─────────────────────────────────

def start_group_session(chat_id: int, questions: list[dict],
                        topic: str, timer: int) -> dict:
    """Create (or replace) a group quiz session for the given chat."""
    old = group_sessions.pop(chat_id, None)
    if old:
        poll_to_chat.pop(old.get("current_poll_id", ""), None)
        job = old.get("advance_job")
        if job and not job.done():
            job.cancel()

    session: dict = {
        "chat_id":          chat_id,
        "topic":            topic,
        "questions":        questions,
        "total":            len(questions),
        "current_idx":      0,
        "timer":            timer,
        "current_poll_id":  None,
        "current_correct":  None,
        "advance_job":      None,
        "answered_users":   set(),        # user_ids who answered current question
        "user_scores":      {},           # user_id → {name, username, correct, wrong, score}
    }
    group_sessions[chat_id] = session
    return session


async def send_group_question(bot: Bot, session: dict):
    idx     = session["current_idx"]
    q       = session["questions"][idx]
    total   = session["total"]
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
        poll_id = msg.poll.id
        session["current_poll_id"] = poll_id
        session["current_correct"] = q["correct_index"]
        session["answered_users"]  = set()
        poll_to_chat[poll_id]      = chat_id
        logger.info("Group poll sent: chat=%d q=%d/%d poll=%s",
                    chat_id, idx + 1, total, poll_id)
    except TelegramError as exc:
        logger.error("Group poll send failed (chat=%d q=%d): %s",
                     chat_id, idx + 1, exc)


async def handle_group_poll_answer(bot: Bot, chat_id: int,
                                   user_id: int, name: str, username: str,
                                   poll_id: str, selected_option: int):
    """Called by on_poll_answer for group/scheduled quiz polls."""
    session = group_sessions.get(chat_id)
    if not session or session.get("current_poll_id") != poll_id:
        return

    # Each user may answer only once per question
    if user_id in session["answered_users"]:
        return
    session["answered_users"].add(user_id)
    ensure_user(user_id, chat_id, username, name)
    if user_id not in session["user_scores"]:
        session["user_scores"][user_id] = {
            "name": name, "username": username,
            "correct": 0, "wrong": 0, "score": 0,
        }

    stats = session["user_scores"][user_id]
    if selected_option == session["current_correct"]:
        stats["correct"] += 1
        stats["score"]   += CORRECT_SCORE
    else:
        stats["wrong"] += 1
        stats["score"] += WRONG_SCORE


async def _advance_group_after_timeout(bot: Bot, chat_id: int, question_index: int):
    """Auto-advances the group session after timer + 1 seconds."""
    session = group_sessions.get(chat_id)
    timer   = session.get("timer", POLL_OPEN_PERIOD) if session else POLL_OPEN_PERIOD
    await asyncio.sleep(timer + 1)

    session = group_sessions.get(chat_id)
    if not session or session["current_idx"] != question_index:
        return

    try:
        await bot.send_message(
            chat_id=chat_id,
            text="⏰ Time's up! Moving to the next question."
        )
    except TelegramError:
        pass

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
    """Save scores for all participants and send a group result card."""
    chat_id = session["chat_id"]

    poll_to_chat.pop(session.get("current_poll_id", ""), None)
    group_sessions.pop(chat_id, None)

    total = session["total"]
    for user_id, stats in session["user_scores"].items():
        ensure_user(user_id, chat_id, stats["username"], stats["name"])
        unanswered = total - stats["correct"] - stats["wrong"]
        save_quiz_result(
            user_id    = user_id,
            chat_id    = chat_id,
            correct    = stats["correct"],
            wrong      = stats["wrong"],
            unanswered = unanswered,
            score      = stats["score"],
            topic      = session["topic"],
            total      = total,
        )

    # Build result card
    if session["user_scores"]:
        sorted_users = sorted(
            session["user_scores"].items(),
            key=lambda x: x[1]["score"], reverse=True
        )
        medals = {0: "🥇", 1: "🥈", 2: "🥉"}
        lines  = [
            f"📅 *Daily Quiz Complete!*\n",
            f"📖 Topic: *{session['topic']}* | Questions: `{total}`",
            "━━━━━━━━━━━━━━━━━━",
        ]
        for i, (uid, s) in enumerate(sorted_users[:10]):
            medal = medals.get(i, f"{i + 1}.")
            dname = s["name"] or s["username"] or "User"
            lines.append(
                f"{medal} *{dname}* — `{s['score']:+}` "
                f"(✅{s['correct']} ❌{s['wrong']})"
            )
        lines.append("━━━━━━━━━━━━━━━━━━")
    else:
        lines = [
            f"📅 *Daily Quiz Complete!*\n",
            f"📖 Topic: *{session['topic']}*",
            "\n_No one answered this quiz._",
        ]

    try:
        await bot.send_message(
            chat_id=chat_id,
            text="\n".join(lines),
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.info("Group result card sent: chat=%d participants=%d",
                    chat_id, len(session["user_scores"]))
    except TelegramError as exc:
        logger.error("Group result card failed (chat=%d): %s", chat_id, exc)
