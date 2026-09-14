"""Speed-first multi-provider AI: Groq Instant -> Gemini Flash Lite/Flash -> Groq quality -> OpenRouter."""
from __future__ import annotations
import asyncio,json,logging,os
from urllib import error,request
logger=logging.getLogger(__name__);_INSTALLED=False

def _values(prefix,count):
 names=[prefix]+[f"{prefix}_{i}" for i in range(2,count+1)]
 return [os.environ.get(n,"").strip() for n in names if os.environ.get(n,"").strip()]
def _unique(items):return list(dict.fromkeys(x for x in items if x))
def gemini_keys():return _values("GEMINI_API_KEY",5)
def groq_keys():return _values("GROQ_API_KEY",3)
def openrouter_keys():return _values("OPENROUTER_API_KEY",3)
def gemini_models():return _unique(["gemini-2.5-flash-lite","gemini-2.5-flash"]+_values("GEMINI_MODEL",5))
def groq_models():return _unique(["llama-3.1-8b-instant"]+_values("GROQ_MODEL",5)+["llama-3.3-70b-versatile"])
def openrouter_models():return _unique(_values("OPENROUTER_MODEL",5)+["openrouter/auto"])

def _openrouter_generate(prompt,key,model):
 body=json.dumps({"model":model,"messages":[{"role":"system","content":"You are the RATHOD VIP quiz engine. Return only the exact requested valid JSON array."},{"role":"user","content":prompt}],"temperature":0.2,"max_tokens":8192}).encode()
 req=request.Request("https://openrouter.ai/api/v1/chat/completions",data=body,method="POST",headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","HTTP-Referer":"https://teachnlogy7509-pixel.github.io/RATHOD-HUB/","X-Title":"RATHOD HUB Telegram Quiz"})
 try:
  with request.urlopen(req,timeout=90) as r:payload=json.loads(r.read().decode())
  return str(payload.get("choices",[{}])[0].get("message",{}).get("content") or "")
 except error.HTTPError as exc:
  detail=exc.read().decode(errors="replace")[:300];raise RuntimeError(f"OpenRouter HTTP {exc.code}: {detail}") from exc

def install(q):
 global _INSTALLED
 if _INSTALLED:return
 _INSTALLED=True;q._api_keys=gemini_keys;q._groq_keys=groq_keys
 # Fast Gemini models are always attempted before larger/configured quality models.
 slots=[]
 for model in gemini_models():
  slot=q.ModelSlot(model,"v1beta")
  if slot not in slots:slots.append(slot)
 for slot in q.CANDIDATE_SLOTS:
  if slot not in slots:slots.append(slot)
 q.CANDIDATE_SLOTS=slots
 if slots:q._working_slot=slots[0]
 # Rotate fast Groq Instant first, then every configured/quality model for each key.
 def groq_generate(prompt,key_index=0):
  client=q._get_groq_client(key_index);last=None
  for model in groq_models():
   try:
    response=client.chat.completions.create(model=model,messages=[{"role":"system","content":"Return only accurate valid quiz JSON. No markdown."},{"role":"user","content":prompt}],temperature=0.15,max_completion_tokens=8192)
    text=response.choices[0].message.content or ""
    if text:return text
   except Exception as exc:last=exc;logger.warning("Groq model failed model=%s: %s",model,exc)
  raise RuntimeError(f"All Groq models failed: {last}")
 q._groq_generate=groq_generate
 original=q.generate_questions
 async def generate_questions(topic,count,style="quiz"):
  prompt=q._build_prompt(topic,count,style);errors=[]
  # SPEED LANE: Groq Instant normally responds first and fastest.
  for key_index,_ in enumerate(groq_keys()):
   try:
    raw_text=await asyncio.to_thread(q._groq_generate,prompt,key_index);raw=q._safe_parse_json(raw_text);valid=q._validate(raw,count)
    if len(valid)>=count:
     logger.info("Speed lane succeeded: Groq key=%s model priority=%s",key_index+1,groq_models()[0]);return valid[:count]
    raise ValueError(f"Groq speed lane returned {len(valid)}/{count}")
   except Exception as exc:errors.append("Groq speed: "+str(exc)[:180])
  # QUALITY/FALLBACK LANE: Gemini Flash Lite/Flash, remaining Gemini models, then Groq quality models.
  try:return await original(topic,count,style)
  except Exception as exc:errors.append("Gemini/Groq quality: "+str(exc)[:180]);logger.warning("Core providers exhausted; switching OpenRouter: %s",exc)
  keys=openrouter_keys()
  if not keys:raise RuntimeError("All Groq/Gemini attempts failed and no OpenRouter key is configured. "+errors[-1])
  for ki,key in enumerate(keys):
   for model in openrouter_models():
    for retry in range(2):
     try:
      raw_text=await asyncio.to_thread(_openrouter_generate,prompt,key,model);raw=q._safe_parse_json(raw_text);valid=q._validate(raw,count)
      if len(valid)<count:raise ValueError(f"OpenRouter returned {len(valid)}/{count}")
      logger.info("OpenRouter succeeded key=%s model=%s",ki+1,model);return valid[:count]
     except Exception as exc:errors.append(f"OpenRouter {ki+1}/{model}: {str(exc)[:180]}");await asyncio.sleep(1+retry)
  raise RuntimeError("All AI providers failed. Last: "+errors[-1])
 q.generate_questions=generate_questions
 logger.info("Speed-first AI ready: Groq Instant -> Gemini Flash Lite/Flash -> quality models -> OpenRouter")

async def cmd_aistatus(update,context):
 await update.message.reply_text("⚡ RATHOD Speed-First Multi-AI\n\n"+f"Groq: {len(groq_keys())} keys • {len(groq_models())} models\n"+f"Gemini: {len(gemini_keys())} keys • {len(gemini_models())} fast/configured models\n"+f"OpenRouter: {len(openrouter_keys())} keys • {len(openrouter_models())} models\n\n"+"Priority:\n1. Groq Instant (fastest)\n2. Gemini Flash Lite/Flash\n3. Gemini/Groq quality models\n4. OpenRouter models/auto")
