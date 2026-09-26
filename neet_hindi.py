"""Timer-free Hindi NEET quiz commands and persistent daily schedules."""
from __future__ import annotations

import asyncio
import logging
import sqlite3

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram.constants import ParseMode

import config
import quiz

logger = logging.getLogger(__name__)
IST = pytz.timezone("Asia/Kolkata")
_scheduler = AsyncIOScheduler(timezone=IST)
_app = None


def _conn():
    conn = sqlite3.connect(getattr(config, "DB_PATH", "scores.db"), timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE IF NOT EXISTS neet_hindi_schedules(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        count INTEGER NOT NULL,
        hour INTEGER NOT NULL,
        minute INTEGER NOT NULL,
        enabled INTEGER NOT NULL DEFAULT 1,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
    )
    conn.commit()
    return conn


def _parse_time(value: str) -> tuple[int, int]:
    parts = value.strip().split(":")
    if len(parts) != 2:
        raise ValueError("समय HH:MM format में दें।")
    hour, minute = int(parts[0]), int(parts[1])
    if not 0 <= hour <= 23 or not 0 <= minute <= 59:
        raise ValueError("समय सही नहीं है।")
    return hour, minute


async def _is_admin(update, context) -> bool:
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id, update.effective_user.id
        )
        return member.status in {"administrator", "creator"}
    except Exception:
        return False


def _parse_topic_count(args) -> tuple[str, int]:
    values = list(args or [])
    if len(values) < 2:
        raise ValueError("Format: /neetquiz <topic> <number>")
    try:
        count = int(values[-1])
    except ValueError as exc:
        raise ValueError("आखिर में questions की संख्या दें।") from exc
    topic = " ".join(values[:-1]).strip()
    if not topic:
        raise ValueError("Topic लिखिए।")
    if not 1 <= count <= 30:
        raise ValueError("Questions 1 से 30 के बीच रखें।")
    return topic, count


async def send_timer_free_quiz(bot, chat_id: int, topic: str, count: int):
    await bot.send_message(
        chat_id=chat_id,
        text=(
            "🧬 *NEET HINDI PRACTICE*\n\n"
            f"📚 Topic: *{topic}*\n"
            f"❓ Questions: *{count}*\n"
            "⏱ कोई timer नहीं—आराम से हल कीजिए।\n\n"
            "_NEET/NCERT-level Hindi questions बन रहे हैं…_"
        ),
        parse_mode=ParseMode.MARKDOWN,
    )
    questions = await quiz.generate_questions(topic, count, "neet_hindi")
    for index, question in enumerate(questions, 1):
        title = f"NEET Hindi Q{index}/{count}: {question['question']}"
        await bot.send_poll(
            chat_id=chat_id,
            question=title[:300],
            options=[str(item)[:100] for item in question["options"]],
            type="quiz",
            correct_option_id=int(question["correct_index"]),
            is_anonymous=False,
        )
        await asyncio.sleep(0.35)


async def cmd_neetquiz(update, context):
    if update.effective_chat.type not in ("group", "supergroup"):
        return
    try:
        topic, count = _parse_topic_count(context.args)
        await send_timer_free_quiz(context.bot, update.effective_chat.id, topic, count)
    except Exception as exc:
        logger.exception("NEET Hindi quiz failed")
        await update.message.reply_text(f"❌ {str(exc)[:250]}")


def _add_job(schedule_id, chat_id, topic, count, hour, minute):
    _scheduler.add_job(
        _run_schedule,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=IST),
        args=[schedule_id, chat_id, topic, count],
        id=f"neet_hindi_{schedule_id}",
        replace_existing=True,
        misfire_grace_time=600,
    )


async def _run_schedule(schedule_id, chat_id, topic, count):
    if _app is None:
        return
    try:
        await send_timer_free_quiz(_app.bot, chat_id, topic, count)
    except Exception as exc:
        logger.exception("Scheduled NEET Hindi quiz failed")
        try:
            await _app.bot.send_message(
                chat_id, f"❌ NEET schedule #{schedule_id} failed: {str(exc)[:180]}"
            )
        except Exception:
            pass


def init_scheduler(application):
    global _app
    _app = application
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM neet_hindi_schedules WHERE enabled=1"
        ).fetchall()
    for row in rows:
        _add_job(
            row["id"], row["chat_id"], row["topic"], row["count"],
            row["hour"], row["minute"]
        )
    if not _scheduler.running:
        _scheduler.start()
    logger.info("NEET Hindi scheduler active with %s jobs", len(rows))


async def cmd_neetschedule(update, context):
    if update.effective_chat.type not in ("group", "supergroup"):
        return
    if not await _is_admin(update, context):
        return await update.message.reply_text("⚠️ केवल group admin schedule बना सकता है।")
    args = list(context.args or [])
    if len(args) < 3:
        return await update.message.reply_text(
            "Format: /neetschedule HH:MM <topic> <number>\n"
            "उदाहरण: /neetschedule 20:30 Human Physiology 10"
        )
    try:
        hour, minute = _parse_time(args[0])
        topic, count = _parse_topic_count(args[1:])
        with _conn() as conn:
            total = conn.execute(
                "SELECT count(*) n FROM neet_hindi_schedules "
                "WHERE chat_id=? AND enabled=1",
                (update.effective_chat.id,),
            ).fetchone()["n"]
            if total >= 10:
                raise ValueError("एक group में maximum 10 NEET schedules रख सकते हैं।")
            cursor = conn.execute(
                "INSERT INTO neet_hindi_schedules"
                "(chat_id,topic,count,hour,minute) VALUES(?,?,?,?,?)",
                (update.effective_chat.id, topic, count, hour, minute),
            )
            schedule_id = int(cursor.lastrowid)
            conn.commit()
        _add_job(
            schedule_id, update.effective_chat.id, topic, count, hour, minute
        )
        await update.message.reply_text(
            f"✅ NEET Schedule #{schedule_id} saved\n"
            f"⏰ {hour:02d}:{minute:02d} IST\n📚 {topic}\n"
            f"❓ {count} questions • कोई timer नहीं"
        )
    except Exception as exc:
        await update.message.reply_text(f"❌ {str(exc)}")


async def cmd_neetschedules(update, context):
    if update.effective_chat.type not in ("group", "supergroup"):
        return
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM neet_hindi_schedules "
            "WHERE chat_id=? AND enabled=1 ORDER BY hour,minute,id",
            (update.effective_chat.id,),
        ).fetchall()
    if not rows:
        return await update.message.reply_text("कोई NEET Hindi schedule नहीं है।")
    lines = ["📅 *NEET HINDI SCHEDULES*"]
    lines.extend(
        f"#{row['id']} • {row['hour']:02d}:{row['minute']:02d} IST • "
        f"{row['topic']} • {row['count']}Q • no timer"
        for row in rows
    )
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_neetoff(update, context):
    if update.effective_chat.type not in ("group", "supergroup"):
        return
    if not await _is_admin(update, context):
        return await update.message.reply_text("⚠️ केवल group admin schedule हटा सकता है।")
    arg = (context.args or ["all"])[0].lower()
    try:
        schedule_id = None if arg == "all" else int(arg)
    except ValueError:
        return await update.message.reply_text("/neetoff <schedule-id|all>")
    with _conn() as conn:
        if schedule_id is None:
            rows = conn.execute(
                "SELECT id FROM neet_hindi_schedules WHERE chat_id=?",
                (update.effective_chat.id,),
            ).fetchall()
            conn.execute(
                "DELETE FROM neet_hindi_schedules WHERE chat_id=?",
                (update.effective_chat.id,),
            )
        else:
            rows = conn.execute(
                "SELECT id FROM neet_hindi_schedules WHERE chat_id=? AND id=?",
                (update.effective_chat.id, schedule_id),
            ).fetchall()
            conn.execute(
                "DELETE FROM neet_hindi_schedules WHERE chat_id=? AND id=?",
                (update.effective_chat.id, schedule_id),
            )
        conn.commit()
    for row in rows:
        try:
            _scheduler.remove_job(f"neet_hindi_{row['id']}")
        except Exception:
            pass
    await update.message.reply_text(f"✅ {len(rows)} NEET schedule हटाया गया।")