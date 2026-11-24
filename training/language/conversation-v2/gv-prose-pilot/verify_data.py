import pathlib,json,gzip,hashlib,sys
P=pathlib.Path(__file__).resolve().parent;V=P.parent;R=V.parents[2]
read=lambda p:json.loads(pathlib.Path(p).read_text())
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
sys.path.insert(0,str(V));from new_tokenizer import Encoder
p=read(P/'PLAN.json');assert sha(P/'PLAN.json')==(P/'PLAN.sha256').read_text().strip()
for f,h in p['sha256'].items():assert sha(R/f)==h,f
rows=[json.loads(s)for s in gzip.decompress((P/'corpus-C.jsonl.gz').read_bytes()).splitlines()];old=[json.loads(s)for f in [V/'novel-continuous-study/REVIEWED_PROSE.jsonl.gz',V/'staged-prose-study/ADDITIONAL_PROSE.jsonl.gz']for s in gzip.decompress(f.read_bytes()).splitlines()]
assert rows[:67]==old and len(rows)==71
tok=read(V/'data/tokenizer.json');enc=Encoder(tok);pieces=[bytes.fromhex(x)for x in tok['bytes']]
for r in rows:
 assert [1]+enc(r['text'])+([2]if r['EOS']else[])==r['tokens'];assert b''.join(pieces[k]for k in r['tokens']if k>=6)==r['text'].encode();assert not r['EOS']
bs=[json.loads(s)for s in gzip.decompress((V/'foundation-absorption-study/corpus.jsonl.gz').read_bytes()).splitlines()];ss=read(P/'SCHEDULE.json')
for arm,rs in [('B',bs),('C',rows)]:
 seen=set();tot=0
 for b in ss[arm]:
  for z in b:
   t=rs[z['record']]['tokens'];a=z['input_start'];e=z['end'];s=z['target_start'];assert 0<=a<s<e<=len(t)and e-a-1<=256;assert t[a:e-1][1:]==t[a+1:e][:-1]
   for k in range(s,e):q=(rs[z['record']]['id'],k);assert q not in seen;seen.add(q);tot+=1
 assert tot==13656 and len(ss[arm])==14
assert [[sum(z['targets']for z in b)for b in ss[k]]for k in ['B','C']]==[[1024]*13+[344]]*2
rv=read(P/'GV_REVIEW.json');assert len(rv['cases'])==90 and rv['new65_individually_read']and rv['provisional7_resolved'];assert sum(x['final_decision']=='admit_historical_report_LM'for x in rv['cases'])==4
oldrv=read(V/'staged-prose-study/GV_INTRO_READING.json')['cases']
for i in range(25):
 if i not in [4,5,6,7,11,19,24]:assert rv['cases'][i]['SHA']==oldrv[i]['SHA']and rv['cases'][i]['decision']==oldrv[i]['decision']
dev=read(P/'EVALUATION_INPUTS.json');assert len(dev['prose'])==18 and len(dev['caption'])==32;assert not {r['family']for r in rows}&{r['family']for r in dev['prose']}
print('PASS: fixed71 corpus/90 judgments/old67/3997 byteBPE/teacher shift/masks/13656x2/14x2/DEV family/PLAN hashes; model calls0')
