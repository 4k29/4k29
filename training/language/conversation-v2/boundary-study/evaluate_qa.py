"""Retain the already source-reviewed human32 DEV; no newly generated answers."""
import argparse,json
from eval_runtime import N, H,V,torch,initial,snapshot,restore_isolated,sha
from prose_decode import greedy
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',default='initial');a=p.parse_args();out=N/'evaluation';out.mkdir(exist_ok=True);path=out/(a.model+'-human32.json');assert not path.exists();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);base=initial()if a.model=='initial'else snapshot(a.model);model,_,_=restore_isolated(base['trajectory']);model.eval();source=V/'foundation-data/evaluation/human-dev.json';cases=json.loads(source.read_text())['cases'];tok=json.loads((V/'data/tokenizer.json').read_text());pieces=[bytes.fromhex(b)for b in tok['bytes']];rows=[]
 with torch.no_grad():
  for c in cases:
   gold=c['goldTokens'];assert gold and all(t>=6 for t in gold);prefix=c['prefixTokens'];s=prefix+gold+[2];assert len(s)<=257;logits=model(torch.tensor([s[:-1]]))[0,len(prefix)-1:];nll=float(torch.nn.functional.cross_entropy(logits,torch.tensor(gold+[2]),reduction='sum'));g=greedy(model,prefix,pieces,max_new=64);rows.append(dict(id=c['id'],component=c['component'],input=c['inputText'],prefix=prefix,human_reference=c['referenceAnswer'],reference_authorship=c['authorship'],reference_nll_sum=nll,reference_target_tokens=len(gold)+1,necessary_string_candidate=(c['referenceAnswer']in g['text']if g['text']else False),automatic_match_not_semantic_pass=True,**g))
 path.write_text(json.dumps(dict(model=a.model,source_sha256=sha(source),cases=rows,optimizer_updates=0,exposed_DEV_not_TEST=True,independent_native_human_evaluation=False),ensure_ascii=False,indent=2)+'\n');print(a.model,'human32 automatic candidates',sum(r['necessary_string_candidate']for r in rows),flush=True)
if __name__=='__main__':main()
