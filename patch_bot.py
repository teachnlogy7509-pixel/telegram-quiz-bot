from pathlib import Path

def rep(path,old,new):
 p=Path(path);s=p.read_text()
 if new in s:return
 if old not in s:raise SystemExit(f'Patch anchor missing in {path}')
 p.write_text(s.replace(old,new,1))

rep('config.py','GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")\n\nDB_PATH = "scores.db"\n\nCORRECT_SCORE = 4\nWRONG_SCORE = -1','GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")\n\n# Secure score sync: set only in Railway Variables.\nSUPABASE_URL = os.environ.get("SUPABASE_URL", "")\nSUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")\n\nDB_PATH = "scores.db"\n\nCORRECT_SCORE = 20\nWRONG_SCORE = -10')
rep('main.py','import vip_scheduler\nimport multi_provider','import vip_scheduler\nimport rathod_ai\nimport multi_provider')
rep('main.py','    await premium_hub.init_commands(application)','    await premium_hub.init_commands(application)\n    await rathod_ai.install(application, db, quiz_module, vip_commands, ADMIN_IDS)')
print('RATHOD AI commands patch applied.')
