"""Frozen whole-vocabulary greedy and mapped body-only teacher forcing."""
from mix_runtime import *
from build import collapse
from collections import Counter
import argparse
sys.path.insert(0,str(V/'foundation-stage'));from prose_decode import greedy
sys.path.insert(0,str(V));from core import decoder
from new_tokenizer import Encoder

@torch.inference_mode()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--checkpoint',required=True);ap.add_argument('--name',required=True);ap.add_argument('--format',choices=['LF1','LF2'],required=True);ap.add_argument('--boundaries-only',action='store_true');a=ap.parse_args();out=P/'evaluation';out.mkdir(exist_ok=True);dest=out/(a.name+'.json');assert not dest.exists(),'No overwrite'
 torch.set_num_threads(2);torch.use_deterministic_algorithms(True);start=time.monotonic();obj=torch.load(a.checkpoint,map_location='cpu',weights_only=False);st=obj['trajectory']
 with torch.random.fork_rng():m=decoder(st['config']);m.load_state_dict(st['model']);m.eval()
 calls=[0];original=m.forward
 def counted(*args,**kw):calls[0]+=1;return original(*args,**kw)
 m.forward=counted
 pieces=[bytes.fromhex(x) for x in read(V/'data/tokenizer.json')['bytes']];enc=Encoder(read(V/'data/tokenizer.json'))
 def cv(t):return collapse(t)[0] if a.format=='LF1' else t[:]
 def metrics(v,g):
  lp=v.double().log_softmax(-1);pr=lp.exp();ids=v.topk(10).indices.tolist()
  def stat(t):return dict(P=float(pr[t]),rank=1+int((v>v[t]).sum()),logP=float(lp[t]))
  return dict(P_LF=stat(16),P_mata=stat(3749),gold=stat(g),argmax=int(v.argmax()),body_argmax=int(v.argmax())>5 and int(v.argmax())!=16,entropy=float(-(pr*lp).sum()),top10=[dict(token=i,P=float(pr[i])) for i in ids])
 old=V/'paragraph-foundation';pairs=read(old/'paragraph-context-use/INPUT_PAIRS.json');corpus=[json.loads(l) for l in gzip.open(old/'corpus.jsonl.gz','rt')];by={r['id']:r for r in corpus};boundary=[]
 for q in pairs:
  c=q['correct'];boundary.append(dict(id='new32-'+str(q['index']),group=q['group'],prefix=c['history_tokens'],unrelated=q['unrelated']['history_tokens'],gold=q['gold'],tail=c['tail_tokens'][:8]))
 for c in read(old/'newline-followup/EIGHT_CASE_AUDIT.json')['cases']:
  r=by[c['source_id']];pos=c['source_offset'];assert r['tokens'][pos]==c['gold']
  boundary.append(dict(id='old8-'+str(c['index']),group='old8',prefix=c['history_tokens'],gold=c['gold'],tail=r['tokens'][pos:pos+8]))
 results=[]
 for c in boundary:
  row={k:v for k,v in c.items() if k not in ['prefix','unrelated']};row['inputs']={};row['TF']={}
  for kind,orig in [('C',c['prefix'])]+([('U',c['unrelated'])] if 'unrelated' in c else []):
   pref=cv(orig);tail=cv(c['tail']);assert tail and tail[0]==c['gold'];n=min(8,len(tail),257-len(pref));seq=pref+tail[:n-1];v=m(torch.tensor([seq]))[0,len(pref)-1:];assert len(v)==n
   row['inputs'][kind]=pref;row[kind]=metrics(v[0],c['gold']);row['TF'][kind]=[dict(position=i+1,token=tail[i],**metrics(v[i],tail[i])) for i in range(n)]
  if 'U' in row:row['delta']=row['C']['gold']['logP']-row['U']['gold']['logP']
  results.append(row)
 write(out/(a.name+'-boundaries.json'),dict(name=a.name,format=a.format,checkpoint_sha256=sha(a.checkpoint),cases=results,forward_calls=calls[0],source_evaluation='Exposed TRAIN boundaries; not heldout generalization'))
 if a.boundaries_only:return
 oldeval=read(old/'evaluation/B-579.json');panels=read(old/'panels/B-579.json');cases=[]
 for c in oldeval['cases']+panels['legacy']:
  pref=cv(c['prefix']);limit=c['maxNewTokens'];assert len(pref)+limit<=256
  g=greedy(m,pref,pieces,max_new=limit);row=dict(id=c['id'],panel=c['panel'],prefix=pref,original_LF2_prefix=c['prefix'],prompt=c.get('prompt',c.get('prefix_text','')),requirement=c.get('requirement'),**g);cases.append(row);record(out/(a.name+'-progress.jsonl'),row)
 episodes=[]
 for c in panels['self_history']:
  ids=cv(c['prefix']);turns=[]
  for k in range(3):
   if len(ids)+24>256:turns.append(dict(unsupported_full_history=True));break
   g=greedy(m,ids,pieces,max_new=24);turns.append(dict(prefix=ids[:],**g));ids+=g['tokensIncludingEos']
   if not g['eos']:break
   if k<2:ids+=cv([3]+enc(c['followups'][k])+[2,4])
  episodes.append(dict(id=c['id'],turns=turns))
 counts={p:dict(n=sum(c['panel']==p for c in cases),EOS=sum(c['eos'] for c in cases if c['panel']==p),repeat4=sum(c['repeated4gram'] is not None for c in cases if c['panel']==p)) for p in sorted({c['panel'] for c in cases})}
 write(dest,dict(name=a.name,format=a.format,checkpoint_sha256=sha(a.checkpoint),cases=cases,self_history=episodes,counts=counts,forward_calls=calls[0],seconds=time.monotonic()-start,optimizer_calls=0,display_normalization='none; rawBytesHex retained',human_evaluation=False,semantic_scoring='Full-text assistant review separate; not inferred from automated counts'))
 print(json.dumps(dict(name=a.name,counts=counts,forward_calls=calls[0],seconds=time.monotonic()-start)),flush=True)
if __name__=='__main__':main()
