"""Single CPU coordinator; never rerun source prefix or replay an advanced branch."""
import pathlib,subprocess,json,sys,os,traceback,hashlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3];V=P.parent;BRANCH="research/inherited-adam-lr3"
def cmd(args,cwd=ROOT):subprocess.run(args,cwd=cwd,check=True)
def sha(f):
 h=hashlib.sha256()
 with pathlib.Path(f).open("rb") as q:
  for b in iter(lambda:q.read(1048576),b""):h.update(b)
 return h.hexdigest()
def write(name,obj):(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
def counts():
 f=P/"UPDATES.jsonl";a=[json.loads(l) for l in f.read_text().splitlines()] if f.exists() else []
 return dict(completed_optimizer_calls=sum(x["event"]=="completed" for x in a),intents=sum(x["event"]=="intent" for x in a),retained_updates=sum(x["event"]=="completed" and x["phase"]=="retained" for x in a))
def publish(message):
 cmd(["git","add","--sparse",str(P.relative_to(ROOT))]);changed=subprocess.run(["git","diff","--cached","--quiet"],cwd=ROOT).returncode
 if changed:
  cmd(["git","-c","user.name=github-actions[bot]","-c","user.email=41898282+github-actions[bot]@users.noreply.github.com","commit","-m",message+" [skip ci]"])
  cmd(["git","push","origin","HEAD:"+BRANCH])
 head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
 remote=subprocess.check_output(["git","ls-remote","origin","refs/heads/"+BRANCH],cwd=ROOT,text=True).split()[0];assert remote==head
 return head
def cold(n,commit):
 folder=ROOT/"cold-restore"/str(n);folder.mkdir(parents=True);cmd(["git","init","--bare","-q",str(folder)])
 cmd(["git","remote","add","origin","https://github.com/4k29/4k29.git"],folder);cmd(["git","config","remote.origin.promisor","true"],folder);cmd(["git","config","remote.origin.partialclonefilter","blob:none"],folder)
 cmd(["git","fetch","--depth=1","--filter=blob:none","origin",commit],folder)
 cmd([sys.executable,str(P/"verify_pinned.py"),"--repository",str(folder),"--cursors",str(n)])
def main():
 assert os.environ.get("GITHUB_RUN_ATTEMPT","1")=="1","No unattended job rerun/replay"
 go=json.loads((P/"GO.json").read_text());assert go["candidate_LR"]==3e-5 and go["planned_updates"]==401
 parent=subprocess.check_output(["git","rev-parse",os.environ.get("GITHUB_SHA","HEAD")+"^"],cwd=ROOT,text=True).strip();assert parent==go["expected_code_commit"]
 cmd([sys.executable,str(P/"prepare.py")])
 publish("Freeze PLAN and all input SHAs before first LR3 optimizer call")
 cmd([sys.executable,"-m","unittest","discover","-s",str(P),"-p","test_contract.py"])
 cmd([sys.executable,str(P/"train.py"),"--until","4","--preflight"])
 # LR has not acted at the first loss/gradient: compare source-state training arithmetic only.
 src=[json.loads(l)["trace"] for l in (V/"mixed-volume-study/UPDATES.jsonl").read_text().splitlines() if json.loads(l)["event"]=="completed" and json.loads(l)["phase"]=="retained"][0]
 b=[json.loads(l)["trace"] for l in (P/"UPDATES.jsonl").read_text().splitlines() if json.loads(l)["event"]=="completed" and json.loads(l)["phase"]=="preflight-original"][0]
 gap={k:abs(src[k]-b[k]) for k in ["loss","gradient_norm"]};assert all(v<=2e-4 for v in gap.values())
 write("FIRST_SOURCE_TRAINING_NUMERIC_CHECK.json",dict(passed=True,differences=gap,tolerance=2e-4,scope="Before any differing LR update: first identical training loss/backward; not whole-trajectory identity",optimizer_calls=0,model_forwards=0))
 publish("Save exact LR3 update-resume and finite-state preflight")
 for n,name in [(4,None),(205,"lr3-mid205"),(401,"lr3-terminal401")]:
  cmd([sys.executable,str(P/"train.py"),"--until",str(n)])
  cmd([sys.executable,str(P/"archive.py"),str(n)])
  write("RUN_STATUS.json",dict(status="TRAINED_FIXED_STAGE",cursor=n,**counts(),planned_updates=401,additional_targets=sum(json.loads(l)["trace"]["targets"] for l in (P/"UPDATES.jsonl").read_text().splitlines() if json.loads(l)["event"]=="completed" and json.loads(l)["phase"]=="retained"),formal_adoption=False))
  commit=publish("Archive LR3 full checkpoint "+str(n));cold(n,commit);publish("Record independent cold full-state restore "+str(n))
  if name:
   cmd([sys.executable,str(P/"evaluate.py"),"--checkpoint",str(ROOT/"scratch"/f"LR3-{n}.pt"),"--name",name,"--format","LF1"])
   cmd([sys.executable,str(P/"nll.py"),"--checkpoint",str(ROOT/"scratch"/f"LR3-{n}.pt"),"--name",name])
   publish("Save LR3 fixed-stage greedy and teacher-forced results "+str(n))
 cmd([sys.executable,str(P/"weight_analysis.py")])
 cmd([sys.executable,str(P/"parity_check.py"),"--models","LR3-401"])
 cmd([sys.executable,str(P/"machine_analysis.py")])
 cmd([sys.executable,str(P/"verify_outputs.py")])
 cmd([sys.executable,"-m","unittest","discover","-s",str(P),"-p","test_contract.py"])
 write("RUN_STATUS.json",dict(status="COMPLETE_RAW_RESULTS_MAIN_SEMANTIC_READING_PENDING",**counts(),additional_targets=409856,cumulative_targets=1000000,new_epochs=0,automatic_replay=0,formal_adoption=False,workflow_run_id=os.environ.get("GITHUB_RUN_ID")))
 publish("Complete LR3 frozen401-update study, raw evaluation and engineering audits")
if __name__=="__main__":
 try:main()
 except Exception as exc:
  write("RUN_STATUS.json",dict(status="STOPPED_FAILURE_REQUIRES_AUDIT",error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc(),**counts(),automatic_replay=0,formal_adoption=False))
  try:publish("Save LR3 failed-stage ledger without replay")
  except Exception:pass
  raise
