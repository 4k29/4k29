"""Wait for actual training and primary mechanical completion; do not train."""
import pathlib,time,json,subprocess,sys
E=pathlib.Path(__file__).resolve().parent;R=E.parent
while True:
 time.sleep(45)
 try:
  p=E/'automatic-publish-complete.json';r=R/'continue-10000/result.json'
  if p.exists()and r.exists()and json.loads(p.read_text())['actualRetainedAdditionalUpdates']==10000 and json.loads(r.read_text())['completedRun']:
   required=[('new-validation.json',17),('daily-new-python.json',12),('content-native-dev/new-python.json',8)]
   if all((E/name).exists() and len(json.loads((E/name).read_text())['rows'])==count for name,count in required):break
 except (json.JSONDecodeError,FileNotFoundError):continue
raise SystemExit(subprocess.run([sys.executable,str(E/'assess_terminal_state.py')],cwd=R.parents[2]).returncode)
