import pathlib,json,statistics,collections,hashlib
P=pathlib.Path(__file__).resolve().parent;V=P.parent
read=lambda p:json.loads(pathlib.Path(p).read_text())
write=lambda f,d:(P/f).write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
names=['initial','B-mid','B-terminal','C-mid','C-terminal'];ds={n:read(P/'evaluation'/f'{n}.json')for n in names}
summary={}
for name,d in ds.items():
 g=collections.defaultdict(lambda:[0.,0]);detail={}
 for r in d['NLL']:
  g[r['panel']][0]+=r['body_sum'];g[r['panel']][1]+=r['body_tokens'];detail[r['id']]=r['body_sum']/r['body_tokens']
 summary[name]=dict(body_NLL={k:dict(NLL=a/b,teachers=b)for k,(a,b)in g.items()},row_NLL=detail)
 if d['cases']:
  rs=[r for r in d['cases']if r['panel']!='new-caption32'];by=collections.defaultdict(list)
  for r in rs:by[r['panel']].append(r)
  summary[name]['prose_automatic']={k:dict(n=len(rs),EOS=sum(r['eos']for r in rs),empty=sum(not r['nonEosTokens']for r in rs),repeated4gram_proxy=sum(bool(r['repeated4gram'])for r in rs),first_token_LF=sum(bool(r['tokensIncludingEos'])and r['tokensIncludingEos'][0]==16 for r in rs),generic_starts_aggregation_only=dict(collections.Counter((r['text']or'').lstrip('\n ').split('、')[0][:6]for r in rs)))for k,rs in by.items()}
u=[json.loads(l)for l in(P/'UPDATES.jsonl').read_text().splitlines()];ret=[r for r in u if r['event']=='returned'and r['phase']=='retained'];train={}
for arm in ['B','C']:
 rr=[r['trace']for r in ret if r['condition']==arm];train[arm]=dict(kept=len(rr),teachers=sum(r['active_teachers']for r in rr),loss_first=rr[0]['loss'],loss_last=rr[-1]['loss'],loss_mean=statistics.mean(r['loss']for r in rr),gradient_min=min(r['gradient_norm']for r in rr),gradient_median=statistics.median(r['gradient_norm']for r in rr),gradient_max=max(r['gradient_norm']for r in rr),clipped=sum(r['clipped']for r in rr),Adam_first=rr[0]['Adam_step'],Adam_last=rr[-1]['Adam_step'],weight_update_deltas=[dict(step=r['step'],L2=r['weight_delta_L2'])for r in rr if r['weight_delta_L2']is not None])
write('NUMERIC_SUMMARY.json',dict(evaluation=summary,training=train,not_semantic_scores=True,retained_only_training_stats=True))
print(json.dumps(dict(evaluation={k:{a:b for a,b in v.items()if a!='row_NLL'}for k,v in summary.items()},training=train),ensure_ascii=False,indent=2))
