import os

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_API_KEY_2 = os.environ.get("GEMINI_API_KEY_2", "")

# Optional Groq failover: add one or both keys in Railway Variables.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_KEY_2 = os.environ.get("GROQ_API_KEY_2", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

DB_PATH = "scores.db"

CORRECT_SCORE = 4
WRONG_SCORE = -1
UNANSWERED_SCORE = 0
POLL_OPEN_PERIOD = 30  # seconds
