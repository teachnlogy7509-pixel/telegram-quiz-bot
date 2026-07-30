from database import get_leaderboard, get_user, get_rank, get_today_stats


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
        name = row['name'] or row['username'] or "Anonymous"
        answered = (row['correct'] or 0) + (row['wrong'] or 0)
        acc = _accuracy(row['correct'] or 0, answered)
        quizzes = row['total_quizzes'] or 0
        score = row['total_score'] or 0
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
    name = user['name'] or user['username'] or "You"
    answered = (user['correct'] or 0) + (user['wrong'] or 0)
    acc = _accuracy(user['correct'] or 0, answered)

    lines = [
        f"📋 *YOUR STATS — {name}*\n",
        f"🏅 Rank: `#{rank}`",
        f"⭐ Total Score: `{user['total_score']:+}`",
        f"✅ Correct: `{user['correct']}`",
        f"❌ Wrong: `{user['wrong']}`",
        f"⏭ Unanswered: `{user['unanswered']}`",
        f"🎯 Accuracy: `{acc}`",
        f"📚 Total Quizzes: `{user['total_quizzes']}`",
        f"🏆 Best Score: `{user['best_score']:+}`",
        f"📝 Last Quiz Score: `{user['last_quiz_score']:+}`",
    ]
    return "\n".join(lines)


def format_today_top(chat_id: int) -> str:
    rows = get_today_stats(chat_id, 10)
    if not rows:
        return "📅 No quizzes played today yet. Be the first!"

    lines = ["📅 *TODAY'S TOP SCORES*\n"]
    for i, row in enumerate(rows, start=1):
        medal = MEDALS.get(i, f"{i}.")
        name = row['name'] or row['username'] or "Anonymous"
        correct   = row['correct'] or 0
        wrong     = row['wrong'] or 0
        answered  = correct + wrong
        acc       = _accuracy(correct, answered)
        score     = row['today_score'] or 0
        lines.append(
            f"{medal} *{name}*\n"
            f"   Score: `{score:+}` | ✅ {correct} ❌ {wrong} | Acc: {acc}"
        )

    return "\n".join(lines)
