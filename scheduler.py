"""
Daily scheduled quiz — APScheduler AsyncIOScheduler firing at 9 PM IST.
init_scheduler(app) must be called from Application.post_init.
"""
import asyncio
import logging

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

IST = pytz.timezone("Asia/Kolkata")
_scheduler = AsyncIOScheduler(timezone=IST)
_app = None   # set by init_scheduler()


def init_scheduler(app):
    """Call once from Application.post_init; loads saved schedules and starts the clock."""
    global _app
    _app = app
    _load_schedules()
    _scheduler.start()
    logger.info("Scheduler started.")


def _load_schedules():
    from database import get_all_schedules
    for row in get_all_schedules():
        _add_job(int(row["chat_id"]), row["topic"], int(row["count"]))


def add_schedule(chat_id: int, topic: str, count: int):
    """Persist to DB and register the cron job (idempotent)."""
    from database import set_schedule
    set_schedule(chat_id, topic, count)
    _add_job(chat_id, topic, count)


def remove_schedule(chat_id: int):
    """Remove DB record and cancel the cron job."""
    from database import remove_schedule as db_remove
    db_remove(chat_id)
    try:
        _scheduler.remove_job(f"daily_{chat_id}")
        logger.info("Removed scheduled quiz for chat %d", chat_id)
    except Exception:
        pass


def _add_job(chat_id: int, topic: str, count: int):
    _scheduler.add_job(
        _run_scheduled_quiz,
        trigger=CronTrigger(hour=21, minute=0, timezone=IST),
        args=[chat_id, topic, count],
        id=f"daily_{chat_id}",
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info("Scheduled daily quiz: chat=%d topic=%r count=%d at 21:00 IST",
                chat_id, topic, count)


async def _run_scheduled_quiz(chat_id: int, topic: str, count: int):
    """Coroutine executed by APScheduler at 9 PM IST each day."""
    if _app is None:
        return
    bot = _app.bot

    from database import get_group_timer
    from quiz import (generate_questions, start_group_session,
                      send_group_question, _advance_group_after_timeout)
    from telegram.constants import ParseMode

    try:
        timer = get_group_timer(chat_id)

        await bot.send_message(
            chat_id=chat_id,
            text=(
                f"📅 *Daily Quiz Time!*\n\n"
                f"📖 Topic: *{topic}*\n"
                f"❓ Questions: *{count}*\n"
                f"⏱ Timer: *{timer}s* per question\n\n"
                f"_Generating questions…_"
            ),
            parse_mode=ParseMode.MARKDOWN,
        )

        questions = await generate_questions(topic, count)
        session   = start_group_session(chat_id, questions, topic, timer)
        await send_group_question(bot, session)

        task = asyncio.create_task(
            _advance_group_after_timeout(bot, chat_id, 0)
        )
        session["advance_job"] = task

    except Exception as exc:
        logger.error("Scheduled quiz failed for chat %d: %s", chat_id, exc)
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"❌ Daily quiz failed to start: {str(exc)[:150]}"
            )
        except Exception:
            pass
