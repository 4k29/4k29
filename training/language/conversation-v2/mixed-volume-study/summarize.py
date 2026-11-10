"""Saved-result calculations only. No optimizer, model or data schedule changes."""
import json,pathlib,statistics,collections,csv,hashlib
P=pathlib.Path(__file__).resolve().parent;V=P.parent;B=V/'mixed-retention-study';load=lambda f:json.loads(f.read_text());mean=statistics.mean
names=['baseline-590k','midpoint-800k','terminal-1M'];paths={names[0]:B/'evaluation/terminal-MIX.json',**{n:P/'evaluation'/f'{n}.json' for n in names[1:]}};ev={n:load(f) for n,f in paths.items()};reading={names[0]:load(B/'evaluation/terminal-MIX-READING.json'),**{n:load(P/'evaluation'/f'{n}-READING.json') for n in names[1:]}}
basecap=load(B/'terminal-MIX-CAPTION_DECISIONS.json');capsets={names[0]:{k for k,v in basecap.items() if v['decision']=='natural_short_text_only'}}
for n in names[1:]:capsets[n]={k for k,v in load(P/f'{n}-CAPTION_DECISIONS.json').items() if v['decision']=='natural_short_text_only'}
ledger=[json.loads(l) for l in (P/'UPDATES.jsonl').read_text().splitlines()];done=[r for r in ledger if r['event']=='completed'];ret=[r['trace'] for r in done if r['phase']=='retained'];assert len(done)==405 and len(ret)==401
sources=collections.Counter();perstage={}
for stop,n in [(205,names[1]),(401,names[2])]:
 count=collections.Counter()
 for r in ret[:stop]:count.update(r['source_targets'])
 perstage[n]=dict(additional_targets=sum(count.values()),additional_source_targets=dict(count),cumulative_targets=590144+sum(count.values()),cumulative_source_targets={s:v+load(B/'SOURCE_AUDIT.json')['source_stats'][s]['targets'] for s,v in count.items()})
train=dict(actual_optimizer_calls=405,retained_additional_updates=401,discarded_original_updates=3,replay_validation_updates=1,replay_recovery_updates=0,additional_targets=sum(r['targets'] for r in ret),cumulative_targets=1000000,clipped_updates=sum(r['clipped'] for r in ret),gradient_norm_min=min(r['gradient_norm'] for r in ret),gradient_norm_max=max(r['gradient_norm'] for r in ret),gradient_norm_mean=mean(r['gradient_norm'] for r in ret),process_training_seconds=sum(load(P/f'TRAIN-{i}.json')['elapsed_process_seconds'] for i in [4,205,401]),peak_RSS_KiB=max(load(P/f'TRAIN-{i}.json')['max_RSS_KiB'] for i in [4,205,401]))
with (P/'LOSS_HISTORY.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=['step','additional_targets','cumulative_targets','loss','gradient_norm','clipped'],lineterminator='\n');w.writeheader();cum=0
 for r in ret:cum+=r['targets'];w.writerow(dict(step=r['step'],additional_targets=cum,cumulative_targets=590144+cum,loss=r['loss'],gradient_norm=r['gradient_norm'],clipped=r['clipped']))
pieces=[bytes.fromhex(x) for x in load(V/'data/tokenizer.json')['bytes']];word=lambda t:pieces[t].decode('utf8','backslashreplace') if t>5 else '<SPECIAL>'
exposure={r['id']:r for r in load(P/'BOUNDARY_EXPOSURE.json')['cases']};spaces={r['id']:r for r in load(P/'BASELINE_SPACE.json')['cases']};boundary={};detail=[]
for n in names:
 f=B/'evaluation/terminal-MIX-boundaries.json' if n==names[0] else P/'evaluation'/f'{n}-boundaries.json';cases=load(f)['cases'];groups={}
 for group,rows in [('all',cases)]+[(g,[r for r in cases if r['group']==g]) for g in sorted({r['group'] for r in cases})]+[(g,[r for r in cases if exposure[r['id']]['classification']==g]) for g in sorted({r['classification'] for r in exposure.values()})]:
  a=[r['C'] for r in rows];tf=[t for r in rows for t in r['TF']['C'][1:8] if t['token']>5 and t['token']!=16];sp=[spaces[r['id']]['P_space'] if n==names[0] else r['C']['P_space']['P'] for r in rows]
  groups[group]=dict(n=len(rows),LF_argmax=sum(r['argmax']==16 for r in a),space_argmax=sum(r['argmax']==38 for r in a),mata_argmax=sum(r['argmax']==3749 for r in a),nonwhitespace_ordinary_argmax=sum(r['argmax']>5 and bool(word(r['argmax']).strip()) for r in a),argmax_distribution=dict(collections.Counter(word(r['argmax']) for r in a)),mean_P_LF=mean(r['P_LF']['P'] for r in a),mean_P_mata=mean(r['P_mata']['P'] for r in a),mean_P_space=mean(sp),mean_P_gold=mean(r['gold']['P'] for r in a),mean_gold_rank=mean(r['gold']['rank'] for r in a),median_gold_rank=statistics.median(r['gold']['rank'] for r in a),gold_top1=sum(r['gold']['rank']==1 for r in a),mean_entropy=mean(r['entropy'] for r in a),TF_body_NLL_positions2_8=mean(-r['gold']['logP'] for r in tf))
 for r in cases:detail.append(dict(model=n,id=r['id'],exposure=exposure[r['id']],prediction=r['C'],P_space=spaces[r['id']]['P_space'] if n==names[0] else r['C']['P_space']['P'],TF_body_NLL_positions2_8=mean(-t['gold']['logP'] for t in r['TF']['C'][1:8] if t['token']>5 and t['token']!=16)))
 boundary[n]=groups
nll={n:load(P/'NLL'/f'{n}.json') for n in names};oldnll=load(B/'NLL/mixed.json')['groups'];baseerr=max(abs(oldnll[s]['NLL']-nll[names[0]]['groups'][s]['NLL']) for s in oldnll)
counts=dict(training=405,midpoint_boundary_pre_cache=72,midpoint_generation=ev[names[1]]['forward_calls'],terminal_generation_and_boundaries=ev[names[2]]['forward_calls'],source_NLL=sum(z['model_forwards'] for z in nll.values()),baseline_space=40,Python_parity=12);counts['total_Python_forward_calls']=sum(counts.values());counts['JS_score_queries']=24
results=dict(training=train,stages=perstage,NLL={n:dict(body=z['groups'],all_valid=z['all_valid_token_groups']) for n,z in nll.items()},baseline_body_NLL_max_difference_from_saved_PR108=baseerr,boundaries=boundary,semantics={n:{k:v for k,v in r.items() if k not in ['rows']} for n,r in reading.items()},caption_retention={n:dict(natural=len(capsets[n]),retained_from_baseline=len(capsets[n]&capsets[names[0]]),lost=sorted(capsets[names[0]]-capsets[n]),gained=sorted(capsets[n]-capsets[names[0]])) for n in names},panel_counts={n:z['counts'] for n,z in ev.items()},forward_counts=counts,formal_adoption='NO-GO',independent_native_human_evaluation=False,new_acquisition_tokens=0)
for name,obj in [('RESULTS.json',results),('BOUNDARY_COMPARISON.json',detail)]: (P/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
lines=['# 学習量比較：固定結果','', '露出済みDEV、メインassistant非盲検採点。独立母語話者評価・封印TESTではない。','', '|評価|PR108 590,144|累計800,000|累計1,000,000|','|---|---:|---:|---:|']
for title,key in [('caption自然短文 /32','caption_natural'),('うち語尾・供給済名詞補完中心','caption_ending_heavy'),('新段落 /5','new_paragraph_success'),('展開文章 /45','old_developed45_success'),('内容必須 /24','native24_strict'),('資料付き /23','provided23_strict'),('自己履歴 /4','self_history_strict')]:lines.append('|'+title+'|'+'|'.join(str(reading[n].get(key,0)) for n in names)+'|')
lines+=['','## captionの入力別保持','', '|状態|自然候補|初期21件の保持|失ったID|新たなID|','|---|---:|---:|---|---|']
for n,r in results['caption_retention'].items():lines.append(f"|{n}|{r['natural']}|{r['retained_from_baseline']}|{', '.join(r['lost']) or 'なし'}|{', '.join(r['gained']) or 'なし'}|")
lines+=['','## 本文NLL（特殊token・LFをmetricから除外）','', '|source|targets|590k|800k|1M|','|---|---:|---:|---:|---:|']
for src,r in nll[names[0]]['groups'].items():lines.append(f"|{src}|{r['targets']}|"+'|'.join(f"{nll[n]['groups'][src]['NLL']:.6f}" for n in names)+'|')
lines+=['','## 全有効教師NLL（LF/EOS/role等も含む、PAD除外）','', '|source|targets|590k|800k|1M|','|---|---:|---:|---:|---:|']
for src,r in nll[names[0]]['all_valid_token_groups'].items():lines.append(f"|{src}|{r['targets']}|"+'|'.join(f"{nll[n]['all_valid_token_groups'][src]['NLL']:.6f}" for n in names)+'|')
lines+=['','同一530窓。JAQUAD等は既知familyを分離した露出DEV、MAFFはsource-held-outの既視DEV。Wikivoyage293本文targetsは小標本。独立ENV DEV・Books/RP個別NLLは未測定。','', '## 40 TRAIN境界','', '|状態|LF argmax|空白 argmax|また argmax|非空白通常token|平均P(LF)|平均P(また)|平均P(空白)|正解top1|本文2–8 NLL|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for n in names:
 r=boundary[n]['all'];lines.append(f"|{n}|{r['LF_argmax']}|{r['space_argmax']}|{r['mata_argmax']}|{r['nonwhitespace_ordinary_argmax']}|{r['mean_P_LF']:.6f}|{r['mean_P_mata']:.6f}|{r['mean_P_space']:.6f}|{r['gold_top1']}|{r['TF_body_NLL_positions2_8']:.6f}|")
lines+=['','旧prefix露出15・追加予定内11・本系列未露出14。群別・実際の中間露出・全top10/確率/順位/entropyはBOUNDARY_COMPARISONとRESULTS。原文tokenは唯一の自然な続きではなく、TRAIN境界top1を一般化成功率とは扱わない。','', '## 終端EOS・反復proxy','', '|panel|件数|EOS|repeated4gram|','|---|---:|---:|---:|']
for panel,r in ev[names[2]]['counts'].items():lines.append(f"|{panel}|{r['n']}|{r['EOS']}|{r['repeat4']}|")
lines+=['','反復proxyと全文の有害反復は別。EOS発生と適切な終了も別。caption自然候補のEOS等はREADINGに個別保存。','', f"実optimizer405回＝保持401＋捨て3＋検証replay1。追加409,856、累計1Mtargets、切断に伴うreplay0。clip {train['clipped_updates']}/401、norm {train['gradient_norm_min']:.5f}–{train['gradient_norm_max']:.5f}。保持学習process合計{train['process_training_seconds']:.3f}秒、最大RSS{train['peak_RSS_KiB']:,}KiB。"]
(P/'TABLES.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'training':train,'forward':counts,'caption':results['caption_retention'],'boundary':{n:z['all'] for n,z in boundary.items()}},ensure_ascii=False,indent=2))
