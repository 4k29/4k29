"""Freeze an LR-only continuation after the separate zero-update host gate."""
import pathlib,json,gzip,hashlib,shutil,subprocess,sys,collections,inspect
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3];V=P.parent;A=V/"mixed-volume-study";BASE="332f26056b882a69ce683d63c394e94697c1c287"
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def ensure(rel):
 f=ROOT/rel
 if not f.exists():
  f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(subprocess.check_output(["git","show",BASE+":"+str(rel)],cwd=ROOT))
 return f
def write(name,obj):(P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n")
assert not(P/"PLAN.json").exists(),"Do not reconstruct frozen experiment"
gate=json.loads((P/"RESOURCE_MAIN_CPU.json").read_text());assert gate["passed"] and gate["optimizer_calls"]==0
original=json.loads(ensure("training/language/conversation-v2/mixed-volume-study/PLAN.json").read_text())
for rel,h in original["sha256"].items():assert sha(ensure(rel))==h,rel
for name in ["corpus.json.gz","schedule.json.gz","POSITION_MAP.json.gz","DEV_BODY_NLL.json.gz","SOURCE_AUDIT.json","TEACHER_AUDIT.json","PREFIX_POSITIONS.json.gz","BOUNDARY_EXPOSURE.json"]:
 src=ensure(str((A/name).relative_to(ROOT)));shutil.copy2(src,P/name);assert sha(src)==sha(P/name)
required=[
"training/language/conversation-v2/PLAN.json",
"training/language/conversation-v2/paragraph-foundation/evaluation/B-579.json",
"training/language/conversation-v2/paragraph-foundation/panels/B-579.json",
"training/language/conversation-v2/foundation-stage/TOKEN_BOUNDARY_PROTOCOL.json",
"training/language/conversation-v2/mixed-retention-study/parity-terminal/MIX-579/python.json",
"training/language/conversation-v2/mixed-retention-study/parity-terminal/MIX-579/weights-metadata.json",
"training/language/conversation-v2/mixed-volume-study/UPDATES.jsonl",
"training/language/conversation-v2/mixed-volume-study/NLL/terminal-1M.json",
"training/language/conversation-v2/mixed-volume-study/evaluation/terminal-1M.json",
"training/language/conversation-v2/mixed-volume-study/evaluation/midpoint-800k.json",
"training/language/conversation-v2/mixed-volume-study/evaluation/terminal-1M-boundaries.json",
"training/language/conversation-v2/mixed-volume-study/evaluation/midpoint-800k-boundaries.json",
"training/language/conversation-v2/mixed-volume-study/evaluation/terminal-1M-READING.json",
"training/language/conversation-v2/mixed-volume-study/evaluation/midpoint-800k-READING.json",
"training/language/conversation-v2/mixed-volume-study/terminal-1M-CAPTION_DECISIONS.json",
"training/language/conversation-v2/mixed-retention-study/evaluation/terminal-MIX.json",
"training/language/conversation-v2/mixed-retention-study/terminal-MIX-CAPTION_DECISIONS.json",
"training/language/conversation-v2/mixed-volume-study/review_cards.py"]
for rel in required:ensure(rel)
c=json.load(gzip.open(P/"corpus.json.gz","rt"));s=json.load(gzip.open(P/"schedule.json.gz","rt"));maps=json.load(gzip.open(P/"POSITION_MAP.json.gz","rt"));old={tuple(r) for r in json.load(gzip.open(P/"PREFIX_POSITIONS.json.gz","rt"))};seen=set();by=collections.Counter()
for batch in s:
 for r in batch:
  i=r["record"];t=c[i]["tokens"][r["start"]:r["start"]+r["length"]];assert len(t)==r["length"] and 2<=len(t)<=257
  for j,v in enumerate(t[1:],r["start"]+1):
   key=(c[i]["source"],c[i]["id"],maps[i]["new_to_original_token_position"][j]);assert key not in old and key not in seen;seen.add(key);by[c[i]["source"]]+=1
assert len(s)==401 and len(old)==590144 and len(seen)==409856
assert sum(r["length"]-1 for b in s[:205] for r in b)==209856
assert gate["initial_Adam_step"]==6940 and gate["source_full_state_integrity"] and gate["control_full_state_integrity"]
groups=gate["inherited_optimizer_groups"];assert len(groups)==1 and groups[0]["betas"]==[.9,.999] and groups[0]["eps"]==1e-8 and groups[0]["weight_decay"]==.05
write("CONDITION_MATCH_AUDIT.json",dict(passed=True,only_learning_hyperparameter_changed="LR1e-5 to3e-5",initial_state_identical_by_full_checkpoint_SHA=True,initial_SHA=original["initial_checkpoint_sha256"],initial_Adam_step=6940,inherited_optimizer_groups=groups,corpus_byte_identical=True,schedule_byte_identical=True,mapping_byte_identical=True,prior_fixed_SHA_checks=49,additional_distinct_positions=len(seen),prior_prefix_positions=len(old),overlap=0,per_source_targets=dict(by),unchanged_numeric_functions=["causal_ce","clip_grad_accurate","AdamW.step","core.decoder"],nonnumeric_changes=["independent output paths","Actions filesystem reserve/ledger location","finite-state assertions","detached delta diagnostics"],gate=gate,model_forwards=0,optimizer_calls=0))
inputs=dict(original["sha256"])
for f in list(P.glob("*.py"))+list(P.glob("*.gz"))+[P/"SOURCE_AUDIT.json",P/"TEACHER_AUDIT.json",P/"CONDITION_MATCH_AUDIT.json",P/"PREPLAN.json",P/"GO.json"]+[ROOT/r for r in required]:
 inputs[str(f.relative_to(ROOT))]=sha(f)
write("PLAN.json",dict(study="inherited-adam-lr-sensitivity-v1",run_id="lr3-v1",initial_checkpoint_sha256=original["initial_checkpoint_sha256"],initial_Adam_step=6940,initial_model_counter=13399,control_LR=1e-5,LR=3e-5,clip=1.,optimizer="Inherited AdamW; beta/epsilon/weight_decay unchanged",updates=401,additional_targets=409856,prefix_targets=590144,cumulative_targets=1000000,save_points=[4,205,401],checkpoint_selection="Fixed terminal only, midpoint diagnostic",model="Own11.23M/BPE3997/context256/LF1/ordinary causal CE",sha256=inputs,source_commit=BASE,code_commit=json.loads((P/"GO.json").read_text())["expected_code_commit"],new_epochs=0,new_acquisition_tokens=0,preflight_calls=4,source_numeric_gate_forward_calls_this_worker=12,source_numeric_gate_forward_calls_prior_probe=12,generation="Same149 exposed diagnostic prompts+4episodes, whole-vocabulary greedy and original max budgets; no penalties/repair/forced words",limits="Public standard Actions CPU only, torch2threads,finite states,4GiBinitialdisk/500MiBatomic reserve/1GiBRAM reserve,stop on ledger mismatch; no automatic replay",cross_hardware="Source12logits gate exact on probe; limited scope, not whole trajectory hardware equality",formal_adoption=False,independent_human_evaluation=False))
(P/"PLAN.sha256").write_text(sha(P/"PLAN.json")+"  PLAN.json\n")
print("PLAN FROZEN, identical401 batches/409856positions, only LR change; optimizer0",flush=True)
