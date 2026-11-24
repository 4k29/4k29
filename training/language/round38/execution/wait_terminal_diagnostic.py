"""Wait for actual training and primary mechanical completion; do not train."""
import pathlib,time,json,subprocess,sys
E=pathlib.Path(__file__).resolve().parent;R=E.parent
while True:
 time.sleep(45)
 try:
  p=E/'automatic-publish-complete.json';r=R/'continue-10000/result.json'
  if p.exists()and r.exists()and json.loads(p.read_text())['actualRetainedAdditionalUpdates']==10000 and json.loads(r.read_text())['completedRun']:break
 except (json.JSONDecodeError,FileNotFoundError):continue
raise SystemExit(subprocess.run([sys.executable,str(E/'assess_terminal_state.py')],cwd=R.parents[2]).returncode)
