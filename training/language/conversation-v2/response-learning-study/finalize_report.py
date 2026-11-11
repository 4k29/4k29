"""Aggregate saved evidence only. No optimizer/model calls."""
import json,pathlib,hashlib,statistics,collections,os
P=pathlib.Path(__file__).resolve().parent;read=lambda f:json.loads((P/f).read_text());result=read('RESULT.json');extra=read('EXTRA_EVALUATION.json');rows=[json.loads(l)for l in (P/'UPDATES.jsonl').read_text().splitlines()if json.loads(l)['event']=='returned'];state=read('SOURCE_STATE.json');index=[]
for arm in ['A','B']:
 for n in [2,4]:
  m=read(f'artifacts/{arm}-PILOT{n}/checkpoint.json');cold=read(f'COLD-{arm}-{n}.json');index.append(dict(arm=arm,cursor=n,manifest=f'artifacts/{arm}-PILOT{n}/checkpoint.json',**{k:m[k]for k in ['sha256','bytes','integrity','Adam_steps']},cold_remote_commit=cold['source_commit'],cold_passed=cold['passed']))
(P/'CHECKPOINT_INDEX.json').write_text(json.dumps(dict(initial=state,checkpoints=index,public_adoption=False),indent=2)+'\n')
summary=dict(actual_optimizer_calls=result['actual_optimizer_returns'],retained_updates=result['retained'],discarded_original=result['discarded_original'],resume_replay=result['resume_replay'],main_updates=0,model_forward_returns=result['model_forward_returns']+extra['forward_returns'],pilot_forward_returns=result['model_forward_returns'],read_only_extra_forward_returns=extra['forward_returns'],saved_baseline_verdicts_reused=read('BASELINE_REUSE.json'),new_corpus_acquisition=0,initial_checkpoint_unchanged=True,main_learning_Go=False,formal_adoption_Go=False,pilot_execution_passed=True,independent_human_evaluation=False)
(P/'FINAL_STATUS.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
lines=['# 保存済み結果の比較','','本研究は4更新/条件の動作pilot。本格的なCE優劣・一般化の証拠ではない。','','| 指標 | 共通初期 MIX-579 | A 全CE・4更新 | B 返答CE・4更新 |','|---|---:|---:|---:|']
ns=[]
for n in ['initial','A-pilot4','B-pilot4']:
 x=read(f'evaluation/{n}.json');d={}
 for part in ['pilot_train','dev']:
  rs=[r for r in x['NLL']if r['partition']==part];d[part]=sum(r['body_sum']for r in rs)/sum(r['body_tokens']for r in rs)
 ns.append(d)
lines+=['| TRAIN16 返答本文NLL | '+' | '.join(f'{x["pilot_train"]:.6f}'for x in ns)+' |','| 固定DEV19 返答本文NLL | '+' | '.join(f'{x["dev"]:.6f}'for x in ns)+' |']
extra_nll=[sum(r['body_sum']for r in m['NLL'])/sum(r['body_tokens']for r in m['NLL'])for m in extra['models']];lines+=['| 追加DEV6 返答本文NLL | '+' | '.join(f'{x:.6f}'for x in extra_nll)+' |','| caption自然短文候補 | 21/32（PR108保存結果） | 22/32 | 21/32 |','| 直接質問DEV13 内容成功 | 0/13 | 0/13 | 0/13 |','| 追加人間DEV 内容成功 | 0/6 | 0/6 | 0/6 |','| assistant作成根拠参照DEV 内容成功 | 0/7 | 0/7 | 0/7 |','| 新段落 / 展開文章 | 0/5・0/45（保存結果） | 0/5・0/45 | 0/5・0/45 |','| 既存内容 / 資料 / 自己履歴 | 0/24・0/23・0/4（保存結果） | 0/24・0/23・0/4 | 0/24・0/23・0/4 |','','NLLは本文のみ・同じ参照位置でtoken加重。異なるloss対象のTRAIN loss同士は比較しない。直接質問13件以外のDEV6件は自由な会話継続を含み、客観的な内容必須課題と混同しない。captionはprefix込みの短文自然さで、画像との一致・新規段落成功ではない。','','| 学習実測 | A 全CE | B 返答CE |','|---|---:|---:|']
for title,fn in [('入力非PAD tokens',lambda z:sum(t['input_tokens']for t in z)),('有効教師 tokens',lambda z:sum(t['active_teachers']for t in z)),('勾配ノルム最小',lambda z:min(t['gradient_norm']for t in z)),('勾配ノルム最大',lambda z:max(t['gradient_norm']for t in z)),('clip回数',lambda z:sum(t['clipped']for t in z))]:
 values=[fn([r['trace']for r in rows if r['phase']=='pilot-retained'and r['arm']==a])for a in ['A','B']];lines.append('| '+title+' | '+' | '.join(f'{v:.6g}'for v in values)+' |')
lines+=['','両条件で16返答・252独立返答本文tokens、各4更新・一巡。全CEは本文717/EOS95/role95教師。返答CEは返答本文252/真EOS16教師。共通入力907に対し教師907対268。','','## 追加データ','','| 項目 | 結果 |','|---|---:|','| 新規読解TRAIN / DEV | 118 / 10 |','| 条件付き候補TRAIN / DEV | 66 / 6 |','| 保留TRAIN / DEV | 50 / 4 |','| 自然だが内容教師未承認TRAIN | 2 |','| 追加TRAIN返答本文tokens | 1,860 |','| 旧196件込み返答本文tokens | 4,590 |','| pilot16除外後の将来main候補 | 246件・4,338tokens |','| 候補TRAIN家族 / source内話者ID | 262 / 113 |','| 新規取得原文 | 0 |','','追加66件の重複カテゴリはA35/B38/C11/D1/E12/F64。Dの不足を「条件」という単語や好みの表明で水増ししない。追加DEV6にはB3/C1/F6、E手順・十分なD評価は未確保。7件の根拠参照問題はassistantによる別枠の質問で、人間執筆の条件付き対話資料の不足を埋めたとは扱わない。','','## 実行量','','optimizer実呼出し14＝保持8＋捨て4＋再開replay2。pilot forward14,712、追加評価567、計15,279。初回checkout失敗と停止制御helperはmodel/optimizerとも0。全4保存点でGit-only cold復元一致。pilot全体484.89秒（Git保存・復元・評価込み）、保持更新処理の合計はA1.904秒/B1.238秒で比較ベンチマークには不十分。追加評価10.83秒。','','## EOS / 反復proxy','','| panel | A EOS / n | B EOS / n | A repeat4gram / n | B repeat4gram / n |','|---|---:|---:|---:|---:|']
xs=[read(f'evaluation/{n}.json')for n in ['A-pilot4','B-pilot4']]
for pan in ['human-dev19','new-caption32','new_source_heldout_paragraph5','old24','oldNew9','new-MAFF12','native24','provided23']:
 zs=[[r for r in x['cases']if r['panel']==pan]for x in xs];n=len(zs[0]);values=[sum(r['eos']for r in z)for z in zs]+[sum(r['repeated4gram']is not None for r in z)for z in zs];lines.append('| '+pan+' | '+' | '.join(f'{v}/{n}'for v in values)+' |')
lines+=['','EOS tokenが出たこと、機械的4gram反復の有無は、意味の成立や適切な終了の判定と別。個別の判定・根拠はREADING.json、全生出力はevaluationとEXTRA_EVALUATIONに保存する。']
(P/'TABLES.md').write_text('\n'.join(lines)+'\n')
print(dict(optimizer_calls=14,forward_returns=summary['model_forward_returns'],checkpoints=len(index)))
