"""RATHOD VIP Telegram commands, full-length poll UI, and multi-key AI rotation."""
from __future__ import annotations

import asyncio
import logging
import os

from telegram.constants import ParseMode
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


def _active(update, db_module) -> bool:
    chat = update.effective_chat
    return bool(chat and db_module.is_bot_active(chat.id))


def install(quiz_module):
    """Enable up to five Gemini keys and never cut long questions/options."""
    def api_keys():
        names = ["GEMINI_API_KEY", "GEMINI_API_KEY_2", "GEMINI_API_KEY_3", "GEMINI_API_KEY_4", "GEMINI_API_KEY_5"]
        return [os.environ.get(name, "").strip() for name in names if os.environ.get(name, "").strip()]
    quiz_module._api_keys = api_keys

    async def send_full_poll(bot, session, *, group: bool):
        idx = session["current_idx"]
        q = session["questions"][idx]
        total = session["total"]
        chat_id = session["chat_id"]
        topic = str(session.get("topic") or "VIP Quiz")
        question = str(q["question"]).strip()
        full_options = [str(x).strip() for x in q["options"]]
        prefix = f"📚 {topic} — ❓ Q{idx + 1}/{total}" if group else f"👑 RATHOD VIP • Q{idx + 1}/{total}"
        option_too_long = any(len(x) > 95 for x in full_options)
        direct = f"{prefix}\n\n{question}"
        if len(direct) > 285 or option_too_long:
            details = f"{prefix}\n\n{question}"
            if option_too_long:
                details += "\n\n" + "\n\n".join(f"{chr(65+i)}. {text}" for i, text in enumerate(full_options))
            for start in range(0, len(details), 3900):
                await bot.send_message(chat_id=chat_id, text=details[start:start + 3900])
            poll_question = f"Q{idx + 1}/{total} — ऊपर दिए गए पूरे प्रश्न का सही उत्तर चुनें।"
            options = [chr(65+i) for i in range(4)] if option_too_long else [x[:100] for x in full_options]
        else:
            poll_question = direct
            options = [x[:100] for x in full_options]
        try:
            msg = await bot.send_poll(chat_id=chat_id, question=poll_question, options=options, type="quiz", correct_option_id=int(q["correct_index"]), is_anonymous=False, open_period=session.get("timer", 30))
        except TelegramError as exc:
            logger.error("VIP poll send failed: %s", exc)
            return
        session["current_poll_id"] = msg.poll.id
        if group:
            session["current_correct"] = int(q["correct_index"])
            session["answered_users"] = set()
            quiz_module.poll_to_chat[msg.poll.id] = chat_id
        else:
            session["answered_current"] = False
            quiz_module.poll_to_user[msg.poll.id] = session["user_id"]

    async def send_question(bot, session):
        await send_full_poll(bot, session, group=False)

    async def send_group_question(bot, session):
        await send_full_poll(bot, session, group=True)

    quiz_module.send_question = send_question
    quiz_module.send_group_question = send_group_question
    logger.info("VIP Telegram UI installed with 5-key Gemini rotation")


async def cmd_proquiz(update, context, quiz_module, db_module):
    if not _active(update, db_module):
        await update.message.reply_text("⏸️ Bot paused है। Admin /on भेजें।")
        return
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("👑 इस्तेमाल: /proquiz <topic> <number>\nउदाहरण: /proquiz Human Physiology 20")
        return
    try:
        count = int(args[-1])
    except ValueError:
        await update.message.reply_text("आखिर में questions की संख्या दें।")
        return
    if not 2 <= count <= 50:
        await update.message.reply_text("PRO Quiz में 2 से 50 questions रखें।")
        return
    topic = " ".join(args[:-1]).strip()
    user = update.effective_user
    chat_id = update.effective_chat.id
    db_module.ensure_user(user.id, chat_id, user.username or "", user.full_name or "Telegram User")
    wait = await update.message.reply_text(f"👑 RATHOD PRO Engine {count} ultra-high-level questions बना रहा है…")
    pro_topic = f"""{topic}. RATHOD PRO MODE: Difficulty above standard NEET but every fact must remain NCERT-valid. Make a balanced mix of PYQ-inspired conceptual traps, Assertion–Reason, Statement I/II, multi-statement combinations, match-the-following, exceptions, deep applications and difficult NCERT line-based questions. No vague or out-of-syllabus fact may be required. Long stems are allowed because the bot displays them separately without truncation."""
    try:
        questions = await quiz_module.generate_questions(pro_topic, count, "pro")
        await wait.delete()
        timer = db_module.get_group_timer(chat_id)
        title = f"👑 PRO • {topic}"
        if chat_id < 0:
            session = quiz_module.start_group_session(chat_id, questions, title, timer)
            await update.message.reply_text(f"👑 *RATHOD PRO QUIZ*\n📚 {topic}\n❓ {count} ultra-level questions", parse_mode=ParseMode.MARKDOWN)
            await quiz_module.send_group_question(context.bot, session)
            session["advance_job"] = asyncio.create_task(quiz_module._advance_group_after_timeout(context.bot, chat_id, 0))
        else:
            session = quiz_module.start_session(user.id, chat_id, questions, title, "pro", timer)
            await update.message.reply_text(f"👑 *RATHOD PRO QUIZ*\n📚 {topic}\n❓ {count} ultra-level questions", parse_mode=ParseMode.MARKDOWN)
            await quiz_module.send_question(context.bot, session)
            session["advance_job"] = asyncio.create_task(quiz_module._advance_after_timeout(context.bot, user.id, 0))
    except Exception as exc:
        logger.exception("PRO quiz failed")
        await wait.edit_text(f"❌ PRO Quiz नहीं बना: {str(exc)[:300]}")
