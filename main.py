"""
Telegram Quiz Bot — main entry point.
python-telegram-bot v21+
"""
import asyncio
import json
import logging
import re
import sys
import random
import os
import yt_dlp

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, ContextTypes,
                          MessageHandler, PollAnswerHandler, filters, ConversationHandler)

import config
import database
import database as db
import leaderboard
import quiz as quiz_module
import scheduler as sched_module
from quiz import verify_gemini_key

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── Admin Settings ─────────────────────────────────────────────
ADMIN_IDS = [8043570403]


# --- ADMIN PDF FILE MANAGER LOGIC ---
WAITING_FOR_FILE, WAITING_FOR_NAME = range(2)

async def addfile_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ केवल Admin ही फाइल्स अपलोड कर सकते हैं।")
        return ConversationHandler.END
    
    await update.message.reply_text("📂 कृपया PDF या Document फाइल भेजें। (रद्द करने के लिए /cancel टाइप करें)")
    return WAITING_FOR_FILE

async def addfile_receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document:
        await update.message.reply_text("⚠️ कृपया एक मान्य फाइल/Document भेजें।")
        return WAITING_FOR_FILE
    
    context.user_data['temp_file_id'] = update.message.document.file_id
    await update.message.reply_text("✅ फाइल प्राप्त हुई! अब इस फाइल का नाम टाइप करके भेजें (जैसे: Biology Notes)।")
    return WAITING_FOR_NAME

async def addfile_receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = update.message.text.strip()
    file_id = context.user_data.get('temp_file_id')
    uploader_id = update.effective_user.id
    
    if db.save_pdf(file_name, file_id, uploader_id):
        await update.message.reply_text(f"🎉 फाइल सफलतापूर्वक '{file_name}' नाम से सेव हो गई!")
    else:
        await update.message.reply_text(f"⚠️ '{file_name}' नाम से फाइल पहले ही मौजूद है। कृपया कोई और नाम दें।")
    
    context.user_data.clear()
    return ConversationHandler.END

async def addfile_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🚫 फाइल अपलोड रद्द कर दिया गया है।")
    return ConversationHandler.END

async def send_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ सही तरीका: /file <नाम>\nउदाहरण: /file Biology Notes")
        return
    
    file_name = " ".join(context.args)
    file_id = db.get_pdf(file_name)
    
    if file_id:
        await update.message.reply_text(f"📤 '{file_name}' भेजी जा रही है...")
        await context.bot.send_document(chat_id=update.effective_chat.id, document=file_id)
    else:
        await update.message.reply_text("❌ यह फाइल नहीं मिली। लिस्ट देखने के लिए /files का उपयोग करें।")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = db.list_pdfs()
    if not files:
        await update.message.reply_text("📭 अभी तक कोई फाइल उपलब्ध नहीं है।")
        return
    
    text = "📚 **Available Files:**\n\n"
    for f in files:
        text += f"▪️ `{f}`\n"
    text += "\nप्राप्त करने के लिए टाइप करें: `/file <नाम>`"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ── Help text ─────────────────────────────────────────────────────────────────
HELP_TEXT = """
🤖 *Telegram Quiz Bot*

*Commands:*
/quiz `<topic> <number>` — Start a quiz
/pyq `<topic> <number>` — PYQ-style quiz
/leaderboard — Top 10 players
/myrank — Your stats & rank
/toptoday — Today's top scores
/resetscore — Reset your score
/timer `<15|30|45|60>` — Set quiz timer
/schedule `<topic> <number>` — Daily quiz
/scheduleoff — Stop the daily quiz
/schedulelist — View current schedule

🌟 *Fun & Group Features:*
/shayari — Random Romantic Shayari
/gm — Good Morning Message
/lovememe — Random Love Meme
/song `<name>` — Download & play a song
/confess `<msg>` — Send anonymous confession (DM only)
/mystats — Check your Chat XP Level

🎙 *Voice:* Send a voice message like _"Biology 10 questions"_
""".strip()


# ── Command handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    await update.message.reply_text(
        f"👋 Welcome, *{user.first_name}*!\n\n{HELP_TEXT}",
        parse_mode=ParseMode.MARKDOWN,
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)


async def _start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, style: str):
    user    = update.effective_user
    chat_id = update.effective_chat.id
    args    = context.args or []

    cmd = "/quiz" if style == "quiz" else "/pyq"
    if len(args) < 2:
        await update.message.reply_text(f"Usage: `{cmd} <topic> <number>`\nExample: `{cmd} Physics 10`", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        count = int(args[-1])
    except ValueError:
        await update.message.reply_text(f"❗ Last argument must be a number.")
        return

    if not (1 <= count <= 50):
        await update.message.reply_text("❗ Number of questions must be between 1 and 50.")
        return
    topic = " ".join(args[:-1])

    if user.id in quiz_module.active_sessions:
        await update.message.reply_text("⚠️ You already have an active quiz running.")
        return

    database.ensure_user(user.id, chat_id, user.username, user.full_name)
    timer = database.get_group_timer(chat_id)

    wait_msg = await update.message.reply_text(f"⏳ Generating *{count}* questions on *{topic}*…", parse_mode=ParseMode.MARKDOWN)

    try:
        questions = await quiz_module.generate_questions(topic, count, style)
    except Exception as exc:
        await wait_msg.edit_text("❌ Failed to generate questions.")
        return

    if not questions:
        await wait_msg.edit_text("❌ Could not generate any questions. Try a different topic.")
        return

    actual = len(questions)
    try:
        await wait_msg.delete()
    except Exception:
        pass

    label = "📝 PYQ Quiz" if style == "pyq" else "📚 Quiz"
    bot = context.bot

    if chat_id < 0:
        session = quiz_module.start_group_session(chat_id, questions, f"{topic} ({label})", timer)
        await update.message.reply_text(
            f"👥 *Group {label} starting!*\n*Topic:* {topic}\n*Questions:* {actual}\n⏱ Timer: *{timer}s*",
            parse_mode=ParseMode.MARKDOWN,
        )
        await quiz_module.send_group_question(bot, session)
        task = asyncio.create_task(quiz_module._advance_group_after_timeout(bot, chat_id, 0))
        session["advance_job"] = task
    else:
        session = quiz_module.start_session(user.id, chat_id, questions, topic, style, timer)
        await update.message.reply_text(
            f"👤 *{label} starting!*\n*Topic:* {topic}\n*Questions:* {actual}\n⏱ Timer: *{timer}s*",
            parse_mode=ParseMode.MARKDOWN,
        )
        await quiz_module.send_question(bot, session)
        task = asyncio.create_task(quiz_module._advance_after_timeout(bot, user.id, 0))
        session["advance_job"] = task

async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _start_quiz(update, context, style="quiz")

async def cmd_pyq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _start_quiz(update, context, style="pyq")

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(leaderboard.format_leaderboard(chat_id), parse_mode=ParseMode.MARKDOWN)

async def cmd_myrank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    await update.message.reply_text(leaderboard.format_my_rank(user.id, chat_id), parse_mode=ParseMode.MARKDOWN)

async def cmd_toptoday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(leaderboard.format_today_top(chat_id), parse_mode=ParseMode.MARKDOWN)

async def cmd_resetscore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    database.reset_score(user.id, chat_id)
    await update.message.reply_text(f"🔄 *{user.first_name}*, your score has been reset.", parse_mode=ParseMode.MARKDOWN)

async def cmd_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args or []
    if not args or not args[0].isdigit() or int(args[0]) not in {15, 30, 45, 60}:
        await update.message.reply_text("Usage: `/timer 15|30|45|60`", parse_mode=ParseMode.MARKDOWN)
        return
    database.set_group_timer(chat_id, int(args[0]))
    await update.message.reply_text(f"✅ Timer set to *{args[0]}s*", parse_mode=ParseMode.MARKDOWN)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Keeping voice handler simple placeholder as per original, assuming it works with quiz module
    await update.message.reply_text("🎙 Voice processing is currently active only via API setup.")

async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    args = context.args or []
    if len(args) < 2:
        return
    topic = " ".join(args[:-1])
    sched_module.add_schedule(chat_id, topic, int(args[-1]))
    await update.message.reply_text("✅ Daily Quiz Scheduled!", parse_mode=ParseMode.MARKDOWN)

async def cmd_scheduleoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sched_module.remove_schedule(update.effective_chat.id)
    await update.message.reply_text("✅ Schedule turned off.")

async def cmd_schedulelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Check active schedules.", parse_mode=ParseMode.MARKDOWN)

async def on_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    if answer.poll_id in quiz_module.poll_to_user:
        await quiz_module.handle_poll_answer(context.bot, answer.user.id, answer.poll_id, answer.option_ids[0])
    elif answer.poll_id in quiz_module.poll_to_chat:
        chat_id = quiz_module.poll_to_chat[answer.poll_id]
        name = answer.user.full_name or "User"
        await quiz_module.handle_group_poll_answer(context.bot, chat_id, answer.user.id, name, "", answer.poll_id, answer.option_ids[0])

# ── Fun Commands ─────────────────────────────────────────────────────────────

async def cmd_shayari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shayaris = [
        "चाँदनी चाँद से होती है, सितारों से नहीं...\nमोहब्बत एक से होती है, हज़ारों से नहीं! ❤️",
        "खुदा करे ज़िंदगी में ये मकाम आए...\nतुझे भूलने की दुआ करूँ और दुआ में तेरा नाम आए! 🌹",
        "ना चाँद की चाहत, ना तारों की फरमाइश...\nहर जनम तू ही मिले, बस यही है ख्वाहिश! ✨"
    ]
    await update.message.reply_text(random.choice(shayaris))

async def cmd_gm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gms = [
        "Good Morning Khushboo! ☀️ उठो और आज एक नया वायरल YouTube Short बनाओ! 🎥✨",
        "Good Morning! ☀️ दिन की शुरुआत एक प्यारी सी स्माइल के साथ करो!",
        "सुबह की किरण आपको हर खुशी दे! Good Morning! 🌼",
        "उठो, मुस्कुराओ और आज के दिन को शानदार बनाओ! Good Morning! ☕️"
    ]
    await update.message.reply_text(random.choice(gms))

async def cmd_lovememe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    memes = [
        "https://i.pinimg.com/736x/2b/9a/99/2b9a99ea7035ce4a25501314ecf1489e.jpg",
        "https://i.pinimg.com/736x/88/47/43/8847434771cb1ba1552a9261fb586a11.jpg"
    ]
    await update.message.reply_photo(photo=random.choice(memes), caption="For you! ❤️")

# ── New Mega Features (Confession, Song, XP) ─────────────────────────────────

async def cmd_confess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != 'private':
        await update.message.reply_text("🤫 यह कमांड सिर्फ मेरे DM (Private Chat) में काम करता है!")
        return
        
    confession_text = " ".join(context.args)
    if not confession_text:
        await update.message.reply_text("❌ इस्तेमाल का तरीका: /confess <आपका सीक्रेट मैसेज>")
        return
        
    group_id = db.get_latest_group_for_user(update.effective_user.id)
    if not group_id:
        await update.message.reply_text("❌ मुझे नहीं पता कि आप किस ग्रुप में हैं। कृपया पहले मेन ग्रुप में एक मैसेज भेजें!")
        return
        
    try:
        await context.bot.send_message(
            chat_id=group_id, 
            text=f"🤫 *New Anonymous Confession:*\n\n{confession_text}",
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ आपका सीक्रेट मैसेज ग्रुप में गुमनाम रूप से भेज दिया गया है!")
    except Exception as e:
        await update.message.reply_text("❌ मैसेज भेजने में कोई दिक्कत आई।")

async def cmd_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    song_name = " ".join(context.args)
    if not song_name:
        await update.message.reply_text("❌ इस्तेमाल का तरीका: /song <गाने का नाम>")
        return
        
    msg = await update.message.reply_text("🎵 आपका गाना ढूँढ कर डाउनलोड किया जा रहा है... थोड़ा इंतज़ार करें!")
    
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': 'downloaded_song.%(ext)s',
        'noplaylist': True,
        'quiet': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{song_name}", download=True)
            audio_file = ydl.prepare_filename(info['entries'][0])
            
            await context.bot.send_audio(
                chat_id=update.effective_chat.id,
                audio=open(audio_file, 'rb'),
                caption=f"🎧 Here is your song: {song_name}",
                title=info['entries'][0].get('title', song_name)
            )
            os.remove(audio_file)
            await msg.delete()
    except Exception as e:
        await msg.edit_text("❌ माफ़ करें, यह गाना नहीं मिल पाया।")

async def handle_normal_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type in ['group', 'supergroup'] and update.message and update.message.text:
        user = update.effective_user
        db.ensure_user(user.id, update.effective_chat.id, user.username, user.first_name)
        db.add_xp(user.id, update.effective_chat.id, 1)

async def cmd_mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ कृपया इसे ग्रुप में यूज़ करें!")
        return
        
    user = db.get_user(update.effective_user.id, update.effective_chat.id)
    if not user:
        await update.message.reply_text("❌ आपका कोई रिकॉर्ड नहीं मिला!")
        return
        
    xp = user.get('xp', 0)
    level = xp // 100
    
    if level < 2:
        title = "👶 Beginner"
    elif level < 5:
        title = "⚔️ Pro"
    elif level < 10:
        title = "🔥 Master"
    else:
        title = "👑 Legend"
        
    stats_text = (
        f"📊 *GAMING STATS FOR {user['name']}*\n\n"
        f"🔹 *Level:* {level} ({title})\n"
        f"✨ *Total XP:* {xp} XP\n"
        f"🏆 *Total Quiz Score:* {user['total_score']}\n"
    )
    await update.message.reply_text(stats_text, parse_mode="Markdown")

async def _post_init(application: Application):
    sched_module.init_scheduler(application)

# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    if not config.TELEGRAM_BOT_TOKEN:
        sys.exit(1)
    if not config.GEMINI_API_KEY:
        sys.exit(1)

    database.init_db()
    verify_gemini_key()

    app = (
        Application.builder()
        .token(config.TELEGRAM_BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    app.add_handler(CommandHandler("start",        cmd_start))
    app.add_handler(CommandHandler("help",         cmd_help))
    app.add_handler(CommandHandler("quiz",         cmd_quiz))
    app.add_handler(CommandHandler("pyq",          cmd_pyq))
    app.add_handler(CommandHandler("leaderboard",  cmd_leaderboard))
    app.add_handler(CommandHandler("myrank",       cmd_myrank))
    app.add_handler(CommandHandler("toptoday",     cmd_toptoday))
    app.add_handler(CommandHandler("resetscore",   cmd_resetscore))
    app.add_handler(CommandHandler("timer",        cmd_timer))
    app.add_handler(CommandHandler("schedule",     cmd_schedule))
    app.add_handler(CommandHandler("scheduleoff",  cmd_scheduleoff))
    app.add_handler(CommandHandler("schedulelist", cmd_schedulelist))
    
    # Fun & Mega Commands
    app.add_handler(CommandHandler("shayari", cmd_shayari))
    app.add_handler(CommandHandler("gm", cmd_gm))
    app.add_handler(CommandHandler("lovememe", cmd_lovememe))
    app.add_handler(CommandHandler("confess", cmd_confess))
    app.add_handler(CommandHandler("song", cmd_song))
    app.add_handler(CommandHandler("mystats", cmd_mystats))

    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    # Catch all normal text messages to award XP
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_normal_message))
    
    app.add_handler(PollAnswerHandler(on_poll_answer))
    
    db.init_pdf_db()
    addfile_conv = ConversationHandler(
        entry_points=[CommandHandler('addfile', addfile_start)],
        states={
            WAITING_FOR_FILE: [MessageHandler(filters.Document.ALL, addfile_receive_file)],
            WAITING_FOR_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, addfile_receive_name)]
        },
        fallbacks=[CommandHandler('cancel', addfile_cancel)]
    )
    
    app.add_handler(addfile_conv)
    app.add_handler(CommandHandler('file', send_file))
    app.add_handler(CommandHandler('files', list_files))

    logger.info("Bot polling for updates …")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
