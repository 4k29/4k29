"""Exact and lexical near-overlap screening against existing TRAIN references only."""
import pathlib,json,collections,re,hashlib,gzip,difflib,unicodedata,time,os
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path(os.environ.get('CE_V2_ROOT',str(P.parent)));rows=[r for r in json.loads((P/'PRIVATE/CANDIDATES.json').read_text())if r['mechanically_eligible']];canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split()).casefold();grams=lambda s:{s[i:i+5]for i in range(max(0,len(s)-4))};strings=[];inv=collections.defaultdict(list)
for r in rows:
 for part in ['question','answer']:
  s=canon(r[part]);i=len(strings);strings.append((r['id'],part,s,grams(s)))
  for g in grams(s):inv[g].append(i)
rare={g:ii for g,ii in inv.items()if len(ii)<=64};rarens=[sum(g in rare for g in x[3])for x in strings];seen=set();matches=[];counts=collections.Counter();inputsha={}
def check(text,source,id):
 s=canon(text);h=hashlib.sha256(s.encode()).hexdigest()
 if h in seen:return
 seen.add(h);counts[source+'_unique_units']+=1
 if len(s)<10:counts['short_units_not_near_compared']+=1;return
 if len(s)>4000:counts['long_units_not_near_compared']+=1;return
 cs=collections.Counter(i for g in grams(s)if g in rare for i in rare[g])
 for i,n in cs.items():
  if n<max(5,.6*rarens[i]):continue
  rid,part,a,gs=strings[i];ratio=difflib.SequenceMatcher(None,a,s,autojunk=False).ratio();contained=len(a)>=30 and a in s
  if a==s or ratio>=.85 or contained:matches.append(dict(new_id=rid,new_part=part,old_source=source,old_id=id,ratio=ratio,exact=a==s,contained=contained))
for rel in ['data/train.docs.jsonl','paragraph-foundation/corpus.jsonl.gz','modern-corpus/next-foundation/corpus.jsonl.gz','diverse-foundation/corpus.jsonl.gz']:
 p=V/rel;inputsha[rel]=hashlib.sha256(p.read_bytes()).hexdigest();f=gzip.open(p,'rt')if p.suffix=='.gz'else p.open()
 with f:
  for line in f:
   r=json.loads(line)
   if str(r.get('split',r.get('partition','train'))).lower()not in ['train','none']:counts['non_train_skipped']+=1;continue
   if 'utterances'in r:
    for u in r['utterances']:
     if isinstance(u,dict)and'text'in u:check(u['text'],r.get('source','RealPersona'),str(r['id'])+':'+str(u.get('ordinal','')))
   elif r.get('text'):check(r['text'],r.get('source','old_corpus'),r['id'])
out=dict(input_SHA256=inputsha,counts=dict(counts),matches=matches,method='NFKC/casefold/whitespace exact and shared-rare5gram candidate retrieval, SequenceMatcher>=0.85 or answer/prompt substring>=30chars',limitations='Approximate lexical screening, not complete semantic-family or author-independence proof. Short/very long units reported separately. Does not open sealed TEST.',optimizer_calls=0,model_forwards=0);(P/'OVERLAP_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print(dict(counts=out['counts'],matches=len(matches)));print(matches[:12])
