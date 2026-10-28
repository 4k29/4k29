"""Actual teacher vocabulary distribution and EOS position; counts are not semantic quality labels."""
import collections
from common import *
batches=json.load(gzip.open(P/'schedule.json.gz','rt'))['batches'];tok=read(V/'data/tokenizer.json');pieces=[bytes.fromhex(x)for x in tok['bytes']];counts=collections.Counter();eos=collections.Counter();by=collections.defaultdict(collections.Counter)
for b in batches:
 for w in b:
  counts.update(w['tokens'][1:]);by[w['source']].update(w['tokens'][1:])
  for j,t in enumerate(w['tokens'][1:]):
   if t==2:eos[str(j//32*32)]+=1
cat={k:set()for k in ['digits_only','contains_digit','whitespace','newline']}
for i,raw in enumerate(pieces):
 if i<6:continue
 try:s=raw.decode()
 except UnicodeDecodeError:continue
 if s and all(c in'0123456789'for c in s):cat['digits_only'].add(i)
 if any(c in'0123456789'for c in s):cat['contains_digit'].add(i)
 if s and s.isspace():cat['whitespace'].add(i)
 if '\n'in s:cat['newline'].add(i)
def summarize(c):
 n=sum(c.values());return dict(targets=n,EOS=c[2],BOS=c[1],PAD=c[0],roles=sum(c[i]for i in [3,4,5]),proxy_fractions={k:sum(c[i]for i in ids)/n for k,ids in cat.items()})
write(P/'TARGET_DISTRIBUTION.json',dict(all=summarize(counts),sources={s:summarize(c)for s,c in by.items()},EOS_position_bins32=dict(eos),top50=[dict(id=i,rawBytesHex=pieces[i].hex(),count=n)for i,n in counts.most_common(50)],scope='Spelling proxies overlap; not semantic genres; original unique target positions exactly once'))
print(summarize(counts))
