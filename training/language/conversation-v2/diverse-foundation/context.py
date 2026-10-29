"""Fixed nine-family zero-update context use diagnostic; no new TEST or optimizer changes."""
import argparse,math
from common import *
from study_checkpoint import load,model_history

def protocol():
 cases=read(P/'DEV_PROTOCOL.json')['cases'];by={r['id']:r for r in gzrows(P/'corpus-clean.jsonl.gz')};rows=[]
 for i,c in enumerate(cases):
  other=by[cases[(i+1)%len(cases)]['source_id']];wrong=other['body_tokens'][:len(c['prefix'])];gold=c['reference_suffix'][:64];assert len(gold)==64 and len(wrong)==len(c['prefix'])and other['component']!=c['component'];rows.append(dict(id=c['id'],source_id=c['source_id'],prefix=c['prefix'],wrong_prefix=wrong,wrong_source_id=other['id'],gold=gold,scored_target_positions=list(range(1,64))))
 return dict(cases=rows,scope='Exposed exploratory DEV; correct and wrong prefixes exact same length. No-context uses first gold token as seed; all score the same remaining63 gold tokens. No-context absolute positions/length differ and are an ablation confound. Character-CJK proxy is not a linguistic content-word tagger or semantic-comprehension score.',optimizer_updates=0,source_protocol_sha256=sha(P/'DEV_PROTOCOL.json'))
def main():
 a=argparse.ArgumentParser();a.add_argument('--freeze',action='store_true');a.add_argument('--arm');args=a.parse_args()
 if args.freeze:write(D/'CONTEXT_ABLATION_PROTOCOL.json',protocol());return
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 model,cursor=load(args.arm)
 model.eval();proto=read(D/'CONTEXT_ABLATION_PROTOCOL.json');pieces=[bytes.fromhex(x)for x in read(V/'data/tokenizer.json')['bytes']];rows=[]
 with torch.inference_mode():
  for c in proto['cases']:
   gold=c['gold'];result={}
   for label,prefix in [('correct',c['prefix']),('unrelated',c['wrong_prefix']),('removed',[])]:
    seq=prefix+gold[:-1];log=model(torch.tensor([seq]))[0,len(prefix):];lp=log.log_softmax(-1);target=torch.tensor(gold[1:]);chosen=lp.argmax(-1);nll=-lp[torch.arange(63),target];mask=[]
    for t in gold[1:]:
     try:s=pieces[t].decode()
     except UnicodeDecodeError:s=''
     mask.append(any('一'<=x<='鿿'for x in s))
    result[label]=dict(NLL=float(nll.mean()),gold_top1=float(chosen.eq(target).float().mean()),target_count=63,CJK_spelling_proxy_targets=sum(mask),CJK_proxy_NLL=float(nll[torch.tensor(mask)].mean())if any(mask)else None,per_target_NLL=[float(z)for z in nll])
   rows.append(dict(id=c['id'],correct_minus_unrelated_NLL=result['correct']['NLL']-result['unrelated']['NLL'],correct_minus_removed_NLL=result['correct']['NLL']-result['removed']['NLL'],conditions=result))
 summary=dict(arm=args.arm,paired_targets=567,mean_correct_minus_unrelated_NLL=sum(r['correct_minus_unrelated_NLL']for r in rows)/9,mean_correct_minus_removed_NLL=sum(r['correct_minus_removed_NLL']for r in rows)/9,correct_better_than_unrelated_cases=sum(r['correct_minus_unrelated_NLL']<0 for r in rows),context_understanding_not_proven_by_NLL=True,formal_native_human=False)
 out=D/'context';out.mkdir(exist_ok=True);write(out/(args.arm+'.json'),dict(protocol_sha256=sha(D/'CONTEXT_ABLATION_PROTOCOL.json'),summary=summary,rows=rows));print(summary)
if __name__=='__main__':main()
