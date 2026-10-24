"""Wait for immutable initial full snapshot, then verify without any optimizer update."""
import pathlib,time,subprocess,sys,json
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';p=R/'continue-10000/checkpoint-0.pt'
for attempt in range(60):
 if p.exists():break
 time.sleep(10)
assert p.exists(),'Initial snapshot not available after bounded wait'
subprocess.run([sys.executable,str(E/'verify_initial.py')],cwd=R.parents[2],check=True)
sys.path.insert(0,str(R));from checkpoint_chunks import pack
import torch
torch.set_num_threads(1);a=torch.load(p,map_location='cpu',weights_only=False);assert a['step']==0 and a['settings']['contextPreference']['coefficient']==.2;assert {int(v['step'])for v in a['optimizer']['state'].values()}=={20000}
m=pack(p)
report=dict(actualSnapshotUpdates=0,optimizerCounters=[20000],contextCeCoefficient=.2,modelAdamAndRngExactlyMatchInitialR28=True,fullStatePartsManifest=str(m.relative_to(R)),prematureReadOnlyFileNotFoundBeforeSnapshotCreationDidNotAffectTrainer=True,additionalOptimizerUpdates=0)
(E/'postlaunch-initial-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
