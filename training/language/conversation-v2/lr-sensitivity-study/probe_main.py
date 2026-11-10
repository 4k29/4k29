"""Zero-optimizer resource/artifact/numeric gate on standard public Actions CPU."""
import pathlib,json,hashlib,subprocess,sys,platform,shutil,os,traceback
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3];V=P.parent
BASE="332f26056b882a69ce683d63c394e94697c1c287"
calls=0;receipt=dict(passed=False,optimizer_calls=0,model_forwards=0,execution="GitHub Actions standard ubuntu-latest CPU, public repository",source_commit=BASE)
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def ensure(rel):
 p=ROOT/rel
 if not p.exists():
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(subprocess.check_output(["git","show",BASE+":"+str(rel)],cwd=ROOT))
 return p
def run():
 global calls
 receipt.update(python=sys.version,platform=platform.platform(),processor=platform.processor(),disk_free_bytes=shutil.disk_usage(ROOT).free,cpu_count=os.cpu_count())
 assert os.environ.get("TORCH_SETUP_OUTCOME")=="success","Pinned dependency installation did not succeed"
 import torch,numpy
 assert torch.__version__=="2.14.1+cpu",torch.__version__
 assert numpy.__version__=="2.3.5",numpy.__version__
 assert sys.version_info[:3]==(3,12,14),sys.version
 receipt.update(torch=torch.__version__,numpy=numpy.__version__,torch_threads=2)
 assert shutil.disk_usage(ROOT).free>4*1024**3,"Less than4GiB free"
 mem=int(next(s.split()[1] for s in pathlib.Path("/proc/meminfo").read_text().splitlines() if s.startswith("MemAvailable:")))*1024
 assert mem>4*1024**3,"Insufficient available RAM"
 receipt["mem_available_bytes"]=mem
 old=ensure("training/language/conversation-v2/mixed-volume-study/PLAN.json");plan=json.loads(old.read_text())
 for rel,h in plan["sha256"].items():assert sha(ensure(rel))==h,rel
 receipt["prior_fixed_input_SHA_checks"]=len(plan["sha256"])
 for rel in ["training/language/conversation-v2/PLAN.json","training/language/conversation-v2/mixed-retention-study/UPDATES.jsonl","training/language/conversation-v2/mixed-retention-study/schedule.json.gz"]:
  ensure(rel)
 scratch=ROOT/"scratch";scratch.mkdir(exist_ok=True)
 subprocess.run([sys.executable,str(ensure("training/language/conversation-v2/mixed-retention-study/restore_checkpoint.py")),"--revision",BASE,"--cursor","579","--output",str(scratch/"initial.pt")],check=True)
 assert sha(scratch/"initial.pt")==plan["initial_checkpoint_sha256"]=="fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7"
 subprocess.run([sys.executable,str(ensure("training/language/conversation-v2/mixed-volume-study/restore_checkpoint.py")),"--revision",BASE,"--cursor","401","--output",str(scratch/"control.pt")],check=True)
 assert sha(scratch/"control.pt")=="001522713b3a7adc1f3c419dd259a1f99a4cdedc86957f27b442ad2a93320a41"
 sys.path.insert(0,str(V/"mixed-volume-study"));from mix_runtime import integrity
 a=torch.load(scratch/"initial.pt",map_location="cpu",weights_only=False);b=torch.load(scratch/"control.pt",map_location="cpu",weights_only=False)
 assert integrity(a)==a["integrity"] and integrity(b)==b["integrity"]
 assert a["active_cursor"]==579 and b["active_cursor"]==401
 assert sum(r["targets"] for r in a["trace"])==590144 and sum(r["targets"] for r in b["trace"])==409856
 assert {int(s["step"]) for s in a["trajectory"]["optimizer"]["state"].values()}=={6940}
 assert {int(s["step"]) for s in b["trajectory"]["optimizer"]["state"].values()}=={7341}
 receipt["source_full_state_integrity"]=True;receipt["control_full_state_integrity"]=True;receipt["initial_Adam_step"]=6940
 groups=a["trajectory"]["optimizer"]["param_groups"];receipt["inherited_optimizer_groups"]=[{k:v for k,v in g.items() if k!="params"} for g in groups]
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 sys.path.insert(0,str(V));from core import decoder
 meta=json.loads(ensure("training/language/conversation-v2/mixed-retention-study/parity-terminal/MIX-579/weights-metadata.json").read_text());assert meta["checkpointSha256"]==plan["initial_checkpoint_sha256"]
 refs=json.loads(ensure("training/language/conversation-v2/mixed-retention-study/parity-terminal/MIX-579/python.json").read_text())
 with torch.random.fork_rng():
  m=decoder(a["trajectory"]["config"]);m.load_state_dict(a["trajectory"]["model"]);m.eval()
 errors=[];disagreements=0
 with torch.inference_mode():
  for c in refs:
   for r in c["generation"]["steps"]:
    calls+=1;v=m(torch.tensor([r["inputTokens"]],dtype=torch.long))[0,-1]
    err=float((v.double()-torch.tensor(r["logits"],dtype=torch.float64)).abs().max());errors.append(err);disagreements+=int(int(v.argmax())!=r["argmax"])
 assert len(errors)==12
 receipt.update(initial_numeric_positions=12,max_absolute_logit_error=max(errors),same_history_argmax_disagreements=disagreements,predeclared_tolerance=2e-4,scope="Limited source-state logits gate, not whole-training cross-hardware exactness or Japanese ability")
 assert max(errors)<=2e-4 and disagreements==0,"Cross-environment source-state numerical gate failed"
 receipt["passed"]=True
try:run()
except Exception as exc:
 receipt["error_type"]=type(exc).__name__;receipt["error"]=str(exc);receipt["traceback"]=traceback.format_exc()
finally:
 receipt["model_forwards"]=calls;P.mkdir(parents=True,exist_ok=True);(P/"RESOURCE_MAIN_CPU.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n");print(json.dumps({k:v for k,v in receipt.items() if k not in ["traceback","inherited_optimizer_groups"]},ensure_ascii=False))
if not receipt["passed"]:sys.exit(1)
