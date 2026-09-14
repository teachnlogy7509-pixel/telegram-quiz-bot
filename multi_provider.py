"""Multi-provider AI fallback: Gemini -> Groq -> OpenRouter, with key/model rotation."""
from __future__ import annotations
import asyncio,json,logging,os
from urllib import error,request
logger=logging.getLogger(__name__);_INSTALLED=False

def _values(prefix,count):
 names=[prefix]+[f"{prefix}_{i}" for i in range(2,count+1)]
 return [os.environ.get(n,"").strip() for n in names if os.environ.get(n,"").strip()]
def gemini_keys():return _values("GEMINI_API_KEY",5)
def groq_keys():return _values("GROQ_API_KEY",3)
def openrouter_keys():return _values("OPENROUTER_API_KEY",3)
def gemini_models():return _values("GEMINI_MODEL",5)
def groq_models():return _values("GROQ_MODEL",5) or ["llama-3.3-70b-versatile"]
def openrouter_models():return _values("OPENROUTER_MODEL",5) or ["openrouter/auto"]

def _openrouter_generate(prompt,key,model):
 body=json.dumps({"model":model,"messages":[{"role":"system","content":"You are the RATHOD VIP quiz engine. Return only the exact requested valid JSON array."},{"role":"user","content":prompt}],"temperature":0.25,"max_tokens":8192}).encode()
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
 # Put every configured Gemini model first, then retain built-in fallback models.
 configured=[]
 for model in gemini_models():
  slot=q.ModelSlot(model,"v1beta")
  if slot not in configured:configured.append(slot)
 for slot in q.CANDIDATE_SLOTS:
  if slot not in configured:configured.append(slot)
 q.CANDIDATE_SLOTS=configured
 if configured:q._working_slot=configured[0]
 # Existing Groq stage calls this once per key; this replacement rotates all configured models for that key.
 def groq_generate(prompt,key_index=0):
  client=q._get_groq_client(key_index);last=None
  for model in groq_models():
   try:
    response=client.chat.completions.create(model=model,messages=[{"role":"system","content":"You are a reliable RATHOD VIP quiz generator. Return only requested JSON."},{"role":"user","content":prompt}],temperature=0.2,max_completion_tokens=8192)
    text=response.choices[0].message.content or ""
    if text:return text
   except Exception as exc:last=exc;logger.warning("Groq model fallback failed model=%s: %s",model,exc)
  raise RuntimeError(f"All Groq models failed: {last}")
 q._groq_generate=groq_generate
 original=q.generate_questions
 async def generate_questions(topic,count,style="quiz"):
  errors=[]
  try:return await original(topic,count,style)
  except Exception as exc:errors.append("Gemini/Groq: "+str(exc)[:180]);logger.warning("Gemini/Groq exhausted; switching OpenRouter: %s",exc)
  keys=openrouter_keys()
  if not keys:raise RuntimeError("All Gemini/Groq attempts failed and no OpenRouter key is configured. "+errors[-1])
  prompt=q._build_prompt(topic,count,style)
  for ki,key in enumerate(keys):
   for model in openrouter_models():
    for retry in range(2):
     try:
      raw_text=await asyncio.to_thread(_openrouter_generate,prompt,key,model);raw=q._safe_parse_json(raw_text);valid=q._validate(raw,count)
      if len(valid)<count:raise ValueError(f"OpenRouter returned {len(valid)}/{count} valid questions")
      logger.info("OpenRouter succeeded key=%s model=%s",ki+1,model);return valid[:count]
     except Exception as exc:errors.append(f"OpenRouter key {ki+1}/{model}: {str(exc)[:180]}");logger.warning(errors[-1]);await asyncio.sleep(1+retry)
  raise RuntimeError("All AI providers failed. Last: "+errors[-1])
 q.generate_questions=generate_questions
 logger.info("Multi-AI ready: Gemini keys=%s models=%s; Groq keys=%s models=%s; OpenRouter keys=%s models=%s",len(gemini_keys()),len(q.CANDIDATE_SLOTS),len(groq_keys()),len(groq_models()),len(openrouter_keys()),len(openrouter_models()))

async def cmd_aistatus(update,context):
 await update.message.reply_text("🤖 RATHOD Multi-AI Status\n\n"+f"Gemini: {len(gemini_keys())} keys • {len(gemini_models()) or 'built-in'} configured models\n"+f"Groq: {len(groq_keys())} keys • {len(groq_models())} models\n"+f"OpenRouter: {len(openrouter_keys())} keys • {len(openrouter_models())} models\n\n"+"Fallback flow:\nGemini keys/models → Groq keys/models → OpenRouter keys/models")
