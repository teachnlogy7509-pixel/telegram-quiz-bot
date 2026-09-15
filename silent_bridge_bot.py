"""RATHOD SAKHI bridge wrapper.

Keeps the existing bridge_bot features and AI commands, but disables automatic
quiz/score broadcasts that list students. Admins can send a manual notice with
/sakhi_notify <message>.
"""
from __future__ import annotations

import os

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

import bridge_bot as base


def admin_ids() -> set[int]:
    raw = os.getenv("BRIDGE_ADMIN_IDS") or os.getenv("ADMIN_IDS") or ""
    result: set[int] = set()
    for value in raw.replace(",", " ").split():
        try:
            result.add(int(value.strip()))
        except ValueError:
            pass
    return result


async def no_automatic_events(app: Application) -> None:
    # Intentionally silent: quiz results, scoreboards and learner names are not
    # broadcast automatically. Admin can use /sakhi_notify when needed.
    return None


async def no_automatic_scores(app: Application) -> None:
    return None


async def sakhi_notify(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller = update.effective_user
    if not caller or caller.id not in admin_ids():
        # Do not reveal the configured admin list.
        return
    message = " ".join(context.args or []).strip()
    reply = update.effective_message.reply_to_message if update.effective_message else None
    if not message and reply:
        message = reply.text or reply.caption or ""
    if not message:
        await update.effective_message.reply_text("Use: /sakhi_notify आपका message")
        return
    target = update.effective_chat.id if update.effective_chat and update.effective_chat.type in {"group", "supergroup"} else base.GROUP_ID
    try:
        target_id = int(str(target))
    except (TypeError, ValueError):
        await update.effective_message.reply_text("Target group configured नहीं है।")
        return
    await context.bot.send_message(chat_id=target_id, text="📢 RATHOD HUB ADMIN NOTICE\n\n" + message)
    await update.effective_message.reply_text("✅ Admin notice भेज दिया गया।")


def main() -> None:
    if not base.BOT_TOKEN:
        raise SystemExit("BRIDGE_TELEGRAM_BOT_TOKEN is missing")
    if not base.SUPA_URL or not base.SUPA_KEY:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

    # Patch only the scheduled automatic broadcast functions. Existing bridge
    # commands, welcome flow, reactions and AI chat remain available.
    base.process_events = no_automatic_events
    base.process_scores = no_automatic_scores

    app = Application.builder().token(base.BOT_TOKEN).post_init(base.post_init).build()
    app.add_handler(CommandHandler("about", base.about))
    app.add_handler(CommandHandler("bridgehelp", base.bridgehelp))
    app.add_handler(CommandHandler("ask", base.ask_command))
    app.add_handler(CommandHandler("sakhi_notify", sakhi_notify))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, base.welcome))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, base.chat_message))
    app.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, base.group_activity))
    base.log.info("Silent Sakhi bridge started: automatic quiz/score broadcasts disabled")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
