from pathlib import Path


def read(path):
    return Path(path).read_text()


def write(path, text):
    Path(path).write_text(text)


def ensure_import(path, line, anchors):
    text = read(path)
    if line in text:
        return
    for anchor in anchors:
        if anchor in text:
            write(path, text.replace(anchor, line + anchor, 1))
            return
    print(f"Master-lock import skipped: {path}")


def replace_once(path, old_options, new, label):
    text = read(path)
    if new in text:
        return
    for old in old_options:
        if old in text:
            write(path, text.replace(old, new, 1))
            return
    print(f"Master-lock section skipped: {label}")


# Quiz bot: central switch blocks command/message checks and poll scoring.
ensure_import("main.py", "import master_control\n", ["from quiz import", "import supabase_sync\n"])
replace_once(
    "main.py",
    [
        "async def check_bot_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:\n    chat = update.effective_chat",
    ],
    """async def check_bot_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:\n    if not await asyncio.to_thread(master_control.is_enabled, \"quiz_bot\"):\n        if update.effective_message:\n            try: await update.effective_message.reply_text(\"🔐 \" + master_control.message())\n            except Exception: pass\n        return False\n    chat = update.effective_chat""",
    "main.py check_bot_active",
)
replace_once(
    "main.py",
    ["async def on_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    answer = update.poll_answer"],
    """async def on_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    if not await asyncio.to_thread(master_control.is_enabled, \"quiz_bot\"): return\n    answer = update.poll_answer""",
    "main.py poll gate",
)

# Scheduled Telegram quizzes must stop with the same switch.
ensure_import("vip_scheduler.py", "import master_control\n", ["import quiz\n", "import config\n"])
replace_once(
    "vip_scheduler.py",
    ["async def _run(sid,chat_id,topic,count):\n    if _app is None:return"],
    """async def _run(sid,chat_id,topic,count):\n    if _app is None or not await asyncio.to_thread(master_control.is_enabled, \"quiz_bot\"):return""",
    "vip_scheduler.py scheduled gate",
)

# PDF worker: pause before reading or publishing archive files.
ensure_import(
    "question_archive_worker.py",
    "import master_control\n",
    [
        "from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer\n",
        "from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer\n",
    ],
)
replace_once(
    "question_archive_worker.py",
    [
        "def run_once() -> None:\n    start, end = window(datetime.now(timezone.utc))",
        "def run_once():\n    start,end=window",
    ],
    """def run_once() -> None:\n    if not master_control.is_enabled(\"pdf_worker\"):\n        log.info(\"PDF worker paused by RATHOD master control\")\n        return\n    start, end = window(datetime.now(timezone.utc))""",
    "question_archive_worker.py PDF gate",
)

# Sakhi: stop polling, scheduled motivation, archive delivery and handlers.
ensure_import("silent_bridge_bot.py", "import master_control\n", ["import bridge_bot as base\n"])
replace_once(
    "silent_bridge_bot.py",
    [
        "async def app_notifications_only(app: Application) -> None:\n    \"\"\"Forward immediate admin/app notifications, never ordinary quiz activity.\"\"\"",
    ],
    """async def app_notifications_only(app: Application) -> None:\n    \"\"\"Forward immediate admin/app notifications, never ordinary quiz activity.\"\"\"\n    if not await asyncio.to_thread(master_control.is_enabled, \"sakhi\"): return""",
    "silent_bridge_bot.py app notifications gate",
)
replace_once(
    "silent_bridge_bot.py",
    [
        "async def motivation_twice_daily(context: ContextTypes.DEFAULT_TYPE) -> None:\n    \"\"\"Send one shayari per configured hour, with a process and DB guard.\"\"\"",
    ],
    """async def motivation_twice_daily(context: ContextTypes.DEFAULT_TYPE) -> None:\n    \"\"\"Send one shayari per configured hour, with a process and DB guard.\"\"\"\n    if not await asyncio.to_thread(master_control.is_enabled, \"sakhi\"): return""",
    "silent_bridge_bot.py motivation gate",
)
replace_once(
    "silent_bridge_bot.py",
    [
        "async def archivepdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:\n    \"\"\"Return the newest archive Notes and Test PDFs in private chat or the group.\"\"\"",
    ],
    """async def archivepdf(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:\n    \"\"\"Return the newest archive Notes and Test PDFs in private chat or the group.\"\"\"\n    if not await asyncio.to_thread(master_control.is_enabled, \"sakhi\"): return""",
    "silent_bridge_bot.py archive gate",
)
replace_once(
    "silent_bridge_bot.py",
    ["async def post_init(app: Application) -> None:\n"],
    """async def gated_poll_job(context: ContextTypes.DEFAULT_TYPE) -> None:\n    if not await asyncio.to_thread(master_control.is_enabled, \"sakhi\"): return\n    return await base.poll_job(context)\n\n\nasync def post_init(app: Application) -> None:\n""",
    "silent_bridge_bot.py poll gate",
)
replace_once(
    "silent_bridge_bot.py",
    ["base.poll_job, interval=base.POLL_SECONDS"],
    "gated_poll_job, interval=base.POLL_SECONDS",
    "silent_bridge_bot.py scheduled poll replacement",
)
replace_once(
    "silent_bridge_bot.py",
    ["def main() -> None:\n"],
    """def gated(handler):\n    async def wrapped(update, context):\n        if not await asyncio.to_thread(master_control.is_enabled, \"sakhi\"): return\n        return await handler(update, context)\n    return wrapped\n\n\ndef main() -> None:\n""",
    "silent_bridge_bot.py handler gate",
)
for old, new in [
    ('CommandHandler("about", base.about)', 'CommandHandler("about", gated(base.about))'),
    ('CommandHandler("bridgehelp", bridge_help)', 'CommandHandler("bridgehelp", gated(bridge_help))'),
    ('CommandHandler("bol", base.ask_command)', 'CommandHandler("bol", gated(base.ask_command))'),
    ('CommandHandler("archivepdf", archivepdf)', 'CommandHandler("archivepdf", gated(archivepdf))'),
    ('CommandHandler("sakhi_notify", sakhi_notify)', 'CommandHandler("sakhi_notify", gated(sakhi_notify))'),
    ('MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, base.welcome)', 'MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, gated(base.welcome))'),
    ('MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, base.chat_message)', 'MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, gated(base.chat_message))'),
    ('MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, base.group_activity)', 'MessageHandler(filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND, gated(base.group_activity))'),
]:
    replace_once("silent_bridge_bot.py", [old], new, f"silent_bridge_bot.py handler {old[:30]}")

print("RATHOD master lock connected to Quiz Bot, Sakhi and PDF Worker")
