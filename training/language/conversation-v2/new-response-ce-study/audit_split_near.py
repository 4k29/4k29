"""Cross-split lexical near-response screen, without moving any frozen family."""
import pathlib,json,collections,difflib,unicodedata
P=pathlib.Path(__file__).resolve().parent;rs=[r for r in json.loads((P/'PRIVATE/CANDIDATES.json').read_text())if r['mechanically_eligible']];canon=lambda s:''.join(unicodedata.normalize('NFKC',s).split()).casefold();texts=[canon(r['answer'])for r in rs];gs=[{s[i:i+5]for i in range(max(0,len(s)-4))}for s in texts];inv=collections.defaultdict(list)
for i,g in enumerate(gs):
 for k in g:inv[k].append(i)
hits=[];done=set()
for i,g in enumerate(gs):
 cs=collections.Counter(j for k in g if len(inv[k])<=64 for j in inv[k]if j<i and rs[j]['partition']!=rs[i]['partition'])
 for j,n in cs.items():
  if n<5 or len(gs[i]&gs[j])/max(1,len(gs[i]|gs[j]))<.5:continue
  ratio=difflib.SequenceMatcher(None,texts[i],texts[j],autojunk=False).ratio()
  if ratio>=.85:hits.append(dict(first_id=rs[j]['id'],second_id=rs[i]['id'],first_family=rs[j]['family'],second_family=rs[i]['family'],ratio=ratio,action='hold both families from future training; frozen partitions not rewritten'))
held={v for h in hits for k,v in h.items()if k in ['first_family','second_family']};out=dict(threshold=.85,cross_split_near_response_pairs=hits,held_families=sorted(held),family_partition_changed=False,training_started=False,method='NFKC/no-whitespace/casefold, rare5gram retrieval, gram Jaccard>=0.5, SequenceMatcher>=0.85; incomplete semantic screening',reviewed_overlap_ids=[r['id']for r in json.loads((P/'PRIVATE/REVIEW_CARDS.json').read_text())if r['family']in held]);(P/'SPLIT_NEAR_AUDIT.json').write_text(json.dumps(out,indent=2)+'\n');print('cross split near pairs',len(hits),'heldfamilies',len(held),'reviewed',out['reviewed_overlap_ids'])
