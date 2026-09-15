"""Premium RATHOD HUB experience for Telegram."""
from __future__ import annotations
import asyncio
from telegram import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode

APP_URL="https://teachnlogy7509-pixel.github.io/RATHOD-HUB/"
_focus_tasks={}

def _tier(score):
 score=int(score or 0)
 if score>=10000:return "👑 RATHOD LEGEND"
 if score>=5000:return "💎 NEET ELITE"
 if score>=2000:return "🏆 VIP SCHOLAR"
 if score>=500:return "⚡ RISING DOCTOR"
 return "🌱 NEET ASPIRANT"

def keyboard():
 return InlineKeyboardMarkup([
  [InlineKeyboardButton("👑 PRO Quiz",callback_data="rh_pro"),InlineKeyboardButton("⚡ Daily Challenge",callback_data="rh_daily")],
  [InlineKeyboardButton("📊 VIP Profile",callback_data="rh_profile"),InlineKeyboardButton("🏆 Leaderboard",callback_data="rh_leaderboard")],
  [InlineKeyboardButton("📅 Schedules",callback_data="rh_schedule"),InlineKeyboardButton("🤖 AI Status",callback_data="rh_ai")],
  [InlineKeyboardButton("📱 Open RATHOD HUB App",url=APP_URL)],
 ])

async def cmd_hub(update,context,db_module,leaderboard_module):
 user=update.effective_user
 text=("👑 *RATHOD TELEGRAM PREMIUM*\n"
       "━━━━━━━━━━━━━━━━━━\n"
       f"Welcome, *{user.first_name or 'Future Doctor'}* 🩺\n\n"
       "⚡ Multi-AI instant quizzes\n"
       "🧠 NCERT + PRO question engine\n"
       "🏆 Permanent App-linked leaderboard\n"
       "📅 Multiple daily schedules\n"
       "🎯 Focus mode & premium profile\n"
       "━━━━━━━━━━━━━━━━━━\n"
       "अपना command center चुनें:")
 await update.effective_message.reply_text(text,parse_mode=ParseMode.MARKDOWN,reply_markup=keyboard())

async def profile_text(user_id,chat_id,db_module,leaderboard_module):
 row=db_module.get_user(user_id,chat_id) or {}
 score=int(row.get("total_score") or row.get("xp") or 0);correct=int(row.get("correct") or 0);wrong=int(row.get("wrong") or 0);answered=correct+wrong;acc=(correct/answered*100) if answered else 0
 try:rank=leaderboard_module.get_rank(user_id,chat_id)
 except Exception:rank=1
 name=row.get("name") or row.get("username") or "Future Doctor"
 return ("💎 *VIP STUDENT PROFILE*\n"
         "━━━━━━━━━━━━━━━━━━\n"
         f"👤 *{name}*\n"
         f"🎖 {_tier(score)}\n\n"
         f"🏅 Rank: `#{rank}`\n"
         f"⚡ Total XP: `{score}`\n"
         f"✅ Correct: `{correct}`\n"
         f"❌ Wrong: `{wrong}`\n"
         f"🎯 Accuracy: `{acc:.1f}%`\n"
         "━━━━━━━━━━━━━━━━━━\n"
         "RATHOD HUB • Consistency Creates Rank")

async def cmd_profile(update,context,db_module,leaderboard_module):
 text=await profile_text(update.effective_user.id,update.effective_chat.id,db_module,leaderboard_module)
 await update.effective_message.reply_text(text,parse_mode=ParseMode.MARKDOWN,reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📱 Open App Profile",url=APP_URL)]]))

async def cmd_dailychallenge(update,context,quiz_module,db_module,vip_commands):
 old=list(context.args or []);context.args=["Mixed","NEET","NCERT","Challenge","10"]
 try:await vip_commands.cmd_proquiz(update,context,quiz_module,db_module)
 finally:context.args=old

async def cmd_focuspro(update,context):
 try:minutes=int((context.args or [25])[0])
 except ValueError:return await update.effective_message.reply_text("Use: /focuspro <minutes>")
 minutes=max(1,min(180,minutes));key=(update.effective_chat.id,update.effective_user.id)
 old=_focus_tasks.pop(key,None)
 if old:old.cancel()
 await update.effective_message.reply_text(f"🎯 *VIP FOCUS STARTED*\n⏱ {minutes} minutes\n📵 Telegram बंद करके focused study करें।",parse_mode=ParseMode.MARKDOWN)
 async def finish():
  try:
   await asyncio.sleep(minutes*60)
   await context.bot.send_message(chat_id=key[0],text=f"🏆 Focus complete! {minutes} minutes की शानदार study हुई। अब /dailychallenge से revision check करें।")
  except asyncio.CancelledError:pass
 _focus_tasks[key]=asyncio.create_task(finish())

async def cmd_focusstop(update,context):
 key=(update.effective_chat.id,update.effective_user.id);task=_focus_tasks.pop(key,None)
 if task:task.cancel();await update.effective_message.reply_text("⏹ Focus timer stopped.")
 else:await update.effective_message.reply_text("कोई active focus timer नहीं है।")

async def handle_button(update,context,db_module,leaderboard_module,quiz_module):
 q=update.callback_query;await q.answer();data=q.data
 if data=="rh_profile":await q.message.reply_text(await profile_text(update.effective_user.id,update.effective_chat.id,db_module,leaderboard_module),parse_mode=ParseMode.MARKDOWN)
 elif data=="rh_leaderboard":await q.message.reply_text(leaderboard_module.format_leaderboard(update.effective_chat.id),parse_mode=ParseMode.MARKDOWN)
 elif data=="rh_pro":await q.message.reply_text("👑 PRO Quiz: `/proquiz <topic> <number>`\nExample: `/proquiz Genetics 10`",parse_mode=ParseMode.MARKDOWN)
 elif data=="rh_daily":await q.message.reply_text("⚡ Daily Challenge शुरू करने के लिए /dailychallenge भेजें।")
 elif data=="rh_schedule":await q.message.reply_text("📅 `/schedule HH:MM <topic> <number>`\nसभी देखने के लिए /schedulelist",parse_mode=ParseMode.MARKDOWN)
 elif data=="rh_ai":await q.message.reply_text("🤖 Provider status देखने के लिए /aistatus भेजें।")

async def init_commands(application):
 await application.bot.set_my_commands([
  BotCommand("hub","Premium command center"),BotCommand("proquiz","Ultra-level NEET quiz"),BotCommand("dailychallenge","10Q daily VIP challenge"),BotCommand("profile","VIP student profile"),BotCommand("focuspro","Premium focus timer"),BotCommand("focusstop","Stop focus timer"),BotCommand("quiz","Create topic quiz"),BotCommand("pyq","PYQ-style quiz"),BotCommand("leaderboard","Top players"),BotCommand("schedule","Add daily quiz time"),BotCommand("schedulelist","View schedules"),BotCommand("aistatus","AI provider status"),BotCommand("help","All commands")
 ])
