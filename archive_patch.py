from pathlib import Path


def apply_patch():
    path = Path("quiz.py")
    text = path.read_text()

    if "import archive_sync" not in text:
        anchor = "import supabase_sync\n"
        if anchor not in text:
            raise SystemExit("quiz.py archive import anchor missing")
        text = text.replace(anchor, anchor + "import archive_sync\n", 1)

    general_marker = "    return accumulated[:count]\n\n\n# (rest of file unchanged from your current quiz logic)"
    general_replacement = """    result = accumulated[:count]
    try:
        await asyncio.to_thread(archive_sync.record_questions, topic, style, result)
    except Exception as exc:
        logger.warning("Question archive enqueue failed: %s", str(exc)[:180])
    return result


# (rest of file unchanged from your current quiz logic)"""
    if "Question archive enqueue failed" not in text:
        if general_marker not in text:
            raise SystemExit("quiz.py question-generation anchor missing")
        text = text.replace(general_marker, general_replacement, 1)

    pdf_marker = "    return accumulated[:count]\n\n\n# =====================\n# Voice (used by main.py)"
    pdf_replacement = """    result = accumulated[:count]
    try:
        await asyncio.to_thread(
            archive_sync.record_questions, f"PDF:{pdf_name}", "pdf", result
        )
    except Exception as exc:
        logger.warning("PDF question archive enqueue failed: %s", str(exc)[:180])
    return result


# =====================
# Voice (used by main.py)"""
    if "PDF question archive enqueue failed" not in text and pdf_marker in text:
        text = text.replace(pdf_marker, pdf_replacement, 1)

    path.write_text(text)
    print("Telegram question archive hooks applied")


if __name__ == "__main__":
    apply_patch()
