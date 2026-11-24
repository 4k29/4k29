"""Post-run descriptive tables; no inference, checkpoint selection or gate changes."""
import pathlib,json,statistics,collections,hashlib
P=pathlib.Path(__file__).resolve().parent;V=P.parent
read=lambda p:json.loads(p.read_text())
pieces=[bytes.fromhex(x) for x in read(V/'data/tokenizer.json')['bytes']]
names=['initial-LF1','control-LF2','midpoint-LF1','terminal-LF1'];runs={n:read(P/'evaluation'/(n+'-boundaries.json')) for n in names}
labels=read(V/'paragraph-foundation/paragraph-context-use/AUXILIARY_TOKEN_REVIEW.json')['specific_content_positions']
allstats={}
def stats(cs):
 body=lambda c:c['C']['argmax']>5 and not pieces[c['C']['argmax']].isspace()
 ds=[c['delta'] for c in cs if 'delta' in c]
 tf=[v for c in cs for v in c['TF']['C'][1:] if v['token']>5 and v['token']!=16]
 cu=[(c['TF']['C'][i],c['TF']['U'][i]) for c in cs if 'U' in c['TF'] for i in range(1,8)]
 spec=[(c['TF']['C'][i],c['TF']['U'][i]) for c in cs if c['id'].startswith('new32-') for i in labels.get(c['id'].split('-')[-1],[])]
 d2=[c['gold']['logP']-u['gold']['logP'] for c,u in cu];sp=[c['gold']['logP']-u['gold']['logP'] for c,u in spec]
 return dict(n=len(cs),LF_argmax=sum(c['C']['argmax']==16 for c in cs),nonLF_ordinary_argmax=sum(c['C']['body_argmax'] for c in cs),nonwhitespace_ordinary_argmax=sum(body(c) for c in cs),mata_argmax=sum(c['C']['argmax']==3749 for c in cs),gold_argmax=sum(c['C']['gold']['rank']==1 for c in cs),P_LF=statistics.mean(c['C']['P_LF']['P'] for c in cs),P_gold=statistics.mean(c['C']['gold']['P'] for c in cs),P_mata=statistics.mean(c['C']['P_mata']['P'] for c in cs),gold_rank_mean=statistics.mean(c['C']['gold']['rank'] for c in cs),entropy_mean=statistics.mean(c['C']['entropy'] for c in cs),body_NLL_2_to_8=statistics.mean(-z['gold']['logP'] for z in tf),context_first_delta_positive=sum(d>0 for d in ds),context_first_delta_mean=statistics.mean(ds) if ds else None,context_body_delta_2_to_8_mean=statistics.mean(d2) if d2 else None,specific_content_BPE_delta_mean=statistics.mean(sp) if sp else None,specific_content_BPE_NLL=statistics.mean(-c['gold']['logP'] for c,u in spec) if spec else None)
for n,x in runs.items():allstats[n]={g:stats([c for c in x['cases'] if g=='all40' or c['group']==g]) for g in ['all40','mata','other','old8']}
lines=['# LF2/LF1境界学習比較','', '同じ原文、各モデルの学習表現で比較。境界・位置・dropout消費・正規化の差を含む。non-LF通常tokenと空白以外の通常tokenは別指標で、いずれも自然な意味成立率ではない。','', '|状態|LFが1位 /40|空白以外の通常tokenが1位 /40|またが1位 /40|原文正解が1位 /40|平均P(LF)|平均P(g)|本文2–8位置NLL|','|---|---:|---:|---:|---:|---:|---:|---:|']
for n in names:
 z=allstats[n]['all40'];lines.append(f"|{n}|{z['LF_argmax']}|{z['nonwhitespace_ordinary_argmax']}|{z['mata_argmax']}|{z['gold_argmax']}|{z['P_LF']:.6f}|{z['P_gold']:.6f}|{z['body_NLL_2_to_8']:.6f}|")
lines+=['','## 群別','', '|状態|群|n|LF 1位|本文候補 1位|正解 1位|P(LF)|P(また)|正解順位平均|H|C−U logP(g)平均|','|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for n in names:
 for g in ['mata','other','old8']:
  z=allstats[n][g];d=z['context_first_delta_mean'];lines.append(f"|{n}|{g}|{z['n']}|{z['LF_argmax']}|{z['nonwhitespace_ordinary_argmax']}|{z['gold_argmax']}|{z['P_LF']:.5f}|{z['P_mata']:.5f}|{z['gold_rank_mean']:.2f}|{z['entropy_mean']:.4f}|{d if d is not None else '—'}|")
lines+=['','## 固定40境界：Cの個別比較','', '|ID|g|LF2対照 P(LF)/P(g)/順位|LF1中間 P(LF)/P(g)/順位|LF1終端 P(LF)/P(g)/順位|LF1終端argmax|','|---|---:|---|---|---|---|']
for i,c in enumerate(runs['control-LF2']['cases']):
 vals=[]
 for n in ['control-LF2','midpoint-LF1','terminal-LF1']:
  z=runs[n]['cases'][i];assert z['id']==c['id'] and z['gold']==c['gold'];vals.append(f"{z['C']['P_LF']['P']:.5f}/{z['C']['gold']['P']:.5f}/{z['C']['gold']['rank']}")
 z=runs['terminal-LF1']['cases'][i];piece=pieces[z['C']['argmax']].decode('utf8','backslashreplace').replace('\n','LF').replace(' ','SPACE');lines.append('|'+ '|'.join([c['id'],str(c['gold'])]+vals+[piece])+'|')
lines+=['','32件はまた16／その他16の均等抽出、旧8件は失敗例由来。学習分布全体の代表値ではない。C/U比較は同じ参照tokenの予測差であり、意味理解の成功率ではない。内容語20片は5例に依存する事前指定BPE片であり、独立した20語ではない。','', '全ケースの上位10候補、位置別TF、入力・正解tokensはevaluation/*-boundaries.jsonを参照。']
(P/'TABLES.md').write_text('\n'.join(lines)+'\n');(P/'BOUNDARY_SUMMARY.json').write_text(json.dumps(allstats,ensure_ascii=False,indent=2)+'\n')
es=[json.loads(l) for l in (P/'UPDATES.jsonl').read_text().splitlines()];intent=[(e['phase'],e['trace']['step']) for e in es if e['event']=='intent'];done=[(e['phase'],e['trace']['step']) for e in es if e['event']=='completed'];assert intent==done
ret=[e['trace'] for e in es if e['event']=='completed' and e['phase']=='retained'];assert [r['step'] for r in ret]==list(range(1,580));assert sum(r['targets'] for r in ret)==590144
summary=dict(retained_updates=len(ret),retained_targets=sum(r['targets'] for r in ret),actual_optimizer_calls=len(done),calls_by_phase=dict(collections.Counter(e['phase'] for e in es if e['event']=='completed')),failed_or_uncertain_optimizer_calls=0,gradient_norm_min=min(r['gradient_norm'] for r in ret),gradient_norm_max=max(r['gradient_norm'] for r in ret),clipped_updates=sum(r['clipped'] for r in ret),weighted_train_loss=sum(r['loss']*r['targets'] for r in ret)/sum(r['targets'] for r in ret),inherited_model_counter=12820,terminal_model_counter=13399,initial_Adam_step=6361,terminal_Adam_step=6940)
(P/'TRAIN_SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
