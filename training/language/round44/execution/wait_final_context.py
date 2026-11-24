"""Run only the predeclared read-only final TRAIN diagnostic after publication."""
import pathlib,time,json,subprocess,sys
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
while True:
 p=E/'automatic-publish-complete.json'
 if p.exists() and json.loads(p.read_text())['actualRetainedAdditionalUpdates']==10000:break
 time.sleep(45)
subprocess.run([sys.executable,str(E/'context_final_diagnostic.py')],cwd=R.parents[2],check=True)
