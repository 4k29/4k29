"""Fix a matched allocation experiment after limited source review, before any update."""
import collections,gzip,hashlib,re
import numpy as np
from common import *
from prepare import rank

def main():
 d=json.loads((N/'paragraph-filtered.json').read_text());vs=json.loads((N/'paragraph-validation.json').read_text());held={vs[i]['id']:reason for i,reason in {1:'unverified current route/travel times',3:'chemical process omits oxidative stabilization',4:'unbound そういう needles and overstated impossibility',5:'unverified world-oldest-flower claim',6:'unverified crime advice',7:'awkward translated language paragraph',9:'ambiguous JR東武 station and unverified local details',10:'all cells have nucleus false generalization',13:'unverified current transport exclusivity',14:'refers to earlier examples and 下の発展',15:'overstated game optimality'}.items()};report=json.loads((N/'PARAGRAPH_REVIEW.json').read_text());report.update(validation_count=16,validation_all_read=True,validation_held=held,bounded_exploratory_admission=True,not_exhaustive_fact_or_human_authorship_certification=True);write(N/'PARAGRAPH_REVIEW.json',report)
 for split in d:
  d[split]=[r for r in d[split]if r['id']not in held and r['component']!='jawikibooks|囲碁'and not re.search(r'下の|上の表|前述|参照|既に|犯罪組織|ヤミ金融',r['text'])]
 pool=[];counts=collections.Counter()
 for r in sorted(d['train'],key=lambda r:rank('use|'+r['id'])):
  cap=64 if r['source']=='jawikibooks'else 4
  if counts[r['component']]>=cap:continue
  pool.append(r);counts[r['component']]+=1
 U=512;assert len(pool)>=2*U,(len(pool),2*U);shorts=pool[:2*U];pure=json.load(gzip.open(H/'schedule.json.gz','rt'));units={r['id']:r for r in map(json.loads,gzip.open(H/'data.jsonl.gz','rt'))};longs=sorted([w for b in pure['batches']for w in b if units[w['unit_id']]['source']=='jaquad'and len(w['tokens'])>=243],key=lambda w:rank(w['id']));assert len(longs)>=3*U,len(longs)
 meta=json.loads((V/'data/data.json').read_text());values=np.fromfile(N.parents[3]/meta['trainTokensPath'],dtype='<u4');rp=sorted([(i,w)for i,w in enumerate(meta['trainWindows'])if w['length']==257],key=lambda z:rank('RP|'+str(z[0])));assert len(rp)>=U
 A=[];B=[];selected=[];ptr=0
 for i in range(U):
  shared=dict(longs[ptr]);ptr+=1;shared['tokens']=shared['tokens'][:243];idx,w=rp[i];dialogue=dict(id='rp:'+str(idx),source_kind='original_human_A_B',tokens=values[w['offset']:w['offset']+257].tolist(),rp_window=idx,rp_offset=w['offset'],document=w['document']);a=[shared];b=[shared]
  for r in shorts[2*i:2*i+2]:
   seq=r['tokens'];control=dict(longs[ptr]);ptr+=1;assert len(control['tokens'])>=len(seq);control['tokens']=control['tokens'][:len(seq)];a.append(control);b.append(dict(id=r['id'],tokens=seq,paragraph_id=r['id'],source_unit=r['source_unit']));selected.append(r)
  a.append(dialogue);b.append(dialogue);assert [len(x['tokens'])for x in a]==[len(x['tokens'])for x in b];A.append(a);B.append(b)
 targets=sum(len(w['tokens'])-1 for b in A for w in b);assert targets==sum(len(w['tokens'])-1 for b in B for w in b)
 def dump(path,obj):
  with path.open('wb')as f:
   with gzip.GzipFile(fileobj=f,mode='wb',mtime=0)as z:z.write(json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode())
 dump(N/'schedule.json.gz',dict(control=A,boundary=B));write(N/'paragraphs.json',dict(train=selected,dev=d['dev']));enc=Encoder(json.loads((V/'data/tokenizer.json').read_text()));pieces=[bytes.fromhex(b)for b in json.loads((V/'data/tokenizer.json').read_text())['bytes']];dev=[]
 for r in d['dev']:
  ids=r['body_tokens'];pos=max(1,len(ids)//3)
  while pos<len(ids):
   try:pre=b''.join(pieces[t]for t in ids[:pos]).decode();break
   except UnicodeDecodeError:pos+=1
  assert len(ids)-pos>10 and 1+pos+128<=256
  dev.append(dict(id=r['id'],component=r['component'],prefix=[1]+ids[:pos],prefix_text=pre,reference_tokens=ids[pos:]+[2],source_text=r['text'],max_new=128))
 write(N/'paragraph-dev.json',dict(cases=dev,scope='Three original held DEV components already exposed in PR101; new standalone paragraph framing, not independent TEST or human evaluation'))
 def stats(batches):
  flat=[w for b in batches for w in b];c=collections.Counter(t for w in flat for t in w['tokens'][1:]);return dict(targets=sum(c.values()),EOS=c[2],BOS=c[1],role=c[3]+c[4],body=sum(n for t,n in c.items()if t>=6),EOS_at_window_end=sum(w['tokens'][-1]==2 for w in flat))
 audit=dict(updates_each=U,targets_each=targets,control=stats(A),boundary=stats(B),short_paragraphs=len(selected),short_unique_original_body_tokens=sum(len(r['body_tokens'])for r in selected),short_components=len({r['component']for r in selected}),short_source_body_tokens={s:sum(len(r['body_tokens'])for r in selected if r['source']==s)for s in ['jawikibooks','jawikivoyage']},short_max_paragraphs_one_component=max(collections.Counter(r['component']for r in selected).values()),RP_shared_windows=U,RP_shared_conversations=len({b[-1]['document']for b in A}),no_QA_or_synthetic_gold=True,no_new_original_corpus_acquisition=True,originals_previously_in_PR101_subset=True,JaQuAD_new_EOS=0,short_source_ordinal_and_whole_text_verified=True,data_factor='Two JaQuAD cut windows replaced by two complete source-native paragraphs; shared JaQuAD and humanA/B dialogue windows unchanged. EOS, BOS, genre change with allocation, not a pure EOS causal test.',prefix_split_change='New BOS/EOS denote a standalone full paragraph task, not claimed original page boundaries; original PR101 results retained',no_known_component_cross_split=not({r['component']for r in selected}&{r['component']for r in d['dev']}),schedule_sha256=sha(N/'schedule.json.gz'),paragraphs_sha256=sha(N/'paragraphs.json'));write(N/'DATA_AUDIT.json',audit);print(audit)
if __name__=='__main__':main()
