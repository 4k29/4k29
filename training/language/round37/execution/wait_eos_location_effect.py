"""Read-only EOS location diagnostic once the already-running training reaches5000."""
import pathlib,time,subprocess,sys,json,datetime
E=pathlib.Path(__file__).resolve().parent
while not (E/'retained-paired-5000/snapshot.json').exists():time.sleep(30)
assert json.loads((E/'retained-paired-5000/snapshot.json').read_text())['actualUpdates']==5000
if (E/'eos-location-effect-5000.json').exists():raise SystemExit('Existing diagnostic; do not duplicate')
subprocess.run([sys.executable,str(E/'audit_eos_location_effect.py')],check=True)
