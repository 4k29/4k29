"""Read-only numerical aggregation; semantic labels are explicit main-agent judgments."""
import json,pathlib,statistics,collections
P=pathlib.Path(__file__).resolve().parent
def read(f):return json.loads((P/f).read_text())
def mean(a):return statistics.mean(a)
def boundary(name):
 c=read("evaluation/"+name+"-boundaries.json")["cases"];tf=[t for r in c for t in r["TF"]["C"][1:]]
 paired=[r for r in c if r.get("U")]
 return dict(n=len(c),LF_argmax=sum(r["C"]["argmax"]==16 for r in c),mata_argmax=sum(r["C"]["argmax"]==3749 for r in c),space_argmax=sum(r["C"]["argmax"]==38 for r in c),ordinary_nonwhitespace_argmax=sum(r["C"]["argmax"]>5 and r["C"]["argmax"] not in [16,38] for r in c),gold_top1=sum(r["C"]["gold"]["rank"]==1 for r in c),other16_gold_top1=sum(r["group"]=="other" and r["C"]["gold"]["rank"]==1 for r in c),P_LF=mean([r["C"]["P_LF"]["P"] for r in c]),P_mata=mean([r["C"]["P_mata"]["P"] for r in c]),P_space=mean([r["C"]["P_space"]["P"] for r in c]),gold_mean_rank=mean([r["C"]["gold"]["rank"] for r in c]),TF2_8_NLL=mean([-t["gold"]["logP"] for t in tf]),paired_n=len(paired),positive_context_delta=sum(r["delta"]>0 for r in paired),mean_context_delta=mean([r["delta"] for r in paired]),TF2_8_context_delta=mean([t["gold"]["logP"]-r["TF"]["U"][i+1]["gold"]["logP"] for r in paired for i,t in enumerate(r["TF"]["C"][1:])]))
def aggregate():
 a=read("BASELINE_REFERENCE.json");out=dict(A=a,stages={},optimizer=read("OPTIMIZATION_COMPARE.json"),forwards=read("FORWARD_COUNTS.json"),formal_adoption=False,independent_human_evaluation=False)
 for stage,label in [("lr3-mid205","mid205"),("lr3-terminal401","terminal401")]:
  raw=read("evaluation/"+stage+".json");adj=read("ADJUDICATION-"+label+".json");nll=read("NLL/"+stage+".json")
  out["stages"][stage]=dict(semantic_counts=dict(collections.Counter(r["panel"] for r in adj["decisions"] if r["decision"]=="natural_short_text_only")),caption_change=adj["caption_change"],raw_EOS_repeat4=raw["counts"],body_NLL=nll["groups"],all_valid_NLL=nll["all_valid_token_groups"],boundary=boundary(stage),self_history_success=adj["self_history_success"])
 return out
if __name__=="__main__":
 (P/"RESULTS_SUMMARY.json").write_text(json.dumps(aggregate(),ensure_ascii=False,indent=2)+"\n")
 print("Read-only aggregation complete: optimizer0, model_forward0; no semantic label inferred.")
