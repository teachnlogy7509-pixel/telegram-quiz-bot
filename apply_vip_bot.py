"""Idempotently wire all RATHOD VIP modules into main.py."""
from pathlib import Path
p=Path('main.py');s=p.read_text()
if 'import vip_question_engine' not in s:s=s.replace('import quiz as quiz_module\n','import quiz as quiz_module\nimport vip_question_engine\n')
for module,after in [('persistent_scores','import vip_question_engine\n'),('app_update_notifier','import persistent_scores\n'),('vip_commands','import app_update_notifier\n'),('vip_scheduler','import vip_commands\n')]:
 if f'import {module}' not in s:s=s.replace(after,after+f'import {module}\n')
anchor='ADMIN_IDS = [8043570403]\n'
if 'vip_question_engine.install(quiz_module)' not in s:s=s.replace(anchor,anchor+'\nvip_question_engine.install(quiz_module)\n')
if 'persistent_scores.install(db, leaderboard, quiz_module)' not in s:s=s.replace('vip_question_engine.install(quiz_module)\n','vip_question_engine.install(quiz_module)\npersistent_scores.install(db, leaderboard, quiz_module)\n')
if 'vip_commands.install(quiz_module)' not in s:s=s.replace('persistent_scores.install(db, leaderboard, quiz_module)\n','persistent_scores.install(db, leaderboard, quiz_module)\nvip_commands.install(quiz_module)\n')
# Replace the old fixed-9-PM scheduler startup and command handlers.
s=s.replace('sched_module.init_scheduler(application)','vip_scheduler.init_scheduler(application)')
s=s.replace('CommandHandler("schedule", cmd_schedule)','CommandHandler("schedule", vip_scheduler.cmd_schedule)')
s=s.replace('CommandHandler("scheduleoff", cmd_scheduleoff)','CommandHandler("scheduleoff", vip_scheduler.cmd_scheduleoff)')
s=s.replace('CommandHandler("schedulelist", cmd_schedulelist)','CommandHandler("schedulelist", vip_scheduler.cmd_schedulelist)')
if 'CommandHandler("schedulereset"' not in s:s=s.replace('app.add_handler(CommandHandler("schedulelist", vip_scheduler.cmd_schedulelist))','app.add_handler(CommandHandler("schedulelist", vip_scheduler.cmd_schedulelist))\n    app.add_handler(CommandHandler("schedulereset", vip_scheduler.cmd_schedulereset))')
if 'CommandHandler("proquiz"' not in s:s=s.replace('app.add_handler(CommandHandler("pyq", cmd_pyq))','app.add_handler(CommandHandler("pyq", cmd_pyq))\n    app.add_handler(CommandHandler("proquiz", lambda u,c: vip_commands.cmd_proquiz(u,c,quiz_module,db)))')
if '/proquiz <topic>' not in s:s=s.replace('/pyq <topic> <number> — PYQ-style quiz','/pyq <topic> <number> — PYQ-style quiz\n/proquiz <topic> <number> — Ultra-level NCERT/PYQ/Assertion quiz')
if '/schedulereset' not in s:s=s.replace('/schedulelist — Current schedule देखें','/schedulelist — सभी schedules देखें\n/scheduleoff <id|all> — schedule हटाएँ\n/schedulereset — सभी schedules reset')
# Preserve earlier generated commands/notification wiring.
if 'app_update_notifier.init(application)' not in s:s=s.replace('vip_scheduler.init_scheduler(application)\n','vip_scheduler.init_scheduler(application)\n    app_update_notifier.init(application)\n')
p.write_text(s);print('All VIP bot modules wired')
