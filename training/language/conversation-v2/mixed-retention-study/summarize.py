"""Aggregate saved evidence only; no model construction, forward or optimization."""
import json,pathlib,statistics,collections,hashlib,math
P=pathlib.Path(__file__).resolve().parent;V=P.parent
load=lambda f:json.loads(f.read_text())
write=lambda f,x:f.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
mean=statistics.mean
pieces=[bytes.fromhex(x) for x in load(V/'data/tokenizer.json')['bytes']]
word=lambda t:pieces[t].decode('utf8','backslashreplace') if t>5 else f'<SPECIAL{t}>'
paths={'initial':V/'lf-boundary-study/evaluation/initial-LF1-boundaries.json','whitepaper':V/'lf-boundary-study/evaluation/terminal-LF1-boundaries.json','mixed_midpoint':P/'evaluation/midpoint-MIX-boundaries.json','mixed_terminal':P/'evaluation/terminal-MIX-boundaries.json'}
exposed={r['id']:r['gold_teacher_exposed_this_mixed_pass'] for r in load(P/'BOUNDARY_EXPOSURE.json')['cases']}
boundaries={};detail=[]
for name,path in paths.items():
 cases=load(path)['cases'];groups={}
 for group,rows in [('all',cases)]+[(g,[c for c in cases if c['group']==g]) for g in sorted({c['group'] for c in cases})]+[('mixed_exposed',[c for c in cases if exposed[c['id']]]),('mixed_not_exposed',[c for c in cases if not exposed[c['id']]])]:
  if not rows:continue
  pred=[c['C'] for c in rows];delta=[c['C']['gold']['logP']-c['U']['gold']['logP'] for c in rows if c.get('U')];tf=[r for c in rows for r in c['TF']['C'][1:8] if r['token']>5 and r['token']!=16]
  groups[group]=dict(n=len(rows),LF_argmax=sum(c['argmax']==16 for c in pred),nonwhitespace_ordinary_argmax=sum(c['argmax']>5 and bool(word(c['argmax']).strip()) for c in pred),mata_argmax=sum(c['argmax']==3749 for c in pred),argmax_distribution=dict(collections.Counter(word(c['argmax']) for c in pred)),mean_P_LF=mean(c['P_LF']['P'] for c in pred),mean_P_mata=mean(c['P_mata']['P'] for c in pred),mean_P_gold=mean(c['gold']['P'] for c in pred),gold_top1=sum(c['gold']['rank']==1 for c in pred),mean_gold_rank=mean(c['gold']['rank'] for c in pred),median_gold_rank=statistics.median(c['gold']['rank'] for c in pred),mean_entropy=mean(c['entropy'] for c in pred),TF_positions2_8_body_NLL=mean(-r['gold']['logP'] for r in tf),TF_positions2_8_body_targets=len(tf),context_delta_positive=sum(d>0 for d in delta),context_delta_mean=mean(delta) if delta else None,context_delta_n=len(delta))
 boundaries[name]=groups
 for c in cases:detail.append(dict(model=name,id=c['id'],group=c['group'],exposed_mixed=exposed[c['id']],argmax=word(c['C']['argmax']),**{k:c['C'][k] for k in ['P_LF','P_mata','gold','entropy','top10']},TF_body_NLL2_8=mean(-r['gold']['logP'] for r in c['TF']['C'][1:8] if r['token']>5 and r['token']!=16)))
ledger=[json.loads(l) for l in (P/'UPDATES.jsonl').read_text().splitlines()];done=[r for r in ledger if r['event']=='completed'];ret=[r['trace'] for r in done if r['phase']=='retained'];assert len(ret)==579
train=dict(actual_optimizer_calls=len(done),retained_updates=len(ret),discarded_original_updates=sum(r['phase']=='preflight-original' for r in done),replay_updates=sum(r['phase']=='preflight-replay' for r in done),retained_targets=sum(r['targets'] for r in ret),clipped_updates=sum(r['clipped'] for r in ret),gradient_norm_min=min(r['gradient_norm'] for r in ret),gradient_norm_max=max(r['gradient_norm'] for r in ret),gradient_norm_mean=mean(r['gradient_norm'] for r in ret),initial_50_target_weighted_loss=sum(r['loss']*r['targets'] for r in ret[:50])/sum(r['targets'] for r in ret[:50]),final_50_target_weighted_loss=sum(r['loss']*r['targets'] for r in ret[-50:])/sum(r['targets'] for r in ret[-50:]),elapsed_train_process_seconds=sum(load(P/f'TRAIN-{n}.json')['elapsed_process_seconds'] for n in [4,289,579]),peak_process_RSS_KiB=max(load(P/f'TRAIN-{n}.json')['max_RSS_KiB'] for n in [4,289,579]))
forwards={'training':len(done),'freegen_and_boundary_midpoint':load(P/'evaluation/midpoint-MIX.json')['forward_calls'],'freegen_and_boundary_terminal':load(P/'evaluation/terminal-MIX.json')['forward_calls'],'source_NLL':sum(load(P/f'NLL/{n}.json')['model_forwards'] for n in ['initial','whitepaper','mixed']),'parity_Python':12}
forwards['total_Python_forward_calls']=sum(forwards.values());forwards['JS_score_queries']=24
result=dict(training=train,forward_counts=forwards,boundaries=boundaries,NLL={n:load(P/f'NLL/{n}.json')['groups'] for n in ['initial','whitepaper','mixed']},semantic={n:{k:v for k,v in load(P/'evaluation'/f'{n}-READING.json').items() if k not in ['rows']} for n in ['midpoint-MIX','terminal-MIX']},panel_counts={n:load(P/'evaluation'/f'{n}.json')['counts'] for n in ['midpoint-MIX','terminal-MIX']},new_acquisition_tokens=0,formal_adoption='NO-GO',independent_native_human_evaluation=False)
write(P/'RESULTS.json',result);write(P/'BOUNDARY_COMPARISON.json',detail)
lines=['# 比較表','', 'すべて露出済みの研究用診断。意味判定はメインassistantの非盲検読解であり、独立人間評価ではない。','', '## 自由生成','', '|条件|caption自然短文 /32|うち語尾・供給済名詞補完中心|新段落 /5|展開文章 /45|内容応答 /24|資料付き /23|自己履歴 /4|','|---|---:|---:|---:|---:|---:|---:|---:|','|共通初期|21|4|0|0|0|0|0|','|白書単独LF1|2|0|0|0|0|0|0|']
for n,label in [('midpoint-MIX','混合289'),('terminal-MIX','混合579（固定終端）')]:
 r=result['semantic'][n];lines.append(f"|{label}|{r['caption_natural']}|{r['caption_ending_heavy']}|0|0|0|0|0|")
lines+=['','captionはprefix付き短文補完。BOSだけからの生成・画像真偽・段落能力とは異なる。終端の保留5件は不合格扱い。中間23件を選んで採用することはしない。','', '## source別本文NLL','', '|source|本文targets|共通初期|白書単独|混合579|','|---|---:|---:|---:|---:|']
for src,r in result['NLL']['initial'].items():lines.append(f"|{src}|{r['targets']}|{r['NLL']:.6f}|{result['NLL']['whitepaper'][src]['NLL']:.6f}|{result['NLL']['mixed'][src]['NLL']:.6f}|")
lines+=['','同一530窓、53,847本文targets。ID>5かつLF以外のみ集計。Wikivoyage293targetsは小標本。独立ENV DEV、Books/RP個別NLLは未測定。ENVは下のTRAIN境界診断と区別。','', '## 固定40境界：正しいLF1履歴','', '|条件|LF argmax|非空白通常token argmax|また argmax|平均P(LF)|平均P(また)|正解top1|平均entropy|本文2–8 NLL|','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
for n,groups in boundaries.items():
 r=groups['all'];lines.append(f"|{n}|{r['LF_argmax']}|{r['nonwhitespace_ordinary_argmax']}|{r['mata_argmax']}|{r['mean_P_LF']:.6f}|{r['mean_P_mata']:.6f}|{r['gold_top1']}|{r['mean_entropy']:.6f}|{r['TF_positions2_8_body_NLL']:.6f}|")
lines+=['','16また・16その他・過去失敗8という選択標本。原文分布の代表ではない。白書対照40/40、混合15/40の正解教師だけが今回露出している。各群・露出別の数値はRESULTS.json。空白を本文意味成立と数えない。','', '## 40件の終端比較','', '|ID|群|混合で教師露出|白書argmax|混合argmax|白書P(LF)|混合P(LF)|白書P(また)|混合P(また)|白書正解順位|混合正解順位|','|---|---|---|---|---|---:|---:|---:|---:|---:|---:|']
a={r['id']:r for r in detail if r['model']=='whitepaper'}
for r in [r for r in detail if r['model']=='mixed_terminal']:
 q=a[r['id']];esc=lambda s:s.replace('|','\\|').replace('\n','LF') if s.strip() else 'SPACE';lines.append(f"|{r['id']}|{r['group']}|{r['exposed_mixed']}|{esc(q['argmax'])}|{esc(r['argmax'])}|{q['P_LF']['P']:.6f}|{r['P_LF']['P']:.6f}|{q['P_mata']['P']:.6f}|{r['P_mata']['P']:.6f}|{q['gold']['rank']}|{r['gold']['rank']}|")
lines+=['','全top10・確率・順位・entropy・TF各位置はBOUNDARY_COMPARISON.jsonとevaluation/*-boundaries.json。argmaxが本文でも意味理解成功とはしない。','', '## EOSと反復proxy（終端）','', '|panel|件数|EOS|反復4gram proxy|','|---|---:|---:|---:|']
for panel,r in result['panel_counts']['terminal-MIX'].items():lines.append(f"|{panel}|{r['n']}|{r['EOS']}|{r['repeat4']}|")
lines+=['','EOS出現は適切な終了を保証しない。反復4gramは機械proxyであり、人間の有害反復判定と同一ではない。','', '## 更新・資源','',f"保持579更新、590,144targets。optimizer実呼出し{len(done)}回（破棄original3、replay1）。clip {train['clipped_updates']}/579、norm {train['gradient_norm_min']:.4f}〜{train['gradient_norm_max']:.4f}。学習プロセス合計{train['elapsed_train_process_seconds']:.3f}秒、最大RSS {train['peak_process_RSS_KiB']:,}KiB。"]
(P/'TABLES.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'training':train,'forwards':forwards,'boundaries':{n:z['all'] for n,z in boundaries.items()}},ensure_ascii=False,indent=2))

# Loss series derives from the same completed retained ledger, LF CSV for review.
import csv
with (P/"LOSS_HISTORY.csv").open("w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=["step","cumulative_targets","targets","loss","gradient_norm","clipped","lr"],lineterminator="\n");w.writeheader();cumulative=0
 for r in ret:
  cumulative+=r["targets"];w.writerow(dict(**{k:r[k] for k in ["step","targets","loss","gradient_norm","clipped","lr"]},cumulative_targets=cumulative))
