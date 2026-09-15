"""Admin access, broadcast and private support relay for RATHOD Telegram Bot."""
from __future__ import annotations

import asyncio
import os
import re
from functools import partial

from telegram import BotCommand
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters


_INSTALLED = False


def _is_admin(update, admin_ids) -> bool:
    user = update.effective_user
    return bool(user and int(user.id) in {int(x) for x in admin_ids})


def _admin_chat_id(admin_ids) -> int | None:
    raw = (os.environ.get("ADMIN_CHAT_ID") or "").strip()
    try:
        return int(raw) if raw else (int(next(iter(admin_ids))) if admin_ids else None)
    except (TypeError, ValueError):
        return None


def _text(update, context) -> str:
    value = " ".join(context.args or []).strip()
    if value:
        return value
    message = update.effective_message
    reply = message.reply_to_message if message else None
    return (reply.text or reply.caption or "").strip() if reply else ""


def _known_chats(db_module) -> list[int]:
    try:
        with db_module.get_connection() as conn:
            rows = conn.execute("SELECT DISTINCT chat_id FROM users WHERE chat_id IS NOT NULL").fetchall()
        return [int(row[0]) for row in rows]
    except Exception:
        return []


async def _send_one(bot, chat_id: int, text: str) -> bool:
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        return True
    except Exception:
        return False


async def cmd_adminpanel(update, context: ContextTypes.DEFAULT_TYPE, *, admin_ids):
    if not _is_admin(update, admin_ids):
        return
    await update.effective_message.reply_text(
        "🔐 RATHOD ADMIN PANEL\n\n"
        "/broadcast <message> — सभी registered chats\n"
        "/dm <user_id> <message> — किसी user को direct message\n"
        "/notify <message> — configured group notification\n"
        "/coupon <code> <note> — coupon announcement\n"
        "Private user message का reply करने पर उसी user को उत्तर जाएगा।\n\n"
        "Admin access Telegram user ID allowlist से सुरक्षित है।"
    )


async def cmd_broadcast(update, context: ContextTypes.DEFAULT_TYPE, *, db_module, admin_ids):
    if not _is_admin(update, admin_ids):
        await update.effective_message.reply_text("⛔️ केवल Admin broadcast भेज सकता है।")
        return
    text = _text(update, context)
    if not text:
        await update.effective_message.reply_text("Use: /broadcast आपका message")
        return
    chats = _known_chats(db_module)
    if not chats:
        await update.effective_message.reply_text("📭 अभी कोई registered chat नहीं है।")
        return
    prefix = "📢 RATHOD HUB BROADCAST\n\n"
    sent = 0
    for chat_id in chats:
        if await _send_one(context.bot, chat_id, prefix + text):
            sent += 1
        await asyncio.sleep(0.05)
    await update.effective_message.reply_text(f"✅ Broadcast complete: {sent}/{len(chats)} chats को भेजा गया।")


async def cmd_dm(update, context: ContextTypes.DEFAULT_TYPE, *, admin_ids):
    if not _is_admin(update, admin_ids):
        await update.effective_message.reply_text("⛔️ केवल Admin DM भेज सकता है।")
        return
    args = list(context.args or [])
    if len(args) < 2 or not args[0].lstrip("-").isdigit():
        await update.effective_message.reply_text("Use: /dm <telegram_user_id> आपका message")
        return
    target = int(args.pop(0))
    text = " ".join(args).strip() or _text(update, context)
    if not text:
        await update.effective_message.reply_text("Message खाली नहीं हो सकता।")
        return
    ok = await _send_one(context.bot, target, "👤 RATHOD Admin\n\n" + text)
    await update.effective_message.reply_text("✅ Direct message भेज दिया गया।" if ok else "❌ User को message नहीं भेज पाया।")


async def handle_private_message(update, context: ContextTypes.DEFAULT_TYPE, *, db_module, admin_ids):
    message = update.effective_message
    user = update.effective_user
    if not message or not user or not message.text:
        return
    if _is_admin(update, admin_ids):
        reply = message.reply_to_message
        if reply:
            match = re.search(r"USER_ID:(\d+)", reply.text or "")
            if match:
                target = int(match.group(1))
                ok = await _send_one(context.bot, target, "👤 RATHOD Admin\n\n" + message.text)
                await message.reply_text("✅ User को reply भेज दिया गया।" if ok else "❌ User को reply नहीं भेज पाया।")
        return

    db_module.ensure_user(user.id, user.id, user.username or "", user.full_name or "Telegram User")
    admin_chat = _admin_chat_id(admin_ids)
    if admin_chat is None:
        return
    forwarded = (
        "📩 PRIVATE SUPPORT MESSAGE\n\n"
        f"Name: {user.full_name or 'User'}\n"
        f"Username: @{user.username}" if user.username else f"Name: {user.full_name or 'User'}"
    )
    forwarded += f"\nUSER_ID:{user.id}\n\n{message.text}"
    await _send_one(context.bot, admin_chat, forwarded)
    await message.reply_text("✅ आपका message Admin तक भेज दिया गया है। Reply आने पर यहीं मिलेगा।")


async def install(application, db_module, admin_ids):
    global _INSTALLED
    if _INSTALLED:
        return
    _INSTALLED = True
    application.add_handler(CommandHandler("adminpanel", partial(cmd_adminpanel, admin_ids=admin_ids)))
    application.add_handler(CommandHandler("broadcast", partial(cmd_broadcast, db_module=db_module, admin_ids=admin_ids)))
    application.add_handler(CommandHandler("dm", partial(cmd_dm, admin_ids=admin_ids)))
    application.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
            partial(handle_private_message, db_module=db_module, admin_ids=admin_ids),
        ),
        group=-1,
    )
    existing = await application.bot.get_my_commands()
    known = {item.command for item in existing}
    additions = [
        BotCommand("adminpanel", "Admin controls"),
        BotCommand("broadcast", "Broadcast to registered chats"),
        BotCommand("dm", "Direct message a user"),
    ]
    await application.bot.set_my_commands(existing + [x for x in additions if x.command not in known])
