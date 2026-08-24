import asyncio
import json
import logging
import re
import sys
import random
import os
import tempfile
import shutil
import yt_dlp
from urllib.parse import quote_plus
from datetime import datetime, timedelta

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (Application, CommandHandler, ContextTypes,
                         MessageHandler, PollAnswerHandler, filters, ConversationHandler)

import config
import database as db
import leaderboard
import quiz as quiz_module
import scheduler as sched_module
from quiz import verify_gemini_key, verify_groq_keys, generate_voice_response, generate_questions_from_pdf

# Logging
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Admin Settings
ADMIN_IDS = [8043570403]

# ADMIN CONTROL MIDDLEWARE
async def check_bot_active(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat is None or user is None:
        return True

    chat_id = chat.id
    user_id = user.id

    # Admin can always use /on even when the chat is paused.
    if update.message and update.message.text:
        text = update.message.text.strip()
        if text.startswith('/on') and user_id in ADMIN_IDS:
            return True

    active = db.is_bot_active(chat_id)
    if active:
        return True

    # Never silently drop commands: explain why the bot did not respond.
    if update.message:
        try:
            await update.message.reply_text(
                "⏸️ Bot अभी इस chat में PAUSED है। Admin `/on` भेजकर इसे चालू कर सकता है।",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception:
            logger.exception("Failed to send bot-paused notice")
    return False

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    err = context.error
    logger.exception("Unhandled Telegram update error", exc_info=err)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Bot में error आया। Admin Railway logs देखें।"
            )
    except Exception:
        logger.exception("Failed to send error message to user")

async def cmd_bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    chat_id = update.effective_chat.id
    db.set_bot_status(chat_id, True)
    await update.message.reply_text("🟢 *Bot is now ACTIVE!* अब बोट सभी मैसेज और कमांड का जवाब देगा।", parse_mode=ParseMode.MARKDOWN)

async def cmd_bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    chat_id = update.effective_chat.id
    db.set_bot_status(chat_id, False)
    await update.message.reply_text("🔴 *Bot is now PAUSED!* अब बोट किसी भी मैसेज या कमांड का जवाब नहीं देगा।", parse_mode=ParseMode.MARKDOWN)

# PDF FILE MANAGER
WAITING_FOR_FILE, WAITING_FOR_NAME = range(2)

async def addfile_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
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
    await update.message.reply_text("✅ फाइल प्राप्त हुई! अब इस फाइल का नाम टाइप करके भेजें।")
    return WAITING_FOR_NAME

async def addfile_receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_name = update.message.text.strip()
    file_id = context.user_data.get('temp_file_id')
    uploader_id = update.effective_user.id
    if db.save_pdf(file_name, file_id, uploader_id):
        await update.message.reply_text(f"🎉 फाइल सफलतापूर्व�� '{file_name}' नाम से सेव हो गई!")
    else:
        await update.message.reply_text(f"⚠️ '{file_name}' नाम से फाइल पहले ही मौजूद है।")
    context.user_data.clear()
    return ConversationHandler.END

async def addfile_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("🚫 फाइल अपलोड रद्द कर दिया गया है।")
    return ConversationHandler.END

async def cmd_pdfquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate MCQs from a saved PDF: /pdfquiz <file name> <number>."""
    if not await check_bot_active(update, context):
        return

    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text(
            "📄 इस्तेमाल: /pdfquiz <PDF का नाम> <प्रश्नों की संख्या>\n"
            "उदाहरण: /pdfquiz Biology Chapter 1 10"
        )
        return

    try:
        count = int(args[-1])
    except ValueError:
        await update.message.reply_text("❗ आखिरी में प्रश्नों की संख्या दें, जैसे: /pdfquiz Biology 10")
        return

    if not 1 <= count <= 50:
        await update.message.reply_text("❗ प्रश्नों की संख्या 1 से 50 के बीच रखें।")
        return

    file_name = " ".join(args[:-1]).strip()
    file_id = db.get_pdf(file_name)
    if not file_id:
        await update.message.reply_text(
            f"❌ '{file_name}' नाम की PDF नहीं मिली। पहले /files से नाम देखें।"
        )
        return

    wait_msg = await update.message.reply_text(
        f"📄 *{file_name}* से {count} प्रश्न बनाए जा रहे हैं…\n"
        "⏳ PDF को Gemini पढ़ रहा है।",
        parse_mode=ParseMode.MARKDOWN,
    )

    temp_path = None
    try:
        tg_file = await context.bot.get_file(file_id)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            temp_path = tmp.name
        await tg_file.download_to_drive(temp_path)

        with open(temp_path, "rb") as fh:
            pdf_bytes = fh.read()

        if len(pdf_bytes) > 20 * 1024 * 1024:
            raise RuntimeError("PDF बहुत बड़ी है। कृपया 20 MB से छोटी PDF इस्तेमाल करें।")

        questions = await generate_questions_from_pdf(pdf_bytes, file_name, count)

        try:
            await wait_msg.delete()
        except Exception:
            pass

        chat_id = update.effective_chat.id
        user = update.effective_user
        timer = db.get_group_timer(chat_id)

        if chat_id < 0:
            session = quiz_module.start_group_session(
                chat_id, questions, f"PDF: {file_name}", timer
            )
            await update.message.reply_text(
                f"📄 *PDF Quiz शुरू!*\n\n📚 {file_name}\n❓ Questions: {len(questions)}",
                parse_mode=ParseMode.MARKDOWN,
            )
            await quiz_module.send_group_question(context.bot, session)
            task = asyncio.create_task(
                quiz_module._advance_group_after_timeout(context.bot, chat_id, 0)
            )
            session["advance_job"] = task
        else:
            db.ensure_user(user.id, chat_id, user.username, user.full_name)
            session = quiz_module.start_session(
                user.id, chat_id, questions, f"PDF: {file_name}", "quiz", timer
            )
            await update.message.reply_text(
                f"📄 *PDF Quiz शुरू!*\n\n📚 {file_name}\n❓ Questions: {len(questions)}",
                parse_mode=ParseMode.MARKDOWN,
            )
            await quiz_module.send_question(context.bot, session)
            task = asyncio.create_task(
                quiz_module._advance_after_timeout(context.bot, user.id, 0)
            )
            session["advance_job"] = task

    except Exception as exc:
        logger.exception("PDF quiz failed")
        await wait_msg.edit_text(
            "❌ PDF से questions नहीं बन पाए।\n\n"
            f"कारण: {str(exc)[:300]}"
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


async def send_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    if not context.args:
        await update.message.reply_text("⚠️ सही तरीका: /file <नाम>")
        return
    file_name = " ".join(context.args)
    file_id = db.get_pdf(file_name)
    if file_id:
        await update.message.reply_text(f"📤 '{file_name}' भेजी जा रही है...")
        await context.bot.send_document(chat_id=update.effective_chat.id, document=file_id)
    else:
        await update.message.reply_text("❌ यह फाइल नहीं मिली। लिस्ट देखने के लिए /files का उपयोग करें।")

async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    files = db.list_pdfs()
    if not files:
        await update.message.reply_text("📭 अभी तक कोई फाइल उपलब्ध नहीं है।")
        return
    text = "📚 Available Files:\n\n"
    for f in files:
        text += f"▪️ `{f}`\n"
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

HELP_TEXT = """
🤖 Telegram Quiz Bot

⚙️ Admin Controls:
/on — Bot ON
/off — Bot OFF

📚 Quiz & Study:
/quiz <topic> <number> — Quiz शुरू करें
/pyq <topic> <number> — PYQ-style quiz
/pdfquiz <PDF name> <number> — PDF से quiz
/timer <15|30|45|60> — Quiz timer

📊 Stats:
/leaderboard — Top 10 players
/myrank — अपनी rank और stats
/toptoday — आज के top scores
/mystats — XP और quiz stats
/resetscore — अपना score reset

📅 Daily Quiz:
/schedule <topic> <number> — रोज 9 PM quiz
/scheduleoff — Daily schedule बंद करें
/schedulelist — Current schedule देखें

📁 PDF Library:
/addfile — PDF/Document save करें
/files — Saved files देखें
/file <नाम> — File भेजें

🎵 Song:
/song <गाने का नाम> — Song search link
/song — Reply किए गए Telegram audio को दोबारा भेजें

🌟 Fun:
/shayari
/gm
/confess <message> — DM से confession
""".strip()

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    user    = update.effective_user
    chat_id = update.effective_chat.id
    db.ensure_user(user.id, chat_id, user.username, user.full_name)
    await update.message.reply_text(f"👋 Welcome, *{user.first_name}*!\n\n{HELP_TEXT}", parse_mode=ParseMode.MARKDOWN)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN)

async def _start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, style: str):
    if not await check_bot_active(update, context): return
    user    = update.effective_user
    chat_id = update.effective_chat.id
    args    = context.args or []
    cmd = "/quiz" if style == "quiz" else "/pyq"
    if len(args) < 2:
        await update.message.reply_text(f"Usage: `{cmd} <topic> <number>`", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        count = int(args[-1])
    except ValueError:
        await update.message.reply_text("❗ Last argument must be a number.")
        return
    if not (1 <= count <= 50):
        await update.message.reply_text("❗ Number must be between 1 and 50.")
        return
    topic = " ".join(args[:-1])

    if user.id in quiz_module.active_sessions:
        await update.message.reply_text("⚠️ You already have an active quiz running.")
        return

    db.ensure_user(user.id, chat_id, user.username, user.full_name)
    timer = db.get_group_timer(chat_id)
    wait_msg = await update.message.reply_text(f"⏳ Generating *{count}* questions on *{topic}*…", parse_mode=ParseMode.MARKDOWN)

    try:
        questions = await quiz_module.generate_questions(topic, count, style)
    except Exception as exc:
        logger.error("Question generation failed: %s", exc)
        await wait_msg.edit_text("❌ Failed to generate questions. Gemini may be temporarily unavailable. Please try again later.")
        return

    if not questions:
        await wait_msg.edit_text("❌ Could not generate any questions.")
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
        await update.message.reply_text(f"👥 Group {label} starting!\nTopic: {topic}\nQuestions: {actual}", parse_mode=ParseMode.MARKDOWN)
        await quiz_module.send_group_question(bot, session)
        task = asyncio.create_task(quiz_module._advance_group_after_timeout(bot, chat_id, 0))
        session["advance_job"] = task
    else:
        session = quiz_module.start_session(user.id, chat_id, questions, topic, style, timer)
        await update.message.reply_text(f"👤 {label} starting!\nTopic: {topic}\nQuestions: {actual}", parse_mode=ParseMode.MARKDOWN)
        await quiz_module.send_question(bot, session)
        task = asyncio.create_task(quiz_module._advance_after_timeout(bot, user.id, 0))
        session["advance_job"] = task

async def cmd_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _start_quiz(update, context, style="quiz")

async def cmd_pyq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _start_quiz(update, context, style="pyq")

async def cmd_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    chat_id = update.effective_chat.id
    await update.message.reply_text(leaderboard.format_leaderboard(chat_id), parse_mode=ParseMode.MARKDOWN)

async def cmd_myrank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    user = update.effective_user
    chat_id = update.effective_chat.id
    await update.message.reply_text(leaderboard.format_my_rank(user.id, chat_id), parse_mode=ParseMode.MARKDOWN)

async def cmd_toptoday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    chat_id = update.effective_chat.id
    await update.message.reply_text(leaderboard.format_today_top(chat_id), parse_mode=ParseMode.MARKDOWN)

async def cmd_resetscore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    user = update.effective_user
    chat_id = update.effective_chat.id
    db.reset_score(user.id, chat_id)
    await update.message.reply_text(f"🔄 *{user.first_name}*, your score has been reset.", parse_mode=ParseMode.MARKDOWN)

async def cmd_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    chat_id = update.effective_chat.id
    args = context.args or []
    if not args or not args[0].isdigit() or int(args[0]) not in {15, 30, 45, 60}:
        await update.message.reply_text("Usage: `/timer 15|30|45|60`", parse_mode=ParseMode.MARKDOWN)
        return
    db.set_group_timer(chat_id, int(args[0]))
    await update.message.reply_text(f"✅ Timer set to *{args[0]}s", parse_mode=ParseMode.MARKDOWN)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    if not update.message or not update.message.voice:
        return

    wait_msg = await update.message.reply_text("🎙 Voice सुन रहा हूँ…")
    try:
        voice = update.message.voice
        tg_file = await context.bot.get_file(voice.file_id)
        audio_bytes = bytes(await tg_file.download_as_bytearray())
        reply = await generate_voice_response(audio_bytes)
        await wait_msg.edit_text(f"🎙 आपने कहा:\n\n{reply}")
    except Exception as exc:
        logger.error("Voice processing failed: %s", exc)
        await wait_msg.edit_text(
            "❌ Voice process नहीं हो पाई। Gemini API/voice format की समस्या हो सकती है।"
        )

async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    chat_id = update.effective_chat.id
    args = context.args or []
    if len(args) < 2:
        await update.message.reply_text("इस्तेमाल: `/schedule <topic> <number>`", parse_mode=ParseMode.MARKDOWN)
        return
    try:
        count = int(args[-1])
    except ValueError:
        await update.message.reply_text("❌ आखिरी argument questions की संख्या होनी चाहिए।")
        return
    if not 1 <= count <= 50:
        await update.message.reply_text("❌ Questions 1 से 50 के बीच रखें।")
        return
    topic = " ".join(args[:-1]).strip()
    if not topic:
        await update.message.reply_text("❌ Topic भी देना जरूरी है।")
        return
    sched_module.add_schedule(chat_id, topic, count)
    await update.message.reply_text(
        f"✅ Daily Quiz scheduled!\n📖 Topic: {topic}\n❓ Questions: {count}\n🕘 Time: 9:00 PM IST"
    )

async def cmd_scheduleoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    sched_module.remove_schedule(update.effective_chat.id)
    await update.message.reply_text("✅ Daily schedule बंद कर दिया गया है।")

async def cmd_schedulelist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    rows = db.get_all_schedules()
    chat_id = update.effective_chat.id
    row = next((r for r in rows if int(r["chat_id"]) == int(chat_id)), None)
    if not row:
        await update.message.reply_text("📋 इस chat में कोई daily quiz scheduled नहीं है।")
        return
    await update.message.reply_text(
        f"📋 Daily Quiz\n📖 Topic: {row['topic']}\n❓ Questions: {row['count']}\n🕘 9:00 PM IST"
    )

async def on_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    if not answer.option_ids: return
    # option_ids is a list; pick first
    selected = answer.option_ids[0]
    if answer.poll_id in quiz_module.poll_to_user:
        await quiz_module.handle_poll_answer(context.bot, answer.user.id, answer.poll_id, selected)
    elif answer.poll_id in quiz_module.poll_to_chat:
        chat_id = quiz_module.poll_to_chat[answer.poll_id]
        name = answer.user.full_name or "User"
        username = answer.user.username or ""
        await quiz_module.handle_group_poll_answer(context.bot, chat_id, answer.user.id, name, username, answer.poll_id, selected)

async def cmd_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search YouTube and send a small audio file in private chats or groups."""
    if not await check_bot_active(update, context):
        return

    if not update.message:
        return

    song_name = " ".join(context.args or []).strip()
    if not song_name:
        await update.message.reply_text("❌ इस्तेमाल: /song <गाने का नाम>")
        return

    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("🎵 गाना ढूँढा जा रहा है…")
    temp_dir = tempfile.mkdtemp(prefix="telegram_song_")

    # Railway must provide ffmpeg/ffprobe because yt-dlp uses them for MP3 conversion.
    # nixpacks.toml installs ffmpeg during Railway build.
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if not ffmpeg_path or not ffprobe_path:
        await msg.edit_text(
            "❌ Song system setup error: Railway में ffmpeg/ffprobe नहीं मिला।\n\n"
            "Deploy को नया build देकर फिर कोशिश करें।"
        )
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    # Convert to MP3 with ffmpeg so Telegram receives a predictable file.
    # 96 kbps keeps most normal songs comfortably below the Bot API upload limit.
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(temp_dir, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 30,
        "retries": 3,
        "fragment_retries": 3,
        "concurrent_fragment_downloads": 1,
        "restrictfilenames": True,
        "default_search": "ytsearch1",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "96",
        }],
        "postprocessor_args": ["-vn"],
        "ffmpeg_location": ffmpeg_path,
    }

    try:
        def download_audio():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch1:{song_name}", download=True)
                entries = info.get("entries") or []
                if not entries:
                    raise RuntimeError("गाना नहीं मिला।")
                item = entries[0]
                video_id = item.get("id")
                if not video_id:
                    raise RuntimeError("YouTube result का ID नहीं मिला।")
                # FFmpegExtractAudio changes the extension to .mp3.
                audio_path = os.path.join(temp_dir, f"{video_id}.mp3")
                if not os.path.exists(audio_path):
                    # Some extractors return a different filename; find the converted MP3.
                    mp3s = [
                        os.path.join(temp_dir, name)
                        for name in os.listdir(temp_dir)
                        if name.lower().endswith(".mp3")
                    ]
                    if not mp3s:
                        raise RuntimeError("ऑडियो कन्वर्ट नहीं हो पाया। Railway में ffmpeg उपलब्ध नहीं है।")
                    audio_path = mp3s[0]
                return audio_path, item

        loop = asyncio.get_running_loop()
        audio_file, info = await loop.run_in_executor(None, download_audio)

        if not audio_file or not os.path.exists(audio_file):
            raise RuntimeError("ऑडियो फ़ाइल डाउनलोड नहीं हुई।")

        size_mb = os.path.getsize(audio_file) / (1024 * 1024)
        if size_mb > 49:
            raise RuntimeError("ऑडियो 49 MB से बड़ा है; छोटा/दूसरा version आज़माएँ।")

        title = (info.get("title") or song_name).strip()[:64]
        artist = (info.get("artist") or info.get("uploader") or "").strip()[:64]

        with open(audio_file, "rb") as audio:
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=audio,
                caption=f"🎧 {title}",
                title=title,
                performer=artist or None,
            )
        await msg.delete()

    except Exception as exc:
        logger.exception("Song error")
        await msg.edit_text(
            "❌ गाना भेजा नहीं जा सका।\n"
            f"कारण: {str(exc)[:220]}"
        )
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)



async def handle_normal_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    if update.effective_chat.type in ['group', 'supergroup'] and update.message and update.message.text:
        user = update.effective_user
        db.ensure_user(user.id, update.effective_chat.id, user.username, user.first_name)
        db.add_xp(user.id, update.effective_chat.id, 1)

async def cmd_mystats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    if update.effective_chat.type == 'private':
        await update.message.reply_text("❌ कृपया इसे ग्रुप में यूज़ करें!")
        return
    user = db.get_user(update.effective_user.id, update.effective_chat.id)
    if not user:
        await update.message.reply_text("❌ कोई रिकॉर्ड नहीं मिला!")
        return
    xp = user.get('xp', 0)
    level = xp // 100
    stats_text = f"📊 *GAMING STATS*\n\n🔹 *Level:* {level}\n✨ *Total XP:* {xp} XP\n🏆 *Total Quiz Score:* {user.get('total_score', 0)}\n"
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def _post_init(application: Application):
    sched_module.init_scheduler(application)



async def cmd_confess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    if update.effective_chat.type != 'private':
        await update.message.reply_text("🤫 यह कमांड सिर्फ मेरे DM में काम करता है!")
        return
    confession_text = " ".join(context.args)
    if not confession_text:
        await update.message.reply_text("❌ इस्तेमाल का तरीका: /confess <मैसेज>")
        return
    group_id = db.get_latest_group_for_user(update.effective_user.id)
    if not group_id:
        await update.message.reply_text("❌ पहले मेन ग्रुप में एक मैसेज भेजें!")
        return
    try:
        await context.bot.send_message(chat_id=group_id, text=f"🤫 *New Confession:*\n\n{confession_text}", parse_mode=ParseMode.MARKDOWN)
        await update.message.reply_text("✅ मैसेज भेज दिया गया है!")
    except Exception:
        await update.message.reply_text("❌ मैसेज भेजने में दिक्कत आई।")

async def cmd_gm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    await update.message.reply_text("Good Morning! ☀️ उठो और आज के दिन को शानदार बनाओ!")

async def cmd_lovememe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    await update.message.reply_photo(photo="https://i.pinimg.com/736x/2b/9a/99/2b9a99ea7035ce4a25501314ecf1489e.jpg", caption="For you! ❤️")

async def cmd_shayari(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_bot_active(update, context): return
    await update.message.reply_text("चाँदनी चाँद से होती है, सितारों से नहीं... ❤️")

def main():
    if not config.TELEGRAM_BOT_TOKEN:
        sys.exit(1)

    db.init_db()
    db.init_pdf_db()

    # Verify Gemini key but don't crash if it's missing or invalid
    try:
        verify_gemini_key()
    except Exception as e:
        logger.warning("Gemini key verification failed at startup: %s", e)

    try:
        verify_groq_keys()
    except Exception as e:
        logger.warning("Groq key verification failed at startup: %s", e)

    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(_post_init).build()

    # Admin Control Handlers
    app.add_handler(CommandHandler("on", cmd_bot_on))
    app.add_handler(CommandHandler("off", cmd_bot_off))

    # Core & Quiz Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("quiz", cmd_quiz))
    app.add_handler(CommandHandler("pyq", cmd_pyq))
    app.add_handler(CommandHandler("pdfquiz", cmd_pdfquiz))
    app.add_handler(CommandHandler("leaderboard", cmd_leaderboard))
    app.add_handler(CommandHandler("myrank", cmd_myrank))
    app.add_handler(CommandHandler("toptoday", cmd_toptoday))
    app.add_handler(CommandHandler("resetscore", cmd_resetscore))
    app.add_handler(CommandHandler("timer", cmd_timer))
    app.add_handler(CommandHandler("schedule", cmd_schedule))
    app.add_handler(CommandHandler("scheduleoff", cmd_scheduleoff))
    app.add_handler(CommandHandler("schedulelist", cmd_schedulelist))


    # Fun handlers
    app.add_handler(CommandHandler("shayari", cmd_shayari))
    app.add_handler(CommandHandler("gm", cmd_gm))
    app.add_handler(CommandHandler("lovememe", cmd_lovememe))
    app.add_handler(CommandHandler("confess", cmd_confess))
    app.add_handler(CommandHandler("song", cmd_song))
    app.add_handler(CommandHandler("mystats", cmd_mystats))

    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    # PDF File Manager Handlers (Placed before normal message handler)
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

    # General Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_normal_message))
    app.add_handler(PollAnswerHandler(on_poll_answer))
    app.add_error_handler(error_handler)

    logger.info("Bot polling with Gemini + Groq failover + voice processing active …")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
