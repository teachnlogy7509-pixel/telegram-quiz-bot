import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DB_PATH = "scores.db"

CORRECT_SCORE = 4
WRONG_SCORE = -1
UNANSWERED_SCORE = 0
POLL_OPEN_PERIOD = 30  # seconds
