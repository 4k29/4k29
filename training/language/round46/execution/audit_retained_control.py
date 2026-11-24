"""Read-only immutable matched-update audits; source-mixture differences are allowed."""
import pathlib,subprocess,time,sys
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
for step in [200,1000,5000]:
 while not(E/f'retained-snapshots/{step}/identity.json').exists():time.sleep(20)
 p=subprocess.run([sys.executable,str(E/'audit_matched_snapshot.py'),str(step)],cwd=R.parents[2],capture_output=True,text=True)
 print(p.stdout if not p.returncode else p.stderr,flush=True)
 if p.returncode:(E/'matched-snapshot-audit-failure.txt').write_text(p.stderr);raise SystemExit(p.returncode)
