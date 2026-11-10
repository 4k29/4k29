"""Machine diagnostics only; semantic judgments are reserved for main-agent full reading."""
import pathlib,json,collections,statistics,hashlib,csv,gzip,subprocess,sys,shutil
P=pathlib.Path(__file__).resolve().parent;V=P.parent;A=V/"mixed-volume-study";ROOT=P.parents[3]
load=lambda f:json.loads(f.read_text())
def write(name,x):(P/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+"\n")
rows=[json.loads(x) for x in (P/"UPDATES.jsonl").read_text().splitlines()];done=[r for r in rows if r["event"]=="completed"];ret=[r["trace"] for r in done if r["phase"]=="retained"]
assert len(done)==405 and len(ret)==401 and sum(r["targets"] for r in ret)==409856
assert [(r["phase"],r["trace"]) for r in rows if r["event"]=="intent"]==[(r["phase"],r["trace"]) for r in done]
base=[json.loads(x)["trace"] for x in (A/"UPDATES.jsonl").read_text().splitlines() if json.loads(x)["event"]=="completed" and json.loads(x)["phase"]=="retained"];assert len(base)==401
for a,b in zip(base,ret):assert a["step"]==b["step"] and a["targets"]==b["targets"] and a["source_targets"]==b["source_targets"]
def stats(rs):
 return dict(updates=len(rs),targets=sum(r["targets"] for r in rs),target_weighted_TRAIN_loss=sum(r["loss"]*r["targets"] for r in rs)/sum(r["targets"] for r in rs),gradient_min=min(r["gradient_norm"] for r in rs),gradient_mean=statistics.mean(r["gradient_norm"] for r in rs),gradient_max=max(r["gradient_norm"] for r in rs),clipped_updates=sum(r["clipped"] for r in rs))
with (P/"LOSS_COMPARE.csv").open("w",newline="") as f:
 w=csv.writer(f,lineterminator="\n");w.writerow(["step","targets","LR1e5_loss","LR3e5_loss","LR1e5_grad","LR3e5_grad","LR1e5_clip","LR3e5_clip"])
 for a,b in zip(base,ret):w.writerow([a["step"],a["targets"],a["loss"],b["loss"],a["gradient_norm"],b["gradient_norm"],a["clipped"],b["clipped"]])
write("OPTIMIZATION_COMPARE.json",dict(A=stats(base),B=stats(ret),retained_updates=401,actual_optimizer_calls=405,preflight_original=3,replay_validation=1,recovery_replay=0,process_training_seconds=sum(load(P/f"TRAIN-{i}.json")["elapsed_process_seconds"] for i in [4,205,401]),peak_RSS_KiB=max(load(P/f"TRAIN-{i}.json")["max_RSS_KiB"] for i in [4,205,401]),semantic_scoring_pending=True))
pieces=[bytes.fromhex(t) for t in load(V/"data/tokenizer.json")["bytes"]];text=lambda ids:b"".join(pieces[t] for t in ids if t>5).decode("utf8","backslashreplace")
shutil.copy2(A/"review_cards.py",P/"review_cards.py")
for name,base_name in [("lr3-mid205","midpoint-800k"),("lr3-terminal401","terminal-1M")]:
 subprocess.run([sys.executable,str(P/"review_cards.py"),name],check=True,stdout=subprocess.DEVNULL)
 x=load(P/"evaluation"/(name+".json"));y=load(A/"evaluation"/(base_name+".json"));by={(r["panel"],r["id"]):r for r in y["cases"]};same=[]
 for r in x["cases"]:
  b=by[(r["panel"],r["id"])];assert r["prefix"]==b["prefix"] and r["maxNewTokens"]==b["maxNewTokens"]
  if all(r[k]==b[k] for k in ["prefix","tokensIncludingEos","rawBytesHex"]):same.append([r["panel"],r["id"]])
 for panel in sorted({r["panel"] for r in x["cases"]}):
  cards=[dict(id=r["id"],panel=panel,prefix=text(r["prefix"]),requirement=r.get("requirement"),generation=r["text"],EOS=r["eos"],repeat4gram=r["repeated4gram"],reference_output=by[(panel,r["id"])]["text"]) for r in x["cases"] if r["panel"]==panel]
  write("REVIEW-"+name+"-"+panel+".json",cards)
 write("REUSE-"+name+".json",dict(exact_same_prefix_tokens_bytes=same,baseline=base_name))
 write("SELF-"+name+".json",[dict(id=e["id"],turns=[dict(prefix=text(t.get("prefix",[])),generation=t.get("text"),EOS=t.get("eos"),tokens=t.get("tokensIncludingEos")) for t in e["turns"]]) for e in x["self_history"]])
counts=dict(training=405,probe_source_numeric=12,worker_source_numeric=12,midpoint=load(P/"evaluation/lr3-mid205.json")["forward_calls"],terminal=load(P/"evaluation/lr3-terminal401.json")["forward_calls"],NLL=sum(load(P/"NLL"/f"{n}.json")["model_forwards"] for n in ["lr3-mid205","lr3-terminal401"]),parity=load(P/"parity-terminal-summary.json")["LR3-401"]["comparison_positions"]);counts["Python_total"]=sum(counts.values());counts["JS_score_queries"]=24
write("FORWARD_COUNTS.json",counts)
write("EVALUATION_STATUS.json",dict(status="RAW_EVALUATIONS_COMPLETE_MAIN_SEMANTIC_READING_PENDING",counts={n:load(P/"evaluation"/(n+".json"))["counts"] for n in ["lr3-mid205","lr3-terminal401"]},optimizer_updates=0,sealed_TEST_used=False,independent_human_evaluation=False))
write("CHECKPOINT_INDEX.json",dict(initial_checkpoint_SHA=load(P/"PLAN.json")["initial_checkpoint_sha256"],saved=[dict(manifest=load(P/f"artifacts/LR3-{i}/checkpoint.json"),cold_Git_restore=load(P/f"GIT_RESTORE-{i}.json")) for i in [4,205,401]],formal_adoption=False))
print("All405 optimizer calls,401retained,149prefixes,raw outputs ready; semantic scoring pending",flush=True)
