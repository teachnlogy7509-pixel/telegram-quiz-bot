"""RATHOD VIP Telegram commands, full-length poll UI, and multi-key AI rotation."""
from __future__ import annotations

import asyncio
import logging
import os

from telegram.constants import ParseMode
from telegram.error import TelegramError

import supabase_sync

logger = logging.getLogger(__name__)


def _active(update, db_module) -> bool:
    chat = update.effective_chat
    return bool(chat and db_module.is_bot_active(chat.id))


def _is_highlevel(session: dict) -> bool:
    style = str(session.get("style") or "").lower().replace("-", "")
    topic = str(session.get("topic") or "").lower()
    return style in {"pro", "highlevel"} or "high-level" in topic or "rathod pro" in topic


def install(quiz_module):
    """Enable five Gemini keys, full poll text and high-level scoring."""
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

    async def sync_skip(bot, session, user_id: int, username: str = "", name: str = "Telegram User"):
        try:
            if not username or name == "Telegram User":
                chat = await bot.get_chat(user_id)
                username = username or getattr(chat, "username", "") or ""
                name = getattr(chat, "full_name", None) or getattr(chat, "first_name", None) or name
            await asyncio.to_thread(
                supabase_sync.record_answer,
                telegram_user_id=int(user_id),
                chat_id=int(session["chat_id"]),
                username=username or "",
                name=name or "Telegram User",
                is_correct=False,
                topic=str(session.get("topic") or "High-Level Quiz") + " [SKIPPED]",
                correct_score=100,
                wrong_score=-75,
            )
        except Exception as exc:
            logger.warning("High-level skip score sync failed: %s", str(exc)[:180])

    async def advance_after_timeout(bot, user_id: int, question_index: int):
        session = quiz_module.active_sessions.get(user_id)
        timer = session.get("timer", 30) if session else 30
        await asyncio.sleep(timer + 1)
        session = quiz_module.active_sessions.get(user_id)
        if not session or session["current_idx"] != question_index:
            return
        if not session["answered_current"]:
            session["unanswered"] += 1
            if _is_highlevel(session):
                session["score"] -= 75
                await sync_skip(bot, session, user_id)
            else:
                session["score"] += getattr(quiz_module, "UNANSWERED_SCORE", 0)
        await quiz_module._next_or_finish(bot, session)

    async def advance_group_after_timeout(bot, chat_id: int, question_index: int):
        session = quiz_module.group_sessions.get(chat_id)
        timer = session.get("timer", 30) if session else 30
        await asyncio.sleep(timer + 1)
        session = quiz_module.group_sessions.get(chat_id)
        if not session or session["current_idx"] != question_index:
            return
        if _is_highlevel(session):
            answered = set(session.get("answered_users") or set())
            for user_id, stats in list((session.get("user_scores") or {}).items()):
                if user_id in answered:
                    continue
                stats["score"] = int(stats.get("score") or 0) - 75
                await sync_skip(bot, session, int(user_id), str(stats.get("username") or ""), str(stats.get("name") or "Telegram User"))
        await quiz_module._next_or_finish_group(bot, session)

    quiz_module.send_question = send_question
    quiz_module.send_group_question = send_group_question
    quiz_module._advance_after_timeout = advance_after_timeout
    quiz_module._advance_group_after_timeout = advance_group_after_timeout
    logger.info("VIP Telegram UI installed; high-level scoring +100/-50/skip -75")


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
    wait = await update.message.reply_text(f"👑 RATHOD PRO Engine {count} ultra-high-level questions बना रहा है…\n✅ +100 XP • ❌ −50 XP • ⏭ Skip −75 XP")
    pro_topic = f"""{topic}. RATHOD PRO MODE: Difficulty above standard NEET but every fact must remain NCERT-valid. Make a balanced mix of PYQ-inspired conceptual traps, Assertion–Reason, Statement I/II, multi-statement combinations, match-the-following, exceptions, deep applications and difficult NCERT line-based questions. No vague or out-of-syllabus fact may be required. Long stems are allowed because the bot displays them separately without truncation."""
    try:
        questions = await quiz_module.generate_questions(pro_topic, count, "pro")
        await wait.delete()
        timer = db_module.get_group_timer(chat_id)
        title = f"👑 PRO • {topic}"
        if chat_id < 0:
            session = quiz_module.start_group_session(chat_id, questions, title, timer)
            await update.message.reply_text(f"👑 *RATHOD PRO QUIZ*\n📚 {topic}\n❓ {count} ultra-level questions\n✅ +100 • ❌ −50 • ⏭ −75 XP", parse_mode=ParseMode.MARKDOWN)
            await quiz_module.send_group_question(context.bot, session)
            session["advance_job"] = asyncio.create_task(quiz_module._advance_group_after_timeout(context.bot, chat_id, 0))
        else:
            session = quiz_module.start_session(user.id, chat_id, questions, title, "pro", timer)
            await update.message.reply_text(f"👑 *RATHOD PRO QUIZ*\n📚 {topic}\n❓ {count} ultra-level questions\n✅ +100 • ❌ −50 • ⏭ −75 XP", parse_mode=ParseMode.MARKDOWN)
            await quiz_module.send_question(context.bot, session)
            session["advance_job"] = asyncio.create_task(quiz_module._advance_after_timeout(context.bot, user.id, 0))
    except Exception as exc:
        logger.exception("PRO quiz failed")
        await wait.edit_text(f"❌ PRO Quiz नहीं बना: {str(exc)[:300]}")
