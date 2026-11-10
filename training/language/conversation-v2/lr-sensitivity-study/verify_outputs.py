"""Saved input/ledger/raw byte/cold restore checks. No model execution."""
import pathlib,json,hashlib,gzip
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3];V=P.parent;load=lambda f:json.loads(f.read_text())
def sha(f):
 h=hashlib.sha256()
 with f.open("rb") as q:
  for b in iter(lambda:q.read(1048576),b""):h.update(b)
 return h.hexdigest()
plan=load(P/"PLAN.json")
for rel,h in plan["sha256"].items():assert sha(ROOT/rel)==h,rel
assert sha(P/"PLAN.json")==(P/"PLAN.sha256").read_text().split()[0]
events=[json.loads(l) for l in (P/"UPDATES.jsonl").read_text().splitlines()];done=[r for r in events if r["event"]=="completed"];assert len(done)==405
assert [(r["phase"],r["trace"]) for r in events if r["event"]=="intent"]==[(r["phase"],r["trace"]) for r in done]
ret=[r["trace"] for r in done if r["phase"]=="retained"];assert [r["step"] for r in ret]==list(range(1,402));assert sum(r["targets"] for r in ret)==409856 and all(r["lr"]==3e-5 for r in ret)
mag=[json.loads(l) for l in (P/"UPDATE_MAGNITUDES.jsonl").read_text().splitlines()];assert len(mag)==405
for r in mag:assert r["Adam_steps"]==[6940+r["step"]] and r["LR"]==3e-5
for n in [4,205,401]:
 m=load(P/f"artifacts/LR3-{n}/checkpoint.json");proof=load(P/f"GIT_RESTORE-{n}.json");assert proof["passed"] and proof["sha256"]==m["sha256"]
 h=hashlib.sha256()
 for c in m["chunks"]:
  f=P/f"artifacts/LR3-{n}"/c["path"];assert sha(f)==c["sha256"]
  with f.open("rb") as q:
   for b in iter(lambda:q.read(1048576),b""):h.update(b)
 assert h.hexdigest()==m["sha256"]
pieces=[bytes.fromhex(x) for x in load(V/"data/tokenizer.json")["bytes"]];nr=nt=0
for name,base in [("lr3-mid205","midpoint-800k"),("lr3-terminal401","terminal-1M")]:
 x=load(P/"evaluation"/(name+".json"));a=load(V/"mixed-volume-study/evaluation"/(base+".json"));by={(r["panel"],r["id"]):r for r in a["cases"]};assert len(x["cases"])==149;nr+=149
 ts=[t for e in x["self_history"] for t in e["turns"]];nt+=len(ts)
 for r in x["cases"]:assert r["prefix"]==by[(r["panel"],r["id"])]["prefix"] and r["maxNewTokens"]==by[(r["panel"],r["id"])]["maxNewTokens"]
 for r in x["cases"]+ts:
  if r.get("unsupported_full_history"):continue
  assert len(r["prefix"])+len(r["nonEosTokens"])<=256
  assert b"".join(pieces[t] for t in r["nonEosTokens"] if t>5).hex()==r["rawBytesHex"]
  assert r["eos"]==(r["tokensIncludingEos"][-1]==2)
receipt=dict(passed=True,actual_optimizer_calls=405,retained_updates=401,additional_targets=409856,raw_single_prompt_cases=nr,self_history_raw_turns=nt,all_prefixes_and_budgets_identical=True,cold_Git_restores=[4,205,401],frozen_SHA_checks=len(plan["sha256"]),model_forwards=0,optimizer_calls=0)
(P/"FINAL_VERIFICATION.json").write_text(json.dumps(receipt,indent=2)+"\n");print(receipt,flush=True)
