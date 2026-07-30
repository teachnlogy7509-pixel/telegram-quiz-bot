# Telegram Quiz Bot

A Telegram bot that generates AI-powered quiz questions using Google Gemini, tracks scores permanently in SQLite, and shows a leaderboard.

## Run & Operate

- Bot runs automatically via the **"Telegram Quiz Bot"** workflow
- `cd telegram-bot && python main.py` — run manually
- Required secrets: `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`

## Stack

- Python 3.11
- python-telegram-bot v21+ (async polling)
- Google Gemini 1.5 Flash (question generation)
- SQLite (`scores.db`) — persistent score storage

## Where things live

- `telegram-bot/main.py` — entry point, command & poll handlers
- `telegram-bot/quiz.py` — session management, Gemini AI, poll logic
- `telegram-bot/database.py` — SQLite CRUD (users, scores, history)
- `telegram-bot/leaderboard.py` — leaderboard & rank formatting
- `telegram-bot/config.py` — env vars, scoring constants
- `telegram-bot/scores.db` — auto-created on first run

## Bot Commands

| Command | Description |
|---|---|
| `/start` | Welcome message |
| `/quiz <topic> <N>` | Start a quiz on any topic, N questions |
| `/pyq <topic> <N>` | PYQ-pattern quiz (Indian competitive exams) |
| `/leaderboard` | Top 10 players with medals |
| `/myrank` | Your personal stats |
| `/help` | Show all commands |

## Scoring

- ✅ Correct: **+4**
- ❌ Wrong: **-1**
- ⏭ Unanswered: **0**

## Architecture decisions

- Each user gets an isolated `active_sessions[user_id]` dict — no score mixing possible
- Gemini generates questions as a JSON array; validated before use, retried up to 3× if malformed
- Auto-advance uses `asyncio.create_task` — polls move to the next question after 30s regardless of whether answered
- `poll_to_user` dict maps Telegram poll IDs → user IDs for global `PollAnswerHandler` routing
- SQLite `ON CONFLICT DO UPDATE` for safe upserts on user records

## User preferences

_Populate as you build._

## Gotchas

- `scores.db` is created relative to the working directory (`telegram-bot/`). The workflow `cd telegram-bot` ensures correct placement.
- Questions must have exactly 4 options and a valid `correct_index` (0–3); any Gemini response that doesn't meet this is discarded and re-requested.
