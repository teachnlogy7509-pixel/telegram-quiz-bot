"""Create readable Hindi/English study cards from a short topic name."""
from __future__ import annotations
import asyncio, io, json, re
import fitz
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from question_archive_worker import ensure_hindi_font, ensure_latin_font, pdf_text

PAGE=1080

def _prompt(topic):
    return f'''Create concise, factually accurate NEET/NCERT study notes for: {topic}.
Write natural Hindi in Devanagari and retain English scientific names in parentheses.
Return ONLY valid JSON with this exact structure:
{{"title":"short title","subtitle":"one-line definition","sections":[
{{"heading":"heading","bullets":["fact 1","fact 2","fact 3"]}},
{{"heading":"heading","bullets":["fact 1","fact 2","fact 3"]}},
{{"heading":"heading","bullets":["fact 1","fact 2","fact 3"]}},
{{"heading":"heading","bullets":["fact 1","fact 2","fact 3"]}}],
"mnemonic":"one short memory trick","exam_tip":"one important NCERT caution"}}
Every bullet must be under 105 characters. Do not invent facts.'''

def _parse(raw, topic):
    text=re.sub(r'^```(?:json)?\s*|\s*```$','',(raw or '').strip(),flags=re.I|re.S)
    try: data=json.loads(text)
    except json.JSONDecodeError:
        a,b=text.find('{'),text.rfind('}')
        if a<0 or b<=a: raise ValueError('AI did not return JSON')
        data=json.loads(text[a:b+1])
    sections=[]
    for item in data.get('sections') or []:
        if not isinstance(item,dict): continue
        bullets=[str(x).strip()[:150] for x in item.get('bullets') or [] if str(x).strip()]
        if bullets: sections.append({'heading':str(item.get('heading') or 'मुख्य बिंदु')[:70],'bullets':bullets[:3]})
    if len(sections)<4: raise ValueError('AI returned incomplete sections')
    return {'title':str(data.get('title') or topic)[:90],
            'subtitle':str(data.get('subtitle') or 'त्वरित अध्ययन नोट्स')[:180],
            'sections':sections[:4],
            'mnemonic':str(data.get('mnemonic') or 'मुख्य शब्द क्रम में दोहराएँ।')[:220],
            'exam_tip':str(data.get('exam_tip') or 'NCERT से सत्यापित करें।')[:220]}

def _gemini(prompt,q):
    errors=[]; keys=q._api_keys(); slots=[q._working_slot]+[x for x in q.CANDIDATE_SLOTS if x!=q._working_slot]
    for ki in range(len(keys)):
        for slot in slots:
            try:
                client=q._get_client(slot.api_version,ki)
                result=client.models.generate_content(model=slot.model,contents=prompt,
                    config=q.genai_types.GenerateContentConfig(max_output_tokens=3000,response_mime_type='application/json',temperature=0.15))
                if result.text:return result.text
            except Exception as exc: errors.append(str(exc)[:150])
    raise RuntimeError(errors[-1] if errors else 'No Gemini key')

async def generate(topic,q):
    prompt=_prompt(topic); errors=[]
    try: count=max(1,len(q._groq_keys()))
    except Exception: count=1
    for ki in range(count):
        try:return _parse(await asyncio.to_thread(q._groq_generate,prompt,ki),topic)
        except Exception as exc: errors.append('Groq: '+str(exc)[:140])
    try:return _parse(await asyncio.to_thread(_gemini,prompt,q),topic)
    except Exception as exc: errors.append('Gemini: '+str(exc)[:140])
    raise RuntimeError(' | '.join(errors[-3:]))

def _para(text,style,w,h):
    p=Paragraph(pdf_text(text),style); _,used=p.wrap(w,h); return p,used

def render(notes):
    hindi=ensure_hindi_font(); ensure_latin_font()
    out=io.BytesIO(); c=canvas.Canvas(out,pagesize=(PAGE,PAGE))
    bg,green,pale,yellow,ink=map(HexColor,['#F7F4E8','#244D32','#E8EEDC','#FFF1B8','#172019'])
    c.setFillColor(bg);c.rect(0,0,PAGE,PAGE,fill=1,stroke=0)
    c.setFillColor(green);c.roundRect(35,915,1010,130,26,fill=1,stroke=0)
    title=ParagraphStyle('t',fontName=hindi,fontSize=34,leading=42,textColor=HexColor('#FFFFFF'),alignment=TA_CENTER)
    sub=ParagraphStyle('s',fontName=hindi,fontSize=16,leading=22,textColor=HexColor('#EAF3E8'),alignment=TA_CENTER)
    head=ParagraphStyle('h',fontName=hindi,fontSize=19,leading=24,textColor=green,alignment=TA_LEFT)
    body=ParagraphStyle('b',fontName=hindi,fontSize=14,leading=19,textColor=ink,alignment=TA_LEFT)
    small=ParagraphStyle('f',fontName=hindi,fontSize=11,leading=14,textColor=HexColor('#526056'),alignment=TA_CENTER)
    p,h=_para(notes['title'],title,940,58);p.drawOn(c,70,985-h)
    p,h=_para(notes['subtitle'],sub,930,46);p.drawOn(c,75,942-h)
    for section,(x,y) in zip(notes['sections'],[(35,605),(550,605),(35,300),(550,300)]):
        c.setFillColor(HexColor('#FFFFFF'));c.setStrokeColor(HexColor('#B8C6AE'));c.roundRect(x,y,495,280,18,fill=1,stroke=1)
        c.setFillColor(pale);c.roundRect(x+12,y+222,471,45,12,fill=1,stroke=0)
        p,h=_para(section['heading'],head,440,38);p.drawOn(c,x+27,y+246-h)
        html='<br/>'.join('• '+pdf_text(v) for v in section['bullets']);p=Paragraph(html,body);_,h=p.wrap(445,185);p.drawOn(c,x+25,y+202-h)
    for x,heading,value in [(35,'याद रखने की ट्रिक',notes['mnemonic']),(550,'NEET/NCERT Focus',notes['exam_tip'])]:
        c.setFillColor(yellow);c.setStrokeColor(HexColor('#D2B85E'));c.roundRect(x,82,495,180,18,fill=1,stroke=1)
        p,h=_para(heading,head,450,35);p.drawOn(c,x+22,225-h)
        p,h=_para(value,body,450,105);p.drawOn(c,x+22,195-h)
    p,h=_para('AI-assisted notes • परीक्षा से पहले NCERT से तथ्य सत्यापित करें',small,900,22);p.drawOn(c,90,28)
    c.showPage();c.save();out.seek(0)
    doc=fitz.open(stream=out.getvalue(),filetype='pdf'); pix=doc[0].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
    image=io.BytesIO(pix.tobytes('png')); image.name='study-note.png';doc.close();image.seek(0);return image

async def create(topic,q):
    notes=await generate(topic,q); return await asyncio.to_thread(render,notes),notes
