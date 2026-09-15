from pathlib import Path

def rep(path,old,new):
 p=Path(path);s=p.read_text()
 if new in s:return
 if old not in s:raise SystemExit(f'Patch anchor missing in {path}')
 p.write_text(s.replace(old,new,1))

def repall(path,old,new):
 p=Path(path);s=p.read_text()
 if old in s:p.write_text(s.replace(old,new))

rep('config.py','GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")\n\nDB_PATH = "scores.db"\n\nCORRECT_SCORE = 4\nWRONG_SCORE = -1','GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")\n\n# Secure score sync: set only in Railway Variables.\nSUPABASE_URL = os.environ.get("SUPABASE_URL", "")\nSUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")\n\nDB_PATH = "scores.db"\n\nCORRECT_SCORE = 20\nWRONG_SCORE = -10')
rep('main.py','import database as db\nimport leaderboard','import database as db\nimport supabase_sync\nimport leaderboard')
rep('main.py','/timer <15|30|45|60> — Quiz timer\n\n📊 Stats:','/timer <15|30|45|60> — Quiz timer\n/link <app code> — RATHOD HUB account link करें\n\n📊 Stats:')
rep('main.py','/proquiz <topic> <number> — Ultra-level NCERT/PYQ/Assertion quiz\n/aistatus','/proquiz <topic> <number> — Ultra-level NCERT/PYQ/Assertion quiz\n/highlevel <topic> <number> — +100/-50 high-level quiz\n/guide <question> — RATHOD app guide\n/tutor <question> — AI Tutor Pro\n/plan <subject> <hours> — Study plan\n/notify <message> — Admin group notification\n/coupon <code> <note> — Admin coupon announcement\n/broadcast <message> — Admin broadcast\n/dm <user_id> <message> — Admin direct message\n/aistatus')
link='''async def cmd_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    args = context.args or []
    if not args:
        await update.message.reply_text("🔗 RATHOD HUB के *Telegram Score* से code बनाएँ और भेजें:\n`/link YOUR_CODE`", parse_mode=ParseMode.MARKDOWN)
        return
    u=update.effective_user
    result=await asyncio.to_thread(supabase_sync.confirm_link,args[0],u.id,u.username or "",u.full_name or "Telegram User")
    if result.get("success"):
        await update.message.reply_text("✅ *Telegram account linked!*\nअब सही उत्तर पर `+20 XP` और गलत पर `-10 XP` 13-day League में जुड़ेगा।",parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("❌ Code गलत/expire है। App से नया code बनाएँ।\n`"+str(result.get("error","Unknown error"))+"`",parse_mode=ParseMode.MARKDOWN)

'''
rep('main.py','async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):',link+'async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):')
rep('main.py','    app.add_handler(CommandHandler("timer", cmd_timer))','    app.add_handler(CommandHandler("timer", cmd_timer))\n    app.add_handler(CommandHandler("link", cmd_link))')
rep('main.py','        await quiz_module.handle_poll_answer(context.bot, answer.user.id, answer.poll_id, selected)','        await quiz_module.handle_poll_answer(context.bot, answer.user.id, answer.poll_id, selected, answer.user.username or "", answer.user.full_name or "Telegram User")')
rep('quiz.py','import textwrap\nfrom datetime','import textwrap\nimport supabase_sync\nfrom datetime')
rep('quiz.py','async def handle_poll_answer(bot: Bot, user_id: int, poll_id: str, selected_option: int):','async def handle_poll_answer(bot: Bot, user_id: int, poll_id: str, selected_option: int, username: str = "", name: str = "Telegram User"):')
rep('quiz.py','''    else:
        session["wrong"] += 1
        session["score"] += WRONG_SCORE

async def finish_quiz''','''    else:
        session["wrong"] += 1
        session["score"] += WRONG_SCORE
    await asyncio.to_thread(supabase_sync.record_answer,user_id,session["chat_id"],username,name,selected_option == q["correct_index"],session["topic"])

async def finish_quiz''')
rep('quiz.py','''    else:
        stats["wrong"] += 1
        stats["score"] += WRONG_SCORE

async def _advance_group_after_timeout''','''    else:
        stats["wrong"] += 1
        stats["score"] += WRONG_SCORE
    await asyncio.to_thread(supabase_sync.record_answer,user_id,chat_id,username,name,selected_option == session["current_correct"],session["topic"])

async def _advance_group_after_timeout''')
rep('main.py','import vip_scheduler\nimport multi_provider','import vip_scheduler\nimport rathod_ai\nimport admin_console\nimport multi_provider')
rep('main.py','    await premium_hub.init_commands(application)','    await premium_hub.init_commands(application)\n    await rathod_ai.install(application, db, quiz_module, vip_commands, ADMIN_IDS)\n    await admin_console.install(application, db, ADMIN_IDS)')

# Per-mode scoring: normal quiz +20/-10, PYQ +50/-20, high-level +100/-50.
score_helper='''def _score_values(style: str) -> tuple[int, int]:
    if str(style).lower() == "pyq":
        return 50, -20
    if str(style).lower() in {"pro", "highlevel", "high-level"}:
        return 100, -50
    return CORRECT_SCORE, WRONG_SCORE

'''
rep('quiz.py','\ndef start_session(\n','\n'+score_helper+'def start_session(\n')
rep('quiz.py','        "style": style,\n        "questions": questions,','        "style": style,\n        "correct_xp": _score_values(style)[0],\n        "wrong_xp": _score_values(style)[1],\n        "questions": questions,')
repall('quiz.py','session["score"] += CORRECT_SCORE','session["score"] += session.get("correct_xp", CORRECT_SCORE)')
repall('quiz.py','session["score"] += WRONG_SCORE','session["score"] += session.get("wrong_xp", WRONG_SCORE)')
rep('quiz.py','def start_group_session(chat_id: int, questions: list[dict], topic: str, timer: int) -> dict:','def start_group_session(chat_id: int, questions: list[dict], topic: str, timer: int, style: str = "quiz") -> dict:')
rep('quiz.py','        "chat_id": chat_id,\n        "topic": topic,\n        "questions": questions,','        "chat_id": chat_id,\n        "topic": topic,\n        "style": style,\n        "correct_xp": _score_values(style)[0],\n        "wrong_xp": _score_values(style)[1],\n        "questions": questions,')
repall('quiz.py','stats["score"] += CORRECT_SCORE','stats["score"] += session.get("correct_xp", CORRECT_SCORE)')
repall('quiz.py','stats["score"] += WRONG_SCORE','stats["score"] += session.get("wrong_xp", WRONG_SCORE)')
repall('quiz.py','            topic=str(session.get("topic") or "Quiz"),\n        )','            topic=str(session.get("topic") or "Quiz"),\n            correct_score=int(session.get("correct_xp", CORRECT_SCORE)),\n            wrong_score=int(session.get("wrong_xp", WRONG_SCORE)),\n        )')
rep('vip_commands.py','session = quiz_module.start_group_session(chat_id, questions, title, timer)','session = quiz_module.start_group_session(chat_id, questions, title, timer, style="highlevel")')
rep('vip_commands.py','session = quiz_module.start_session(user.id, chat_id, questions, title, "pro", timer)','session = quiz_module.start_session(user.id, chat_id, questions, title, "highlevel", timer)')
rep('supabase_sync.py','def record_answer(telegram_user_id: int, chat_id: int, username: str, name: str, is_correct: bool, topic: str) -> dict:','def record_answer(telegram_user_id: int, chat_id: int, username: str, name: str, is_correct: bool, topic: str, correct_score: int = 20, wrong_score: int = -10) -> dict:')
rep('supabase_sync.py','"p_is_correct": bool(is_correct), "p_topic": (topic or "Quiz")[:250]','"p_is_correct": bool(is_correct), "p_topic": (topic or "Quiz")[:250], "p_correct_score": int(correct_score), "p_wrong_score": int(wrong_score)')

# python-telegram-bot returns a tuple from get_my_commands(); normalize it before concatenating.
rep('rathod_ai.py','await application.bot.set_my_commands(existing + [x for x in additions if x.command not in known])','await application.bot.set_my_commands(list(existing) + [x for x in additions if x.command not in known])')
rep('admin_console.py','await application.bot.set_my_commands(existing + [x for x in additions if x.command not in known])','await application.bot.set_my_commands(list(existing) + [x for x in additions if x.command not in known])')
print('RATHOD AI, scoring, admin console and startup patches applied.')
