"""Multiple daily Telegram quiz schedules with arbitrary IST times and reset controls."""
from __future__ import annotations

import asyncio
import logging
import sqlite3
from datetime import datetime

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
    conn.execute("""CREATE TABLE IF NOT EXISTS vip_schedules(id INTEGER PRIMARY KEY AUTOINCREMENT,chat_id INTEGER NOT NULL,topic TEXT NOT NULL,count INTEGER NOT NULL,hour INTEGER NOT NULL,minute INTEGER NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit();return conn


def _parse_time(value: str) -> tuple[int, int]:
    parts=value.strip().split(":")
    if len(parts)!=2:raise ValueError("Time HH:MM format में दें")
    hour,minute=int(parts[0]),int(parts[1])
    if not 0<=hour<=23 or not 0<=minute<=59:raise ValueError("Invalid time")
    return hour,minute


def add_schedule(chat_id: int,time_text: str,topic: str,count: int) -> int:
    hour,minute=_parse_time(time_text)
    with _conn() as conn:
        existing=conn.execute("SELECT id FROM vip_schedules WHERE chat_id=? AND hour=? AND minute=? AND lower(topic)=lower(?)",(chat_id,hour,minute,topic)).fetchone()
        if existing:
            sid=int(existing["id"]);conn.execute("UPDATE vip_schedules SET count=?,enabled=1 WHERE id=?",(count,sid))
        else:
            total=conn.execute("SELECT count(*) n FROM vip_schedules WHERE chat_id=? AND enabled=1",(chat_id,)).fetchone()["n"]
            if total>=10:raise ValueError("एक group में maximum 10 daily schedules रख सकते हैं।")
            cur=conn.execute("INSERT INTO vip_schedules(chat_id,topic,count,hour,minute) VALUES(?,?,?,?,?)",(chat_id,topic,count,hour,minute));sid=int(cur.lastrowid)
        conn.commit()
    _add_job(sid,chat_id,topic,count,hour,minute);return sid


def list_schedules(chat_id: int):
    with _conn() as conn:return [dict(x) for x in conn.execute("SELECT * FROM vip_schedules WHERE chat_id=? AND enabled=1 ORDER BY hour,minute,id",(chat_id,)).fetchall()]


def remove_schedule(chat_id: int,sid: int|None=None):
    with _conn() as conn:
        if sid is None:rows=conn.execute("SELECT id FROM vip_schedules WHERE chat_id=?",(chat_id,)).fetchall();conn.execute("DELETE FROM vip_schedules WHERE chat_id=?",(chat_id,))
        else:rows=conn.execute("SELECT id FROM vip_schedules WHERE chat_id=? AND id=?",(chat_id,sid)).fetchall();conn.execute("DELETE FROM vip_schedules WHERE chat_id=? AND id=?",(chat_id,sid))
        conn.commit()
    for row in rows:
        try:_scheduler.remove_job("vip_daily_"+str(row["id"]))
        except Exception:pass
    return len(rows)


def _add_job(sid,chat_id,topic,count,hour,minute):
    _scheduler.add_job(_run,trigger=CronTrigger(hour=hour,minute=minute,timezone=IST),args=[sid,chat_id,topic,count],id="vip_daily_"+str(sid),replace_existing=True,misfire_grace_time=600)


def init_scheduler(application):
    global _app
    _app=application
    with _conn() as conn:rows=conn.execute("SELECT * FROM vip_schedules WHERE enabled=1").fetchall()
    for row in rows:_add_job(row["id"],row["chat_id"],row["topic"],row["count"],row["hour"],row["minute"])
    if not _scheduler.running:_scheduler.start()
    logger.info("VIP multi-scheduler active with %s jobs",len(rows))


async def _run(sid,chat_id,topic,count):
    if _app is None:return
    bot=_app.bot
    try:
        await bot.send_message(chat_id=chat_id,text=f"⏰ *Scheduled RATHOD Quiz #{sid}*\n📚 {topic}\n❓ {count} questions\n👑 VIP questions generate हो रहे हैं…",parse_mode=ParseMode.MARKDOWN)
        questions=await quiz.generate_questions(topic,count,"quiz")
        session=quiz.start_group_session(chat_id,questions,f"⏰ {topic}",30)
        await quiz.send_group_question(bot,session)
        session["advance_job"]=asyncio.create_task(quiz._advance_group_after_timeout(bot,chat_id,0))
    except Exception as exc:
        logger.exception("Scheduled quiz failed")
        await bot.send_message(chat_id=chat_id,text=f"❌ Schedule #{sid} failed: {str(exc)[:180]}")


async def cmd_schedule(update,context):
    args=context.args or []
    if len(args)<3:
        await update.message.reply_text("इस्तेमाल: /schedule HH:MM <topic> <number>\nउदाहरण: /schedule 09:00 Biology 10\nकम-से-कम 2 अलग schedules भी जोड़ सकते हैं।")
        return
    try:count=int(args[-1]);time_text=args[0];topic=" ".join(args[1:-1]).strip();
    except ValueError:return await update.message.reply_text("आखिर में question number दें।")
    if not 2<=count<=50:return await update.message.reply_text("Questions 2 से 50 रखें।")
    try:sid=add_schedule(update.effective_chat.id,time_text,topic,count);await update.message.reply_text(f"✅ Daily Schedule #{sid} saved\n⏰ {time_text} IST\n📚 {topic}\n❓ {count} questions")
    except Exception as exc:await update.message.reply_text(f"❌ {str(exc)}")


async def cmd_schedulelist(update,context):
    rows=list_schedules(update.effective_chat.id)
    if not rows:return await update.message.reply_text("कोई daily schedule नहीं है।")
    text=["📅 *DAILY QUIZ SCHEDULES*"]+[f"#{r['id']} • {r['hour']:02d}:{r['minute']:02d} IST • {r['topic']} • {r['count']}Q" for r in rows]
    await update.message.reply_text("\n".join(text),parse_mode=ParseMode.MARKDOWN)


async def cmd_scheduleoff(update,context):
    arg=(context.args or ["all"])[0].lower()
    try:sid=None if arg=="all" else int(arg);removed=remove_schedule(update.effective_chat.id,sid);await update.message.reply_text(f"✅ {removed} schedule हटाया गया।")
    except ValueError:await update.message.reply_text("/scheduleoff <schedule-id|all>")


async def cmd_schedulereset(update,context):
    removed=remove_schedule(update.effective_chat.id,None);await update.message.reply_text(f"🔄 Scheduler reset complete — {removed} schedules removed. अब नए schedules डालें।")
