from pathlib import Path

def rep(path,old,new):
 p=Path(path);s=p.read_text()
 if new in s:return
 if old not in s:raise SystemExit(f'Master-lock patch anchor missing: {path}')
 p.write_text(s.replace(old,new,1))

# Quiz bot: block commands, messages and poll scoring while centrally locked.
rep('main.py','import supabase_sync\nfrom quiz import','import supabase_sync\nimport master_control\nfrom quiz import')
rep('main.py','async def check_bot_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:\n    chat = update.effective_chat','async def check_bot_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:\n    if not await asyncio.to_thread(master_control.is_enabled, "quiz_bot"):\n        if update.effective_message:\n            try: await update.effective_message.reply_text("🔐 " + master_control.message())\n            except Exception: pass\n        return False\n    chat = update.effective_chat')
rep('main.py','async def on_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    answer = update.poll_answer','async def on_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    if not await asyncio.to_thread(master_control.is_enabled, "quiz_bot"): return\n    answer = update.poll_answer')
# Scheduled Telegram quizzes must also stop.
rep('vip_scheduler.py','import quiz\n','import quiz\nimport master_control\n')
rep('vip_scheduler.py','async def _run(sid,chat_id,topic,count):\n    if _app is None:return','async def _run(sid,chat_id,topic,count):\n    if _app is None or not await asyncio.to_thread(master_control.is_enabled, "quiz_bot"):return')
# PDF worker pauses without deleting files or events.
rep('question_archive_worker.py','from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer\n','from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer\nimport master_control\n')
rep('question_archive_worker.py','def run_once():\n    start,end=window','def run_once():\n    if not master_control.is_enabled("pdf_worker"):\n        log.info("PDF worker paused by RATHOD master control");return\n    start,end=window')
# Correct group-readable Drive permission endpoint from the earlier archive update.
for bad,good in [('f"{https://www.googleapis.com/drive/v3/files/{file_id}}/permissions?fields=permissions(id,type,role)"','f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?fields=permissions(id,type,role)"'),('f"{https://www.googleapis.com/drive/v3/files/{file_id}}/permissions?fields=id"','f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?fields=id"')]:
 p=Path('question_archive_worker.py');s=p.read_text();p.write_text(s.replace(bad,good))
# Sakhi: every public handler/job is centrally gated; admin controller remains separate.
rep('silent_bridge_bot.py','import bridge_bot as base\n','import bridge_bot as base\nimport master_control\n')
rep('silent_bridge_bot.py','async def app_notifications_only(app: Application) -> None:\n    """Forward immediate admin/app notifications, never ordinary quiz activity."""','async def app_notifications_only(app: Application) -> None:\n    """Forward immediate admin/app notifications, never ordinary quiz activity."""\n    if not await asyncio.to_thread(master_control.is_enabled, "sakhi"): return')
rep('silent_bridge_bot.py','async def motivation_twice_daily(context: ContextTypes.DEFAULT_TYPE) -> None:\n    """Send one shayari per configured hour, with a process and DB guard."""','async def motivation_twice_daily(context: ContextTypes.DEFAULT_TYPE) -> None:\n    """Send one shayari per configured hour, with a process and DB guard."""\n    if not await asyncio.to_thread(master_control.is_enabled, "sakhi"): return')
rep('silent_bridge_bot.py','async def archivepdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:\n    """Return the newest archive Notes and Test PDFs in private chat or the group."""','async def archivepdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:\n    """Return the newest archive Notes and Test PDFs in private chat or the group."""\n    if not await asyncio.to_thread(master_control.is_enabled, "sakhi"): return')
rep('silent_bridge_bot.py','def main() -> None:\n','def gated(handler):\n    async def wrapped(update, context):\n        if not await asyncio.to_thread(master_control.is_enabled, "sakhi"): return\n        return await handler(update, context)\n    return wrapped\n\ndef main() -> None:\n')
for old,new in [('CommandHandler("about", base.about)','CommandHandler("about", gated(base.about))'),('CommandHandler("bridgehelp", bridge_help)','CommandHandler("bridgehelp", gated(bridge_help))'),('CommandHandler("bol", base.ask_command)','CommandHandler("bol", gated(base.ask_command))'),('CommandHandler("sakhi_notify", sakhi_notify)','CommandHandler("sakhi_notify", gated(sakhi_notify))'),('MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, base.welcome)','MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, gated(base.welcome))'),('MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, base.chat_message)','MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, gated(base.chat_message))'),('MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, base.group_activity)','MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, gated(base.group_activity))')]:rep('silent_bridge_bot.py',old,new)
print('RATHOD master lock connected to Quiz Bot, Sakhi and PDF Worker')
