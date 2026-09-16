from pathlib import Path
p=Path('question_archive_worker.py');s=p.read_text()
def r(old,new):
 global s
 if new in s:return
 if old not in s:raise SystemExit('PDF shaping patch anchor missing')
 s=s.replace(old,new,1)
r('TTFont(FONT_NAME,FONT_PATH)','TTFont(FONT_NAME,FONT_PATH,shapable=True)')
r('fontName=font));styles.add(ParagraphStyle(name="RA",parent=styles["BodyText"],fontName=font,fontSize=8.5,leading=12));styles.add(ParagraphStyle(name="RQ",parent=styles["Heading3"],fontName=font,fontSize=10.5,leading=14,spaceBefore=8,spaceAfter=4))','fontName=font,shaping=1));styles.add(ParagraphStyle(name="RA",parent=styles["BodyText"],fontName=font,fontSize=8.5,leading=12,shaping=1));styles.add(ParagraphStyle(name="RQ",parent=styles["Heading3"],fontName=font,fontSize=10.5,leading=14,spaceBefore=8,spaceAfter=4,shaping=1))')
r('escape(f"Questions: {len(rows)} | RATHOD HUB archive")','escape(f"कुल प्रश्न: {len(rows)} | RATHOD HUB संग्रह")')
r('escape(f"{chr(65+i)}. {o}")','escape(f"{(\'क\',\'ख\',\'ग\',\'घ\')[i]}. {o}")')
r('answer="Not available" if q["correct_index"] is None else chr(65+q["correct_index"]);story.append(Paragraph(escape("Answer: "+answer),styles["RA"]))','answer="उपलब्ध नहीं" if q["correct_index"] is None else ("क","ख","ग","घ")[q["correct_index"]];story.append(Paragraph(escape("सही उत्तर: "+answer),styles["RA"]))')
r('make_pdf("RATHOD HUB Notes - "+label,rows,True)','make_pdf("RATHOD HUB नोट्स - "+label,rows,True)')
r('make_pdf("RATHOD HUB Test Bank - "+label,rows,False)','make_pdf("RATHOD HUB टेस्ट प्रश्नपत्र - "+label,rows,False)')
# rh_bridge_events permits only immediate/digest. Keep archive links command-only by using digest.
s=s.replace('"delivery_mode":"archive"','"delivery_mode":"digest"')
# Correct malformed Drive permission endpoints.
s=s.replace('f"{{https://www.googleapis.com/drive/v3/files/{file_id}}}/permissions?fields=permissions(id,type,role)"','f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?fields=permissions(id,type,role)"')
s=s.replace('f"{{https://www.googleapis.com/drive/v3/files/{file_id}}}/permissions?fields=id"','f"https://www.googleapis.com/drive/v3/files/{file_id}/permissions?fields=id"')
p.write_text(s)
print('Devanagari shaping, valid archive mode and Drive links enabled')
