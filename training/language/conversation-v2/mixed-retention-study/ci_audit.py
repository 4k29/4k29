"""No torch, weights or original large corpus required: verify frozen LF1 artifacts."""
import gzip,json,hashlib,pathlib
P=pathlib.Path(__file__).resolve().parent;root=P.parents[3];plan=json.loads((P/'PLAN.json').read_text());prefix=str(P.relative_to(root))+'/'
for n,h in plan['sha256'].items():
 if n.startswith(prefix):assert hashlib.sha256((root/n).read_bytes()).hexdigest()==h,n
c=json.load(gzip.open(P/'corpus.json.gz','rt'));s=json.load(gzip.open(P/'schedule.json.gz','rt'));maps=json.load(gzip.open(P/'POSITION_MAP.json.gz','rt'));assert len(s)==579 and len(c)==8037
seen=set();tot=lf=eos=0
for b in s:
 for r in b:
  t=c[r['record']]['tokens'][r['start']:r['start']+r['length']];assert len(t)==r['length'] and 2<=len(t)<=257
  for j,v in enumerate(t[1:],r['start']+1):
   k=(r['record'],j);assert k not in seen;seen.add(k);tot+=1;lf+=v==16;eos+=v==2
assert (tot,lf,eos)==(590144,1818,10561)
print('Frozen multi-genre artifact SHA, unique targets and counts: PASS')
