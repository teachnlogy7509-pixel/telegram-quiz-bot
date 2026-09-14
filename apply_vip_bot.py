"""Idempotently wire the VIP question engine and professional commands into main.py."""
from pathlib import Path

p = Path("main.py")
s = p.read_text()

if "import vip_question_engine" not in s:
    s = s.replace("import quiz as quiz_module\n", "import quiz as quiz_module\nimport vip_question_engine\n")

anchor = "ADMIN_IDS = [8043570403]\n"
if "vip_question_engine.install(quiz_module)" not in s:
    s = s.replace(anchor, anchor + "\n# Upgrade every /quiz, /pyq, scheduled and PDF quiz with persistent anti-repeat memory.\nvip_question_engine.install(quiz_module)\n")

commands = '''\n\nasync def cmd_chatid(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    """Show the exact Telegram chat ID needed for Railway update announcements."""\n    if not await check_bot_active(update, context):\n        return\n    await update.message.reply_text(f"🆔 Chat ID: `{update.effective_chat.id}`", parse_mode=ParseMode.MARKDOWN)\n\n\nasync def cmd_qtypes(update: Update, context: ContextTypes.DEFAULT_TYPE):\n    if not await check_bot_active(update, context):\n        return\n    await update.message.reply_text(\n        "👑 *RATHOD VIP Question Engine*\\n\\n"\n        "✅ NCERT fact & conceptual\\n"\n        "✅ Statement I/II & Assertion–Reason\\n"\n        "✅ Correct/incorrect combinations\\n"\n        "✅ Match, sequence, case & application\\n"\n        "✅ Numerical/data/PYQ-inspired traps\\n"\n        "✅ Persistent exact + near-duplicate blocking\\n\\n"\n        "Use `/quiz <topic> <number>` or `/pyq <topic> <number>`.",\n        parse_mode=ParseMode.MARKDOWN,\n    )\n'''
if "async def cmd_qtypes" not in s:
    s = s.replace("async def error_handler", commands + "\nasync def error_handler")

if "/qtypes — VIP" not in s:
    s = s.replace("/timer <15|30|45|60> — Quiz timer", "/timer <15|30|45|60> — Quiz timer\n/qtypes — VIP question formats और anti-repeat status\n/chatid — Current group Chat ID")

handler_anchor = 'app.add_handler(CommandHandler("help", cmd_help))\n'
if 'CommandHandler("qtypes"' not in s:
    s = s.replace(handler_anchor, handler_anchor + '    app.add_handler(CommandHandler("qtypes", cmd_qtypes))\n    app.add_handler(CommandHandler("chatid", cmd_chatid))\n')

p.write_text(s)
print("VIP bot wiring applied")
