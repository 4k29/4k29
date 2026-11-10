"""Same-source parameter displacements and saved Adam stages; zero forwards/updates."""
from mix_runtime import *
import collections,math,subprocess
BASE="332f26056b882a69ce683d63c394e94697c1c287"
torch.set_num_threads(2)
initial=torch.load(SCRATCH/"initial.pt",map_location="cpu",weights_only=False)["trajectory"]["model"];output={}
for arm in ["A_LR1e5","B_LR3e5"]:
 for n in [4,205,401]:
  if arm.startswith("A"):
   path=SCRATCH/(f"control-{n}.pt")
   if n==401:path=SCRATCH/"control.pt"
   if not path.exists():subprocess.run([sys.executable,str(V/"mixed-volume-study/restore_checkpoint.py"),"--revision",BASE,"--cursor",str(n),"--output",str(path)],check=True)
  else:path=SCRATCH/f"LR3-{n}.pt"
  obj=torch.load(path,map_location="cpu",weights_only=False);assert {int(v["step"]) for v in obj["trajectory"]["optimizer"]["state"].values()}=={6940+n}
  groups=collections.defaultdict(lambda:[0.,0.,0,0.])
  for k,w in initial.items():
   d=obj["trajectory"]["model"][k].double()-w.double();key=".".join(k.split(".")[:2]) if k.startswith("blocks.") else k.split(".")[0];z=groups[key];z[0]+=float(d.square().sum());z[1]+=float(w.double().square().sum());z[2]+=w.numel();z[3]=max(z[3],float(d.abs().max()))
  output[arm+"-"+str(n)]=dict(checkpoint_sha256=sha(path),Adam_step=6940+n,groups={k:dict(delta_L2=math.sqrt(z[0]),relative_L2=math.sqrt(z[0]/z[1]),delta_RMS=math.sqrt(z[0]/z[2]),max_absolute_delta=z[3],parameters=z[2]) for k,z in groups.items()},global_delta_L2=math.sqrt(sum(z[0] for z in groups.values())),not_evidence_of_language_ability=True)
  del obj
write(P/"WEIGHT_DELTA_COMPARE.json",dict(stages=output,optimizer_calls=0,model_forwards=0,scope="A and B checkpoint displacement from identical source, not sum of per-step updates. B UPDATE_MAGNITUDES contains actual per-update norm separately."))
