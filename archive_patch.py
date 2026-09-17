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

    # Keep generated question language readable: natural Hindi in Devanagari
    # for ordinary words, standard English only for scientific terminology.
    language_marker = "        4. The response MUST start with '[' and end with ']'.\n"
    language_rules = """        5. Write ordinary instructions, question wording and generic answer text in natural, correct Hindi Devanagari when the topic is Hindi/Hinglish. Do not use broken Roman-Hindi, half-translated spellings or mixed fragments.
        6. Keep scientific and technical terms, abbreviations, units, chemical names, Latin species names and proper nouns in standard English exactly (for example: DNA, RNA, ATP, NAD+, pH, gene, enzyme). Never output the Unicode replacement character, mojibake, or corrupted words.
"""
    if "Unicode replacement character" not in text:
        if language_marker not in text:
            raise SystemExit("quiz.py language prompt anchor missing")
        text = text.replace(language_marker, language_marker + language_rules, 1)

    path.write_text(text)
    print("Telegram question archive hooks and clean Hindi/English prompt applied")


if __name__ == "__main__":
    apply_patch()
