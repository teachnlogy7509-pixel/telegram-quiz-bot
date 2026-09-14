"""Idempotently wire VIP questions, persistent scores and app notifications into main.py."""
from pathlib import Path

p = Path("main.py")
s = p.read_text()

if "import vip_question_engine" not in s:
    s = s.replace("import quiz as quiz_module\n", "import quiz as quiz_module\nimport vip_question_engine\n")
if "import persistent_scores" not in s:
    s = s.replace("import vip_question_engine\n", "import vip_question_engine\nimport persistent_scores\n")
if "import app_update_notifier" not in s:
    s = s.replace("import persistent_scores\n", "import persistent_scores\nimport app_update_notifier\n")

anchor = "ADMIN_IDS = [8043570403]\n"
if "vip_question_engine.install(quiz_module)" not in s:
    s = s.replace(anchor, anchor + "\n# Upgrade every /quiz, /pyq, scheduled and PDF quiz with persistent anti-repeat memory.\nvip_question_engine.install(quiz_module)\n")
if "persistent_scores.install(db, leaderboard, quiz_module)" not in s:
    s = s.replace("vip_question_engine.install(quiz_module)\n", "vip_question_engine.install(quiz_module)\n# Supabase is the score source of truth; SQLite remains an offline fallback.\npersistent_scores.install(db, leaderboard, quiz_module)\n")

commands = '''\n\nasync def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    if not await check_bot_active(update, context):\n        return\n    await update.message.reply_text(f"🆔 Chat ID: `{update.effective_chat.id}`", parse_mode=ParseMode.MARKDOWN)\n\n\nasync def cmd_testupdate(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    if update.effective_user.id not in ADMIN_IDS:\n        return\n    try:\n        sent = await app_update_notifier.check_once(context.bot, force=True, test=True)\n        await update.message.reply_text("✅ Test update notification group में भेज दिया।" if sent else "❌ APP_UPDATE_CHAT_ID missing/invalid या GitHub APK नहीं मिला।")\n    except Exception as exc:\n        await update.message.reply_text(f"❌ Test notification failed: {str(exc)[:250]}")\n\n\nasync def cmd_qtypes(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    if not await check_bot_active(update, context):\n        return\n    await update.message.reply_text(\n        "👑 *RATHOD VIP Question Engine*\\n\\n"\n        "✅ NCERT fact & conceptual\\n"\n        "✅ Statement I/II & Assertion–Reason\\n"\n        "✅ Correct/incorrect combinations\\n"\n        "✅ Match, sequence, case & application\\n"\n        "✅ Numerical/data/PYQ-inspired traps\\n"\n        "✅ Persistent exact + near-duplicate blocking\\n\\n"\n        "Use `/quiz <topic> <number>` or `/pyq <topic> <number>`.",\n        parse_mode=ParseMode.MARKDOWN,\n    )\n'''
if "async def cmd_qtypes" not in s:
    s = s.replace("async def error_handler", commands + "\nasync def error_handler")
elif "async def cmd_testupdate" not in s:
    s = s.replace("async def cmd_qtypes", commands.split("async def cmd_qtypes")[0] + "async def cmd_qtypes", 1)

if "/qtypes — VIP" not in s:
    s = s.replace("/timer <15|30|45|60> — Quiz timer", "/timer <15|30|45|60> — Quiz timer\n/qtypes — VIP question formats और anti-repeat status\n/chatid — Current group Chat ID\n/testupdate — Admin notification test")
elif "/testupdate —" not in s:
    s = s.replace("/chatid — Current group Chat ID", "/chatid — Current group Chat ID\n/testupdate — Admin notification test")

handler_anchor = 'app.add_handler(CommandHandler("help", cmd_help))\n'
if 'CommandHandler("qtypes"' not in s:
    s = s.replace(handler_anchor, handler_anchor + '    app.add_handler(CommandHandler("qtypes", cmd_qtypes))\n    app.add_handler(CommandHandler("chatid", cmd_chatid))\n    app.add_handler(CommandHandler("testupdate", cmd_testupdate))\n')
elif 'CommandHandler("testupdate"' not in s:
    s = s.replace('    app.add_handler(CommandHandler("chatid", cmd_chatid))\n', '    app.add_handler(CommandHandler("chatid", cmd_chatid))\n    app.add_handler(CommandHandler("testupdate", cmd_testupdate))\n')

if "app_update_notifier.init(application)" not in s:
    s = s.replace("sched_module.init_scheduler(application)\n", "sched_module.init_scheduler(application)\n    app_update_notifier.init(application)\n")

p.write_text(s)
print("VIP bot wiring applied")
