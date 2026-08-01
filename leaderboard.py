"""
Leaderboard formatting and retrieval logic.
"""
import logging
from database import get_leaderboard, get_user, get_rank, get_today_top

MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}

def _accuracy(correct: int, total_answered: int) -> str:
    if total_answered == 0:
        return "0.0%"
    return f"{correct / total_answered * 100:.1f}%"

def format_leaderboard(chat_id: int) -> str:
    rows = get_leaderboard(chat_id, 10)
    if not rows:
        return "📊 No scores recorded yet. Be the first to play!"

    lines = ["🏆 *LEADERBOARD — TOP 10*\n"]
    for i, row in enumerate(rows, start=1):
        medal = MEDALS.get(i, f"{i}.")
        name = row.get('name') or row.get('username') or "Anonymous"
        correct = row.get('correct', 0) or 0
        wrong = row.get('wrong', 0) or 0
        answered = correct + wrong
        acc = _accuracy(correct, answered)
        quizzes = row.get('total_quizzes', 0) or 0
        score = row.get('total_score', 0) or 0
        lines.append(
            f"{medal} *{name}*\n"
            f"   Score: `{score:+}` | Acc: {acc} | Quizzes: {quizzes}"
        )

    return "\n".join(lines)

def format_my_rank(user_id: int, chat_id: int) -> str:
    user = get_user(user_id, chat_id)
    if not user:
        return "You haven't played any quiz yet. Use /quiz to start!"

    rank = get_rank(user_id, chat_id)
    name = user.get('name') or user.get('username') or "You"
    correct = user.get('correct', 0) or 0
    wrong = user.get('wrong', 0) or 0
    answered = correct + wrong
    acc = _accuracy(correct, answered)

    lines = [
        f"📋 *YOUR STATS — {name}*\n",
        f"🏅 Rank: `#{rank}`",
        f"⭐ Total Score: `{user.get('total_score', 0):+}`",
        f"✅ Correct: `{correct}`",
        f"❌ Wrong: `{wrong}`",
        f"⏭ Unanswered: `{user.get('unanswered', 0)}`",
        f"🎯 Accuracy: `{acc}`",
        f"📚 Total Quizzes: `{user.get('total_quizzes', 0)}`",
        f"🏆 Best Score: `{user.get('best_score', 0):+}`",
        f"📝 Last Quiz Score: `{user.get('last_quiz_score', 0):+}`",
    ]
    return "\n".join(lines)

def format_today_top(chat_id: int) -> str:
    rows = get_today_top(chat_id, 10)
    if not rows:
        return "📅 No quizzes played today yet. Be the first!"

    lines = ["📅 *TODAY'S TOP SCORES*\n"]
    for i, row in enumerate(rows, start=1):
        medal = MEDALS.get(i, f"{i}.")
        name = row.get('name') or row.get('username') or "Anonymous"
        correct = row.get('correct', 0) or 0
        wrong = row.get('wrong', 0) or 0
        answered = correct + wrong
        acc = _accuracy(correct, answered)
        score = row.get('score', 0) or 0
        lines.append(
            f"{medal} *{name}*\n"
            f"   Score: `{score:+}` | ✅ {correct} ❌ {wrong} | Acc: {acc}"
        )

    return "\n".join(lines)
