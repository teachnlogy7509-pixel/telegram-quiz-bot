import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from quiz import generate_and_send_quiz

# Logging setup
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 नमस्ते! आपका NEET स्टडी बोट तैयार है।\n"
        "क्विज़ शुरू करने के लिए `/quiz` कमांड भेजें।"
    )

# Quiz Command Trigger
async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ क्विज़ तैयार हो रहा है, कृपया प्रतीक्षा करें...")
    await generate_and_send_quiz(update, context, topic="Biology", count=5)

def main():
    # Telegram Bot Token चेक करें
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    if not TOKEN:
        logger.error("❌ TELEGRAM_BOT_TOKEN is not set in environment variables.")
        return

    # Telegram Application बनाएं
    application = Application.builder().token(TOKEN).build()

    # Handlers जोड़ें
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("quiz", quiz_command))

    # बोट को शुरू करें (Polling)
    logger.info("🚀 Starting Telegram Bot...")
    application.run_polling()

if __name__ == "__main__":
    main()
