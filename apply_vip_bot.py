"""Idempotently wire all RATHOD VIP modules into main.py."""
from pathlib import Path
p=Path('main.py');s=p.read_text()
if 'import vip_question_engine' not in s:s=s.replace('import quiz as quiz_module\n','import quiz as quiz_module\nimport vip_question_engine\n')
for module,after in [('persistent_scores','import vip_question_engine\n'),('app_update_notifier','import persistent_scores\n'),('vip_commands','import app_update_notifier\n'),('vip_scheduler','import vip_commands\n'),('multi_provider','import vip_scheduler\n'),('premium_hub','import multi_provider\n')]:
 if f'import {module}' not in s:s=s.replace(after,after+f'import {module}\n')
if 'CallbackQueryHandler' not in s:s=s.replace('filters, ConversationHandler)','filters, ConversationHandler, CallbackQueryHandler)')
anchor='ADMIN_IDS = [8043570403]\n'
if 'vip_question_engine.install(quiz_module)' not in s:s=s.replace(anchor,anchor+'\nvip_question_engine.install(quiz_module)\n')
if 'multi_provider.install(quiz_module)' not in s:s=s.replace('vip_question_engine.install(quiz_module)\n','multi_provider.install(quiz_module)\nvip_question_engine.install(quiz_module)\n')
if 'persistent_scores.install(db, leaderboard, quiz_module)' not in s:s=s.replace('vip_question_engine.install(quiz_module)\n','vip_question_engine.install(quiz_module)\npersistent_scores.install(db, leaderboard, quiz_module)\n')
if 'vip_commands.install(quiz_module)' not in s:s=s.replace('persistent_scores.install(db, leaderboard, quiz_module)\n','persistent_scores.install(db, leaderboard, quiz_module)\nvip_commands.install(quiz_module)\n')
s=s.replace('sched_module.init_scheduler(application)','vip_scheduler.init_scheduler(application)')
if 'premium_hub.init_commands(application)' not in s:s=s.replace('app_update_notifier.init(application)','app_update_notifier.init(application)\n    await premium_hub.init_commands(application)')
s=s.replace('CommandHandler("schedule", cmd_schedule)','CommandHandler("schedule", vip_scheduler.cmd_schedule)').replace('CommandHandler("scheduleoff", cmd_scheduleoff)','CommandHandler("scheduleoff", vip_scheduler.cmd_scheduleoff)').replace('CommandHandler("schedulelist", cmd_schedulelist)','CommandHandler("schedulelist", vip_scheduler.cmd_schedulelist)')
if 'CommandHandler("schedulereset"' not in s:s=s.replace('app.add_handler(CommandHandler("schedulelist", vip_scheduler.cmd_schedulelist))','app.add_handler(CommandHandler("schedulelist", vip_scheduler.cmd_schedulelist))\n    app.add_handler(CommandHandler("schedulereset", vip_scheduler.cmd_schedulereset))')
base='app.add_handler(CommandHandler("pyq", cmd_pyq))'
handlers='''app.add_handler(CommandHandler("proquiz", lambda u,c: vip_commands.cmd_proquiz(u,c,quiz_module,db)))
    app.add_handler(CommandHandler("aistatus", multi_provider.cmd_aistatus))
    app.add_handler(CommandHandler("hub", lambda u,c: premium_hub.cmd_hub(u,c,db,leaderboard)))
    app.add_handler(CommandHandler("premium", lambda u,c: premium_hub.cmd_hub(u,c,db,leaderboard)))
    app.add_handler(CommandHandler("profile", lambda u,c: premium_hub.cmd_profile(u,c,db,leaderboard)))
    app.add_handler(CommandHandler("dailychallenge", lambda u,c: premium_hub.cmd_dailychallenge(u,c,quiz_module,db,vip_commands)))
    app.add_handler(CommandHandler("focuspro", premium_hub.cmd_focuspro))
    app.add_handler(CommandHandler("focusstop", premium_hub.cmd_focusstop))
    app.add_handler(CallbackQueryHandler(lambda u,c: premium_hub.handle_button(u,c,db,leaderboard,quiz_module),pattern="^rh_"))'''
if 'CommandHandler("hub"' not in s:
 existing=[]
 if 'CommandHandler("proquiz"' not in s:existing.append(handlers)
 else:
  existing.append('\n'.join(handlers.splitlines()[2:]))
 s=s.replace(base,base+'\n    '+existing[0])
if '/hub — Premium' not in s:s=s.replace('📚 Quiz & Study:','👑 Premium:\n/hub — Premium command center\n/profile — VIP profile card\n/dailychallenge — Daily 10Q challenge\n/focuspro <minutes> — Focus timer\n/focusstop — Stop focus\n\n📚 Quiz & Study:')
p.write_text(s);print('All VIP bot modules wired')
