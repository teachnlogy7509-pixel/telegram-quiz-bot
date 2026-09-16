from pathlib import Path

# Keep the worker source safe for both fresh and cached Railway builds.
path = Path("question_archive_worker.py")
if path.exists():
    source = path.read_text()
    source = source.replace('"delivery_mode":"archive"', '"delivery_mode":"digest"')
    source = source.replace('"delivery_mode": "archive"', '"delivery_mode": "digest"')
    source = source.replace('f"{{https://www.googleapis.com/drive/v3/files/', 'f"https://www.googleapis.com/drive/v3/files/')
    source = source.replace("{file_id}}}/permissions", "{file_id}/permissions")
    source = source.replace("{file_id}}/permissions", "{file_id}/permissions")

    # Biology names and official program names stay unchanged, while generic
    # mode labels are rendered in Hindi in the PDF.
    if "def pdf_mode_label(" not in source:
        anchor = "def make_pdf(title: str, rows: list[dict], answers: bool) -> bytes:\n"
        helper = '''def pdf_mode_label(mode: object) -> str:\n    value = str(mode or "Quiz").strip()\n    low = value.casefold()\n    if low in {"daily 9 pm", "daily 9pm"}:\n        return "दैनिक 9 PM"\n    if low in {"live quiz", "live_quiz"}:\n        return "लाइव क्विज़"\n    if low in {"quiz", "practice", "study practice"}:\n        return {"quiz": "क्विज़", "practice": "अभ्यास", "study practice": "अध्ययन अभ्यास"}[low]\n    if low == "pdf" or low.startswith("pdf:"):\n        return "पीडीएफ"\n    return value\n\n\n'''
        if anchor in source:
            source = source.replace(anchor, helper + anchor, 1)
    source = source.replace(
        'f"{number}. [{question[\'mode\']}] {question[\'question\']}"',
        'f"{number}. [{pdf_mode_label(question[\'mode\'])}] {question[\'question\']}"',
    )
    path.write_text(source)
    print("PDF worker keeps archive generation only; PDF list/topic search removed")
