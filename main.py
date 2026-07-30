"""
Telegram Quiz Bot — main entry point.
python-telegram-bot v21+
"""
import asyncio
import json
import logging
import re
import sys

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, ContextTypes,
                           MessageHandler, PollAnswerHandler, filters)

import config
import database
import leaderboard
import quiz as quiz_module
import scheduler as sched_module
from quiz import verify_gemini_key

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── Help text ─────────────────────────────────────────────────────────────────
HELP_TEXT = """
🤖 *Telegram Quiz Bot*

*Commands:*
/quiz `<topic> <number>` — Start a quiz
/pyq `<topic> <number>` — PYQ-style quiz (NEET/JEE/UPSC)
/leaderboard — Top 10 players in this group
/myrank — Your stats & rank in this group
/toptoday — Today's top scores in this group
/resetscore — Reset your score in this group
/timer `<15|30|45|60>` — Set quiz timer for this group
/schedule `<topic> <number>` — Daily quiz at 9 PM IST
/scheduleoff — Stop the daily quiz
/schedulelist — View current schedule
/help — This message

*Examples:*
`/quiz Physics 10`
`/quiz Biology Chapter 2 5`
`/pyq NEET Chemistry 15`
`/timer 30`
`/schedule Biology 10`

🎙 *Voice:* Send a voice message like _"Biology 10 questions"_

*Scoring:* ✅ Correct +4 | ❌ Wrong −1 | ⏭ Skip 0

*Topics:* Biology, Physics, Chemistry, Maths, History,
Geography, Polity, Economics, English, Hindi, GK,
Current Affairs, NEET, JEE, Board Exams, and more!
""".strip()


# ── Command handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    await update.message.reply_text(
        f"👋 Welcome, *{user.first_name}*!\n\n{HELP_TEXT}",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)


async def _start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE,
                      style: str):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    args    = context.args or []

    cmd = "/quiz" if style == "quiz" else "/pyq"
    if len(args) < 2:
        await update.message.reply_text(
            f"Usage: `{cmd} <topic> <number>`\nExample: `{cmd} Physics 10`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    try:
        count = int(args[-1])
    except ValueError:
        await update.message.reply_text(
            f"❗ Last argument must be a number.\nExample: `{cmd} Physics 10`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not (1 <= count <= 50):
        await update.message.reply_text(
            "❗ Number of questions must be between 1 and 50."
        )
        return

    topic = " ".join(args[:-1])

    if user.id in quiz_module.active_sessions:
        await update.message.reply_text(
            "⚠️ You already have an active quiz running. "
            "Please finish it before starting a new one."
        )
        return

    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    timer = database.get_group_timer(chat_id)

    wait_msg = await update.message.reply_text(
        f"⏳ Generating *{count}* questions on *{topic}*… Please wait.",
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        questions = await quiz_module.generate_questions(topic, count, style)
    except Exception as exc:
        logger.error("Question generation failed for user %d: %s", user.id, exc)
        error_str = str(exc)
        if "quota" in error_str.lower() or "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
            user_msg = (
                "❌ *Gemini API quota exceeded.*\n\n"
                "The bot's AI quota is exhausted for this model right now.\n"
                "Please try again in a few minutes, or contact the bot admin."
            )
        else:
            user_msg = (
                "❌ Failed to generate questions. Please try again later.\n"
                f"_Error: {error_str[:150]}_"
            )
        await wait_msg.edit_text(user_msg, parse_mode=ParseMode.MARKDOWN)
        return

    if not questions:
        await wait_msg.edit_text(
            "❌ Could not generate any questions. Try a different topic."
        )
        return

    actual = len(questions)
    if actual < count:
        notice = f"⚠️ Generated {actual}/{count} questions — starting with available ones.\n\n"
    else:
        notice = ""
        try:
            await wait_msg.delete()
        except Exception:
            pass

    session = quiz_module.start_session(user.id, chat_id, questions, topic, style, timer)

    label = "📝 PYQ Quiz" if style == "pyq" else "📚 Quiz"
    await update.message.reply_text(
        f"{notice}{label} starting!\n"
        f"*Topic:* {topic}\n"
        f"*Questions:* {actual}\n\n"
        f"⏱ Each question has a *{timer}s* timer.\n"
        f"Scoring: ✅ +4 | ❌ −1 | ⏭ 0",
        parse_mode=ParseMode.MARKDOWN,
    )

    bot = context.bot
    await quiz_module.send_question(bot, session)

    task = asyncio.create_task(
        quiz_module._advance_after_timeout(bot, user.id, 0)
    )
    session["advance_job"] = task


async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _start_quiz(update, context, style="quiz")


async def cmd_pyq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _start_quiz(update, context, style="pyq")


async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    await update.message.reply_text(
        leaderboard.format_leaderboard(chat_id), parse_mode=ParseMode.MARKDOWN
    )


async def cmd_myrank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    await update.message.reply_text(
        leaderboard.format_my_rank(user.id, chat_id), parse_mode=ParseMode.MARKDOWN
    )


async def cmd_toptoday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    await update.message.reply_text(
        leaderboard.format_today_top(chat_id), parse_mode=ParseMode.MARKDOWN
    )


async def cmd_resetscore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    database.reset_score(user.id, chat_id)
    await update.message.reply_text(
        f"🔄 *{user.first_name}*, your score in this group has been reset to zero.",
        parse_mode=ParseMode.MARKDOWN,
    )


# ── Feature 1: Per-group timer ────────────────────────────────────────────────

async def cmd_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    args    = context.args or []

    valid = {15, 30, 45, 60}
    current = database.get_group_timer(chat_id)

    if not args or not args[0].isdigit() or int(args[0]) not in valid:
        await update.message.reply_text(
            f"⏱ *Quiz Timer*\n\n"
            f"Current timer for this group: *{current}s*\n\n"
            f"Usage: `/timer 15` | `/timer 30` | `/timer 45` | `/timer 60`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    seconds = int(args[0])
    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    database.set_group_timer(chat_id, seconds)
    await update.message.reply_text(
        f"✅ Quiz timer set to *{seconds} seconds* for this group.\n"
        f"All future `/quiz` and `/pyq` commands will use this timer.",
        parse_mode=ParseMode.MARKDOWN,
    )


# ── Feature 2: Voice message support ─────────────────────────────────────────

async def _transcribe_and_extract(voice_bytes: bytes) -> tuple[str, int]:
    """
    Send voice audio to Gemini inline, ask it to transcribe and extract
    the quiz topic + question count.  Returns (topic, count).
    Supports Hindi and English.
    """
    from google.genai import types as genai_types

    slot   = quiz_module._working_slot
    client = quiz_module._get_client(slot.api_version)

    prompt = (
        "This is a voice message requesting a quiz.\n"
        "Transcribe the audio (supports Hindi and English) and extract:\n"
        "1. The quiz topic (e.g. 'Biology', 'Human Reproduction', 'Physics Chapter 2')\n"
        "2. The number of questions (default 10 if not mentioned; max 50)\n\n"
        "Reply with ONLY valid JSON — no markdown, no explanation:\n"
        '{"topic": "...", "count": N, "transcript": "..."}'
    )

    part = genai_types.Part(
        inline_data=genai_types.Blob(
            mime_type="audio/ogg",
            data=voice_bytes,
        )
    )

    def _call():
        return client.models.generate_content(
            model=slot.model,
            contents=[part, prompt],
            config=genai_types.GenerateContentConfig(
                max_output_tokens=300,
                temperature=0.1,
            ),
        )

    resp = await asyncio.to_thread(_call)
    text = resp.text or ""

    m = re.search(r"\{.*?\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"Gemini returned no JSON: {text[:200]!r}")

    data  = json.loads(m.group())
    topic = str(data.get("topic", "General Knowledge")).strip() or "General Knowledge"
    count = max(1, min(int(data.get("count", 10)), 50))
    return topic, count


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle Telegram voice messages — transcribe via Gemini, then start quiz."""
    user    = update.effective_user
    chat_id = update.effective_chat.id

    if user.id in quiz_module.active_sessions:
        await update.message.reply_text(
            "⚠️ You already have an active quiz. Please finish it first."
        )
        return

    wait_msg = await update.message.reply_text("🎙 Processing your voice message…")

    # Download voice file (Telegram sends OGG/Opus)
    try:
        voice   = update.message.voice
        tg_file = await context.bot.get_file(voice.file_id)
        raw     = await tg_file.download_as_bytearray()
        topic, count = await _transcribe_and_extract(bytes(raw))
    except Exception as exc:
        logger.error("Voice processing failed for user %d: %s", user.id, exc)
        await wait_msg.edit_text(
            "❌ Could not understand the voice message.\n"
            "Please try again or type `/quiz <topic> <number>`.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await wait_msg.edit_text(
        f"🎙 Got it!\n*Topic:* {topic}\n*Questions:* {count}\n\n⏳ Generating quiz…",
        parse_mode=ParseMode.MARKDOWN,
    )

    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    timer = database.get_group_timer(chat_id)

    try:
        questions = await quiz_module.generate_questions(topic, count, "quiz")
    except Exception as exc:
        await wait_msg.edit_text(
            f"❌ Failed to generate questions: {str(exc)[:150]}",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not questions:
        await wait_msg.edit_text("❌ Could not generate questions. Try a different topic.")
        return

    actual = len(questions)
    try:
        await wait_msg.delete()
    except Exception:
        pass

    session = quiz_module.start_session(user.id, chat_id, questions, topic, "quiz", timer)

    await update.message.reply_text(
        f"🎙 *Voice Quiz Starting!*\n"
        f"*Topic:* {topic}\n"
        f"*Questions:* {actual}\n\n"
        f"⏱ Timer: *{timer}s* per question\n"
        f"Scoring: ✅ +4 | ❌ −1 | ⏭ 0",
        parse_mode=ParseMode.MARKDOWN,
    )

    await quiz_module.send_question(context.bot, session)
    task = asyncio.create_task(
        quiz_module._advance_after_timeout(context.bot, user.id, 0)
    )
    session["advance_job"] = task


# ── Feature 3: Daily scheduled quiz ──────────────────────────────────────────

async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    args    = context.args or []

    if len(args) < 2:
        await update.message.reply_text(
            "Usage: `/schedule <topic> <number>`\nExample: `/schedule Biology 10`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    try:
        count = int(args[-1])
    except ValueError:
        await update.message.reply_text("❗ Last argument must be a number.")
        return

    if not (1 <= count <= 50):
        await update.message.reply_text("❗ Question count must be 1–50.")
        return

    topic = " ".join(args[:-1])
    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    sched_module.add_schedule(chat_id, topic, count)

    timer = database.get_group_timer(chat_id)
    await update.message.reply_text(
        f"✅ *Daily Quiz Scheduled!*\n\n"
        f"📖 Topic: *{topic}*\n"
        f"❓ Questions: *{count}*\n"
        f"⏱ Timer: *{timer}s* per question\n"
        f"🕘 Time: *9:00 PM IST* every day\n\n"
        f"Use /scheduleoff to stop.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def cmd_scheduleoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id  = update.effective_chat.id
    existing = database.get_schedule(chat_id)
    if not existing:
        await update.message.reply_text("❌ No active schedule for this group.")
        return
    sched_module.remove_schedule(chat_id)
    await update.message.reply_text(
        "✅ Daily quiz schedule has been turned off for this group."
    )


async def cmd_schedulelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id  = update.effective_chat.id
    existing = database.get_schedule(chat_id)
    if not existing:
        await update.message.reply_text(
            "📋 No active schedule for this group.\n"
            "Use `/schedule <topic> <number>` to set one.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    timer = database.get_group_timer(chat_id)
    await update.message.reply_text(
        f"📋 *Active Schedule*\n\n"
        f"📖 Topic: *{existing['topic']}*\n"
        f"❓ Questions: *{existing['count']}*\n"
        f"⏱ Timer: *{timer}s* per question\n"
        f"🕘 Time: *9:00 PM IST* (daily)",
        parse_mode=ParseMode.MARKDOWN,
    )


# ── Poll answer handler (personal + group quizzes) ────────────────────────────

async def on_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer  = update.poll_answer
    poll_id = answer.poll_id
    user_id = answer.user.id

    # ── Personal quiz ──────────────────────────────────────────────────────
    if poll_id in quiz_module.poll_to_user:
        if quiz_module.poll_to_user[poll_id] != user_id:
            return
        if not answer.option_ids:
            return  # retracted
        await quiz_module.handle_poll_answer(
            context.bot, user_id, poll_id, answer.option_ids[0]
        )
        return

    # ── Group / scheduled quiz ─────────────────────────────────────────────
    if poll_id in quiz_module.poll_to_chat:
        if not answer.option_ids:
            return  # retracted
        chat_id  = quiz_module.poll_to_chat[poll_id]
        name     = answer.user.full_name or answer.user.first_name or "User"
        username = answer.user.username or ""
        await quiz_module.handle_group_poll_answer(
            context.bot,
            chat_id, user_id, name, username,
            poll_id, answer.option_ids[0],
        )


# ── Scheduler post-init ───────────────────────────────────────────────────────

async def _post_init(application: Application):
    sched_module.init_scheduler(application)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set — exiting.")
        sys.exit(1)
    if not config.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY not set — exiting.")
        sys.exit(1)

    database.init_db()

    logger.info("Validating Gemini API key …")
    ok = verify_gemini_key()
    if ok:
        logger.info("✅ Gemini ready — default model: %s",
                    quiz_module._working_slot.model)
    else:
        logger.warning(
            "⚠️  Gemini key validation failed. "
            "Quiz commands may fail if the key is invalid."
        )

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    # Existing commands
    app.add_handler(CommandHandler("start",        cmd_start))
    app.add_handler(CommandHandler("help",         cmd_help))
    app.add_handler(CommandHandler("quiz",         cmd_quiz))
    app.add_handler(CommandHandler("pyq",          cmd_pyq))
    app.add_handler(CommandHandler("leaderboard",  cmd_leaderboard))
    app.add_handler(CommandHandler("myrank",       cmd_myrank))
    app.add_handler(CommandHandler("toptoday",     cmd_toptoday))
    app.add_handler(CommandHandler("resetscore",   cmd_resetscore))
    # New commands
    app.add_handler(CommandHandler("timer",        cmd_timer))
    app.add_handler(CommandHandler("schedule",     cmd_schedule))
    app.add_handler(CommandHandler("scheduleoff",  cmd_scheduleoff))
    app.add_handler(CommandHandler("schedulelist", cmd_schedulelist))
    # Voice messages
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    # Poll answers (personal + group)
    app.add_handler(PollAnswerHandler(on_poll_answer))

    logger.info("Bot polling for updates …")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
