from pathlib import Path

# This build-time patch is intentionally idempotent. It keeps the worker's
# direct source compatible with cached Railway builds while applying the final
# five-day, immutable, uniquely named PDF behavior.
path = Path("question_archive_worker.py")
if path.exists():
    source = path.read_text()

    source = source.replace('"delivery_mode":"archive"', '"delivery_mode":"digest"')
    source = source.replace('"delivery_mode": "archive"', '"delivery_mode": "digest"')
    source = source.replace('f"{{https://www.googleapis.com/drive/v3/files/', 'f"https://www.googleapis.com/drive/v3/files/')
    source = source.replace("{file_id}}}/permissions", "{file_id}/permissions")
    source = source.replace("{file_id}}/permissions", "{file_id}/permissions")

    # Keep an existing file untouched for the whole five-day window. A new
    # deterministic filename is created only when the next window starts.
    reuse_anchor = '    old = find_file(access, folder, name)\n    if old:\n'
    reuse_block = '''    old = find_file(access, folder, name)\n    if old:\n        file_id = str(old["id"])\n        ensure_group_access(access, file_id)\n        return "https://drive.google.com/file/d/" + file_id + "/view?usp=sharing"\n    if old:\n'''
    if reuse_anchor in source and 'Keep an existing file untouched' not in source:
        source = source.replace(reuse_anchor, reuse_block, 1)

    # Five-day windows anchored at 2026-01-01. The current 13–16 window
    # therefore becomes 13–17 and remains unchanged until the next window.
    old_window = '''def window(now: datetime):\n    start = now.replace(day=((now.day - 1) // 4) * 4 + 1, hour=0, minute=0, second=0, microsecond=0)\n    return start, start + timedelta(days=4)\n'''
    new_window = '''def window(now: datetime):\n    anchor = datetime(2026, 1, 1, tzinfo=timezone.utc)\n    elapsed_days = max(0, (now - anchor).days)\n    start = anchor + timedelta(days=(elapsed_days // 5) * 5)\n    return start, start + timedelta(days=5)\n'''
    if old_window in source:
        source = source.replace(old_window, new_window, 1)

    # Give every Notes/Test PDF a stable RATHOD HUB identity. The stable name
    # prevents accidental duplicates on polling retries; the reuse block above
    # prevents content changes before the five-day window expires.
    old_label = '    label = start.strftime("%d-%b") + "_to_" + (end - timedelta(days=1)).strftime("%d-%b-%Y")\n'
    new_label = '''    window_key = start.strftime("%Y%m%d") + "_" + (end - timedelta(days=1)).strftime("%Y%m%d")\n    label = "RATHOD HUB | " + start.strftime("%d-%b") + "_to_" + (end - timedelta(days=1)).strftime("%d-%b-%Y")\n    notes_name = "RATHOD_HUB_NOTES_" + window_key + ".pdf"\n    test_name = "RATHOD_HUB_TEST_" + window_key + ".pdf"\n'''
    if old_label in source and 'notes_name = "RATHOD_HUB_NOTES_"' not in source:
        source = source.replace(old_label, new_label, 1)
    source = source.replace('"Notes_" + label + ".pdf"', 'notes_name')
    source = source.replace('"Test_" + label + ".pdf"', 'test_name')

    # Biology/technical names remain in English, but generic mode labels are
    # Hindi. The body and options continue to use the real Devanagari font.
    if "def pdf_mode_label(" not in source:
        anchor = "def make_pdf(title: str, rows: list[dict], answers: bool) -> bytes:\n"
        helper = '''def pdf_mode_label(mode: object) -> str:\n    value = str(mode or "Quiz").strip()\n    low = value.casefold()\n    if low in {"daily 9 pm", "daily 9pm"}:\n        return "दैनिक 9 PM"\n    if low in {"live quiz", "live_quiz"}:\n        return "लाइव क्विज़"\n    if low in {"quiz", "practice", "study practice"}:\n        return {"quiz": "क्विज़", "practice": "अभ्यास", "study practice": "अध्ययन अभ्यास"}[low]\n    if low == "pdf" or low.startswith("pdf:"):\n        return "पीडीएफ"\n    return value\n\n\n'''
        if anchor in source:
            source = source.replace(anchor, helper + anchor, 1)
    source = source.replace(
        'f"{number}. [{question[\'mode\']}] {question[\'question\']}"',
        'f"{number}. [{pdf_mode_label(question[\'mode\'])}] {question[\'question\']}"',
    )

    # Register the Hindi font as a family as well, so ReportLab never falls
    # back to Helvetica when a Paragraph contains mixed Hindi/Latin text.
    family_anchor = '        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH, shapable=True))\n'
    family_replacement = family_anchor + '        pdfmetrics.registerFontFamily(FONT_NAME, normal=FONT_NAME, bold=FONT_NAME, italic=FONT_NAME, boldItalic=FONT_NAME)\n'
    if family_anchor in source and 'registerFontFamily(FONT_NAME' not in source:
        source = source.replace(family_anchor, family_replacement, 1)

    path.write_text(source)
    print("RATHOD HUB PDFs: Hindi shaping, unique names, immutable five-day windows ready")
