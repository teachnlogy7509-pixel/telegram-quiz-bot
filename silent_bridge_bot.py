"""RATHOD SAKHI bridge wrapper with group archive PDF access."""
from __future__ import annotations

import asyncio
import html
import os
import random
from datetime import datetime, timedelta, timezone

from telegram import BotCommand, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import bridge_bot as base

IST = timezone(timedelta(hours=5, minutes=30))
MOTIVATION_HOURS = tuple(sorted({int(x) for x in (os.getenv("BRIDGE_MOTIVATION_HOURS", "12,20").replace(" ", "").split(",")) if x.isdigit() and 0 <= int(x) <= 23})) or (12, 20)
SHAYARI = [
    "📚 Chhoti progress bhi progress hoti hai. Aaj ka ek quiz kal ki jeet banega 💙",
    "✨ Mehnat ki roshni dheere-dheere sahi, lekin sapne tak zaroor pahunchati hai।",
    "🌸 Thak jao to rukna, haarna nahi—RATHOD SAKHI hamesha aapke saath hai 💙",
    "🔥 Ek focused hour, ek strong step—NEET dream aapse door nahi hai।",
    "🌙 Aaj ki padhai kal ke result ki sabse khoobsurat wajah banegi 📖",
]
SENT_MOTIVATION_SLOTS: set[str] = set()
MOTIVATION_LOCK = asyncio.Lock()


def admin_ids() -> set[int]:
    raw = os.getenv("BRIDGE_ADMIN_IDS") or os.getenv("ADMIN_IDS") or ""
    result: set[int] = set()
    for value in raw.replace(",", " ").split():
        try: result.add(int(value.strip()))
        except ValueError: pass
    return result


async def app_notifications_only(app: Application) -> None:
    """Forward immediate admin/app notifications, never ordinary quiz activity."""
    if not (base.SUPA_URL and base.SUPA_KEY and base.GROUP_ID): return
    try:
        rows = await asyncio.to_thread(base.pending, "immediate")
        for row in rows[:20]:
            payload = base.payload(row)
            title = str(payload.get("title") or "📢 RATHOD HUB Update")
            body = str(payload.get("body") or "Nayi app notification aayi hai.")
            text = f"{html.escape(title)}\n\n{html.escape(body)}\n\n<i>— {base.BOT_NAME} 💙</i>"
            if await base.send_group(text, app.bot):
                await asyncio.to_thread(base.mark, [int(row["id"])], "admin-app-notification")
    except Exception: base.log.exception("App notification delivery failed")


def all_score_text(rows: list[dict]) -> str:
    lines: list[str] = []
    for i, row in enumerate(rows, 1):
        medal = ["🥇", "🥈", "🥉"][i - 1] if i <= 3 else f"{i}."
        lines.append(f"{medal} {html.escape(base.safe_name(row.get('telegram_name')))} — <b>{int(row.get('total_xp', 0) or 0)} XP</b>")
    body = "\n".join(lines) or "Abhi score board ready ho raha hai 😊"
    return ("🎯 <b>Telegram Quiz Leaderboard Update</b>\n\nPichhle update ke 30 minute baad latest score:\n\n" + body + "\n\n👏 Padhte raho, aap sab bahut achha kar rahe ho 🔥📚")


async def motivation_twice_daily(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send one shayari per configured hour, with a process and DB guard."""
    local = datetime.now(IST)
    if local.hour not in MOTIVATION_HOURS: return
    day = local.date().isoformat(); slot = str(local.hour); key = f"{day}:{slot}"
    async with MOTIVATION_LOCK:
        if key in SENT_MOTIVATION_SLOTS: return
        SENT_MOTIVATION_SLOTS.add(key)
        try:
            rows = await asyncio.to_thread(base.rest,"GET","rh_bridge_events",{"select":"payload","event_type":"eq.sakhi_motivation","created_at":f"gte.{day}T00:00:00+05:30","limit":"20"}) or []
            for row in rows:
                payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
                if str(payload.get("day")) == day and str(payload.get("slot")) == slot: return
        except Exception:
            SENT_MOTIVATION_SLOTS.discard(key); base.log.exception("Could not check shayari state"); return
        line = random.choice(SHAYARI)
        text = f"💌 <b>{base.BOT_NAME}</b> ki daily shayari\n\n{html.escape(line)}\n\n<i>{base.BOT_BYLINE}</i>"
        if not await base.send_group(text, context.application.bot):
            SENT_MOTIVATION_SLOTS.discard(key); return
        try:
            await asyncio.to_thread(base.rest,"POST","rh_bridge_events",body={"event_type":"sakhi_motivation","delivery_mode":"direct","display_name":base.BOT_NAME,"payload":{"kind":"twice_daily_shayari","day":day,"slot":slot}})
        except Exception: base.log.exception("Could not save shayari state")


async def archivepdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return the newest archive Notes and Test PDFs in private chat or the group."""
    message = update.effective_message
    if not message: return
    try:
        rows = await asyncio.to_thread(base.rest,"GET","rh_bridge_events",{"select":"payload,created_at","event_type":"eq.archive_pdf_ready","order":"created_at.desc","limit":"1"}) or []
    except Exception:
        base.log.exception("Archive PDF lookup failed")
        await message.reply_text("Archive PDF अभी load नहीं हो पाई। थोड़ी देर बाद /archivepdf चलाएँ।")
        return
    if not rows:
        await message.reply_text("Archive worker ने अभी PDF link तैयार नहीं की है। अगला archive update आने के बाद /archivepdf चलाएँ।")
        return
    payload = rows[0].get("payload") if isinstance(rows[0].get("payload"), dict) else {}
    notes_url = str(payload.get("notes_url") or "").strip()
    test_url = str(payload.get("test_url") or "").strip()
    label = html.escape(str(payload.get("label") or "Latest archive"))
    links = []
    if notes_url: links.append(f'📘 <a href="{html.escape(notes_url, quote=True)}">Notes PDF खोलें</a>')
    if test_url: links.append(f'📝 <a href="{html.escape(test_url, quote=True)}">Test PDF खोलें</a>')
    if not links:
        await message.reply_text("Latest archive record मिला, लेकिन PDF links अभी ready नहीं हैं।")
        return
    await message.reply_text("📚 <b>RATHOD Quiz Archive</b>\n" + label + "\n\n" + "\n".join(links) + "\n\n<i>इन links को group members खोल सकते हैं।</i>",parse_mode="HTML",disable_web_page_preview=True)


async def sakhi_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user
    if not caller or caller.id not in admin_ids(): return
    message = " ".join(context.args or []).strip()
    reply = update.effective_message.reply_to_message if update.effective_message else None
    if not message and reply: message = reply.text or reply.caption or ""
    if not message:
        await update.effective_message.reply_text("Use: /sakhi_notify आपका message"); return
    target = update.effective_chat.id if update.effective_chat and update.effective_chat.type in {"group", "supergroup"} else base.GROUP_ID
    try: target_id = int(str(target))
    except (TypeError, ValueError):
        await update.effective_message.reply_text("Target group configured नहीं है।"); return
    await context.bot.send_message(chat_id=target_id, text="📢 RATHOD HUB ADMIN NOTICE\n\n" + message)
    await update.effective_message.reply_text("✅ Admin notice भेज दिया गया।")


async def bridge_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(
        "💙 <b>RATHOD SAKHI</b>\n\n"
        "• Admin app updates और Daily 9 PM updates\n"
        "• Telegram quiz leaderboard 30-minute delay के साथ\n"
        "• /archivepdf से latest Notes/Test PDF\n"
        "• New member welcome\n"
        "• /bol से Sakhi से बात करें\n"
        "• Group messages पर light reactions\n"
        "• Shayari/motivation: दिन में अधिकतम 2 बार\n\n" + base.BOT_BYLINE,
        parse_mode="HTML",
    )


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("about", "RATHOD SAKHI के बारे में"),
        BotCommand("bridgehelp", "Sakhi के features"),
        BotCommand("bol", "Sakhi से बात करें"),
        BotCommand("archivepdf", "Latest Notes/Test PDF"),
    ])
    if app.job_queue:
        app.job_queue.run_repeating(base.poll_job, interval=base.POLL_SECONDS, first=8, name="rh-bridge-poll")
        app.job_queue.run_repeating(motivation_twice_daily, interval=60, first=300, name="rh-bridge-shayari")


def main() -> None:
    if not base.BOT_TOKEN: raise SystemExit("BRIDGE_TELEGRAM_BOT_TOKEN is missing")
    if not base.SUPA_URL or not base.SUPA_KEY: raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    base.process_events = app_notifications_only
    base.score_text = all_score_text
    app = Application.builder().token(base.BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("about", base.about))
    app.add_handler(CommandHandler("bridgehelp", bridge_help))
    app.add_handler(CommandHandler("bol", base.ask_command))
    app.add_handler(CommandHandler("archivepdf", archivepdf))
    app.add_handler(CommandHandler("sakhi_notify", sakhi_notify))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, base.welcome))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, base.chat_message))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, base.group_activity))
    base.log.info("Sakhi configured: archive PDFs, max two shayari/day, duplicate guard")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__": main()
