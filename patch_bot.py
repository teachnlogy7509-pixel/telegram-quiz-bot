from pathlib import Path

def rep(path,old,new):
 p=Path(path);s=p.read_text()
 if new in s:return
 if old not in s:raise SystemExit(f'Patch anchor missing in {path}')
 p.write_text(s.replace(old,new,1))

rep('config.py','GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")\n\nDB_PATH = "scores.db"\n\nCORRECT_SCORE = 4\nWRONG_SCORE = -1','GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")\n\n# Secure score sync: set only in Railway Variables.\nSUPABASE_URL = os.environ.get("SUPABASE_URL", "")\nSUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")\n\nDB_PATH = "scores.db"\n\nCORRECT_SCORE = 20\nWRONG_SCORE = -10')
rep('main.py','import database as db\nimport leaderboard','import database as db\nimport supabase_sync\nimport leaderboard')
rep('main.py','/timer <15|30|45|60> — Quiz timer\n\n📊 Stats:','/timer <15|30|45|60> — Quiz timer\n/link <app code> — RATHOD HUB account link करें\n\n📊 Stats:')
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
print('Telegram score integration patch applied.')
