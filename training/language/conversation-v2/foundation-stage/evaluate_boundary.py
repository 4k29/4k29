"""Supplemental full-source-BPE boundary comparison, never replaces primary24."""
import argparse,gzip,json
from runtime import H,V,torch,initial,snapshot,restore_isolated
from prose_decode import greedy
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',default='initial');a=p.parse_args();units={r['id']:r for r in map(json.loads,gzip.open(H/'data.jsonl.gz','rt'))};original=json.loads((H/'prose-dev.json').read_text())['cases'];tok=json.loads((V/'data/tokenizer.json').read_text());pieces=[bytes.fromhex(x)for x in tok['bytes']];cs=[]
 for c in original:
  s=units[c['unit_id']]['tokens'];b=b'';options=[]
  for pos,t in enumerate(s):
   if t==2:break
   b+=pieces[t]
   try:text=b.decode('utf-8')
   except UnicodeDecodeError:continue
   if text:options.append((abs(len(text)-len(c['prefix_text'])),len(text)<len(c['prefix_text']),pos+1,text))
   if len(text)>len(c['prefix_text'])+10:break
  _,_,L,text=min(options);prefix=s[:L];gold=s[L:L+128];assert prefix and len(prefix)+128<=256 and gold
  cs.append(dict(id=c['id'],source_unit=c['unit_id'],prefix=prefix,prefix_text=text,original_prefix=c['prefix'],original_prefix_text=c['prefix_text'],reference_tokens=gold))
 protocol=H/'TOKEN_BOUNDARY_PROTOCOL.json'
 if not protocol.exists():protocol.write_text(json.dumps(dict(scope='Supplement fixed after initial primary outputs but before any foundation terminal output read; full source BPE prefix ending at nearest valid UTF8 char; primary24 unchanged; same source components, not new TEST',cases=cs),ensure_ascii=False,indent=2)+'\n')
 else:assert json.loads(protocol.read_text())['cases']==cs
 out=H/'evaluation'/(a.model+'-token-boundary.json');assert not out.exists();torch.set_num_threads(2);torch.use_deterministic_algorithms(True);base=initial()if a.model=='initial'else snapshot(a.model);model,_,_=restore_isolated(base['trajectory']);model.eval();rows=[]
 with torch.no_grad():
  for c in cs:
   s=c['prefix']+c['reference_tokens'];logits=model(torch.tensor([s[:-1]]))[0,len(c['prefix'])-1:];loss=torch.nn.functional.cross_entropy(logits,torch.tensor(c['reference_tokens']),reduction='sum');g=greedy(model,c['prefix'],pieces,gold=c['reference_tokens'],tf_logits=logits,max_new=128);rows.append(dict(**c,reference_nll_sum=float(loss),**g))
 out.write_text(json.dumps(dict(model=a.model,cases=rows,optimizer_updates=0,not_primary_adoption_gate=True),ensure_ascii=False,indent=2)+'\n');print(a.model,'token boundary evaluation saved',flush=True)
if __name__=='__main__':main()
