# Telegram Quiz Bot — Fixed Build

## Features
- `/quiz` and `/pyq` Gemini MCQ quizzes
- PDF upload + `/pdfquiz`
- Group and private quiz sessions with Telegram quiz polls
- Leaderboard, rank, daily scores and XP
- Daily scheduled quiz at 9:00 PM IST
- `/timer` for 15/30/45/60 second polls
- PDF file library
- Voice messages with Gemini
- Fun commands: `/shayari`, `/gm`, `/confess`
- `/song <name>` returns YouTube / YouTube Music search links for a song title
- `/song` re-sends a Telegram audio message when used as a reply

## Railway environment variables
Set:
- `TELEGRAM_BOT_TOKEN`
- `GEMINI_API_KEY`
- `GEMINI_API_KEY_2` (optional)
- `GEMINI_MODEL` (optional, defaults to `gemini-3.7-flash`)
- `GROQ_API_KEY` (optional fallback)
- `GROQ_API_KEY_2` (optional fallback)
- `GROQ_MODEL` (optional)

Start command: `python main.py`
