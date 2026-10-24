"""Recover read-only terminal evaluation after primary diagnostic file omission."""
import pathlib,time,subprocess,sys,json
E=pathlib.Path(__file__).resolve().parent;R=E.parent
while not all((E/n).exists()for n in ['new-validation.json','daily-new-python.json','content-native-dev/new-python.json']):time.sleep(10)
assert not(E/'terminal-state-diagnostic/mechanical-complete.json').exists()
with(E/'terminal-recovery.log').open('ab',buffering=0)as log:status=subprocess.run([sys.executable,str(E/'assess_terminal_state.py')],cwd=R.parents[2],stdout=log,stderr=subprocess.STDOUT).returncode
(E/'terminal-recovery-status.json').write_text(json.dumps(dict(exitCode=status,additionalOptimizerUpdates=0))+'\n')
raise SystemExit(status)
