from pathlib import Path

# Build-time patch for the Railway archive worker. It is deliberately
# idempotent because Railway may reuse a cached build layer.
path = Path("question_archive_worker.py")
if not path.exists():
    raise SystemExit("question_archive_worker.py not found")

source = path.read_text()

# Keep the existing archive and Drive fixes safe across old cached builds.
source = source.replace('"delivery_mode":"archive"', '"delivery_mode":"digest"')
source = source.replace('"delivery_mode": "archive"', '"delivery_mode": "digest"')
source = source.replace('f"{{https://www.googleapis.com/drive/v3/files/', 'f"https://www.googleapis.com/drive/v3/files/')
source = source.replace("{file_id}}}/permissions", "{file_id}/permissions")
source = source.replace("{file_id}}/permissions", "{file_id}/permissions")

# The five-day window is fixed and immutable. These replacements are kept for
# deployments that still contain the pre-window implementation.
old_window = '''def window(now: datetime):
    start = now.replace(day=((now.day - 1) // 4) * 4 + 1, hour=0, minute=0, second=0, microsecond=0)
    return start, start + timedelta(days=4)
'''
new_window = '''def window(now: datetime):
    elapsed_days = max(0, (now - WINDOW_ANCHOR).days)
    start = WINDOW_ANCHOR + timedelta(days=(elapsed_days // WINDOW_DAYS) * WINDOW_DAYS)
    return start, start + timedelta(days=WINDOW_DAYS)
'''
if old_window in source:
    source = source.replace(old_window, new_window, 1)

# Make the corrected PDF generation create a fresh Drive file once, instead
# of reusing the older broken-font file from the same window.
source = source.replace(
    'unique_tag = hashlib.sha1(("RATHOD-HUB:" + window_key).encode("utf-8")).hexdigest()[:10].upper()',
    'unique_tag = hashlib.sha1(("RATHOD-HUB:FOOTER-V2:" + window_key).encode("utf-8")).hexdigest()[:10].upper()',
)
source = source.replace('RATHOD-HUB:FOOTER-V1:', 'RATHOD-HUB:FOOTER-V2:')

# Unicode normalization is needed before ReportLab sees the text.
if "import unicodedata" not in source:
    source = source.replace("import time\n", "import time\nimport unicodedata\n", 1)

# Replace the old mixed-font HTML segmentation. It was the source of missing
# Devanagari glyphs in labels and Hindi/English runs. One shaping-capable
# Devanagari font is used for the complete line; it contains the Latin glyphs
# needed for scientific terms such as NAD+, ATP, DNA and pH.
pdf_start = source.find("\ndef pdf_text(")
pdf_end = source.find("\n\ndef rest(", pdf_start)
if pdf_start < 0 or pdf_end < 0:
    raise SystemExit("pdf_text patch anchors missing")

pdf_helpers = '''

def normalize_pdf_text(value: object) -> str:
    """Return clean Unicode text without replacement boxes or emoji glyphs."""
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.translate(
        str.maketrans(
            {
                "\\u00a0": " ",
                "\\u2013": "-",
                "\\u2014": "-",
                "\\u2212": "-",
                "\\u2192": "->",
                "\\u2190": "<-",
                "\\u2022": "-",
                "\\u2018": "'",
                "\\u2019": "'",
                "\\u201c": '"',
                "\\u201d": '"',
                "\\ufffd": "",
            }
        )
    )
    text = re.sub(r"[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]", "", text)
    # Emoji and symbol pictographs are not present in the educational text and
    # do not exist in the bundled Devanagari font, so remove them rather than
    # rendering empty squares.
    text = re.sub(r"[\\U0001F000-\\U0001FAFF\\u2600-\\u27BF\\uFE0F]", "", text)
    text = re.sub(r"[ \\t\\r\\n]+", " ", text)
    return text.strip()


def pdf_text(value: object) -> str:
    """Escape normalized text while preserving Devanagari shaping."""
    return escape(normalize_pdf_text(value))
'''
source = source[:pdf_start] + pdf_helpers.rstrip() + source[pdf_end:]

# Replace the complete PDF builder so the footer is attached to every page and
# option markers are unambiguous Hindi letters instead of a slash-like glyph.
make_start = source.find("def make_pdf(")
make_end = source.find("\n\ndef rows_for(", make_start)
if make_start < 0 or make_end < 0:
    raise SystemExit("make_pdf patch anchors missing")

make_pdf = '''def draw_pdf_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setStrokeColorRGB(0.55, 0.55, 0.55)
    canvas.setLineWidth(0.35)
    canvas.line(16 * mm, 11 * mm, A4[0] - 16 * mm, 11 * mm)
    canvas.setFont(FONT_NAME, 7.5)
    canvas.setFillColorRGB(0.25, 0.25, 0.25)
    footer = "RATHOD HUB | Admin: Ashish Rathod | NEET | IMPORTANT"
    canvas.drawString(16 * mm, 6.5 * mm, footer)
    canvas.drawRightString(A4[0] - 16 * mm, 6.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def make_pdf(title: str, rows: list[dict], answers: bool) -> bytes:
    font = ensure_hindi_font()
    output = io.BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="RATitle", parent=styles["Title"], fontName=font, shaping=1))
    styles.add(ParagraphStyle(name="RA", parent=styles["BodyText"], fontName=font, fontSize=8.5, leading=12, shaping=1))
    styles.add(ParagraphStyle(name="RQ", parent=styles["Heading3"], fontName=font, fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=4, shaping=1))
    story = [
        Paragraph(pdf_text(title), styles["RATitle"]),
        Spacer(1, 5 * mm),
        Paragraph(pdf_text(f"कुल प्रश्न: {len(rows)} | RATHOD HUB संग्रह"), styles["RA"]),
    ]
    option_letters = ("क)", "ख)", "ग)", "घ)")
    for number, question in enumerate(rows, 1):
        story.append(
            Paragraph(
                pdf_text(f"{number}. [{pdf_mode_label(question['mode'])}] {question['question']}"),
                styles["RQ"],
            )
        )
        for index, option in enumerate(question["options"]):
            story.append(Paragraph(pdf_text(f"{option_letters[index]} {option}"), styles["RA"]))
        if answers:
            answer = "उपलब्ध नहीं" if question["correct_index"] is None else option_letters[question["correct_index"]]
            story.append(Paragraph(pdf_text("सही उत्तर: " + answer), styles["RA"]))
    document.build(story, onFirstPage=draw_pdf_footer, onLaterPages=draw_pdf_footer)
    return output.getvalue()
'''
source = source[:make_start] + make_pdf.rstrip() + source[make_end:]

path.write_text(source)
print("RATHOD HUB PDFs: clean Hindi/English shaping, no replacement glyphs, stable footer, fresh corrected file")
