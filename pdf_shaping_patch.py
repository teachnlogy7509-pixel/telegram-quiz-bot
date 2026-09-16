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

    # Preserve the originating quiz/topic so Sakhi can search archive PDFs.
    source = source.replace(
        '"mode": str(payload.get("mode") or "Quiz"),',
        '"mode": str(payload.get("mode") or "Quiz"),\n        "topic": str(payload.get("quiz_name") or payload.get("topic") or payload.get("mode") or "Quiz"),',
        1,
    )
    source = source.replace(
        'def publish_archive_links(label: str, notes_url: str, test_url: str) -> None:',
        'def publish_archive_links(label: str, notes_url: str, test_url: str, topics: list[str] | None = None) -> None:',
        1,
    )
    source = source.replace(
        '"updated_at": datetime.now(timezone.utc).isoformat(),\n    }',
        '"updated_at": datetime.now(timezone.utc).isoformat(),\n        "topics": sorted({str(topic).strip() for topic in (topics or []) if str(topic).strip()}),\n        "search_text": " ".join(sorted({str(topic).strip() for topic in (topics or []) if str(topic).strip()})),\n    }',
        1,
    )
    if 'topics = sorted({str(row.get("topic")' not in source:
        source = source.replace(
            '    access = token()\n',
            '    topics = sorted({str(row.get("topic") or "").strip() for row in rows if str(row.get("topic") or "").strip()})\n    access = token()\n',
            1,
        )
    source = source.replace(
        'publish_archive_links(label, notes_url, test_url)',
        'publish_archive_links(label, notes_url, test_url, topics)',
    )
    path.write_text(source)
    print("PDF worker keeps topic metadata for /pdfglist search")
