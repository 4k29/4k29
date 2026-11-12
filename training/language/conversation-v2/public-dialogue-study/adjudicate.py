"""Materialize main-agent nonblind readings, not an automatic success classifier."""
import pathlib,json,hashlib,collections,statistics
P=pathlib.Path(__file__).resolve().parent;read=lambda n:json.loads(((P/n)if (P/n).exists()else P.parent/'mixed-retention-study/evaluation'/n.replace('BASELINE-','')).read_text());write=lambda n,x:(P/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
base={(r['panel'],r['id']):r for r in read('BASELINE-terminal-MIX.json')['cases']};prior={(r['panel'],r['id']):r for r in read('BASELINE-terminal-MIX-READING.json')['rows']};dev={r['id']:r for r in read('DEV_PROTOCOL.json')['cases']}
# Main agent read all new DEV, all32 caption outputs each arm, self turns; old changed outputs with exact-repeat display compression. Identical old outputs retain prior verdicts.
scopes=['initial','A-pilot17','B-pilot17'];summary={}
for name in scopes:
 data=read('evaluation/'+name+'.json');rows=[]
 for r in data['cases']:
  key=(r['panel'],r['id']);caption=r['panel']=='new-caption32';isdev=r['id']in dev;identical=key in base and r['tokensIncludingEos']==base[key]['tokensIncludingEos'];ok=caption and prior[key]['caption_natural']
  if isdev:
   reason='必要条件: '+dev[r['id']]['required']+' 判定: 出力は相槌のみ、無関係な話題・問い返し、誤った自己属性、または語句反復・崩れであり、この条件を満たす具体応答はない。'
  elif caption:
   reason=('入力対象を保持する自然な短文補完。画像の事実確認や未知段落能力の証拠ではない。'if ok else prior[key]['reason'])
  else:
   reason='既知の同一入力に対するbyte同一の保存済み不合格判定を再利用。'if identical else'変更された全文を読解（厳密な同一反復は表示のみ圧縮）。無関係な内容、疑似語、数値・語句反復、必要な回答の欠落があり、入力に沿う意味のつながった文章ではない。'
  rows.append(dict(id=r['id'],panel=r['panel'],caption_natural=bool(ok),ending_only_or_supplied_noun_completion=bool(caption and prior[key]['ending_only_or_supplied_noun_completion']),condition_or_content_success=False,coherent_two_or_three_sentences=False,EOS_token=r['eos'],appropriate_EOS=bool(caption and ok and r['eos']),repeat4gram_proxy=bool(r['repeated4gram']),generic_ack_only=(r.get('text')or'').strip()in['そうなんですね。','そうですね。','はい。'],reason=reason,prior_verdict_reused_byte_identical=bool(identical),judgment='main assistant, nonblind, no independent human evaluation'))
 nll={}
 for part in ['pilot_train','dev']:
  z=[x for x in data['NLL']if x['partition']==part];nll[part]=dict(body_NLL=sum(x['body_sum']for x in z)/sum(x['body_tokens']for x in z),body_tokens=sum(x['body_tokens']for x in z),with_EOS_NLL=sum(x['with_EOS_sum']for x in z)/sum(x['with_EOS_tokens']for x in z))
 counts={}
 for panel in sorted({r['panel']for r in rows}):
  z=[x for x in rows if x['panel']==panel];counts[panel]=dict(n=len(z),content_success=0,caption_natural=sum(x['caption_natural']for x in z),EOS=sum(x['EOS_token']for x in z),appropriate_EOS=sum(x['appropriate_EOS']for x in z),repeat4gram_proxy=sum(x['repeat4gram_proxy']for x in z),ack_only=sum(x['generic_ack_only']for x in z))
 obj=dict(name=name,source_sha256=sha(P/'evaluation'/f'{name}.json'),method='Main assistant full raw new DEV and caption; changed legacy lossless-repeat reading view; identical old token sequences reuse prior saved judgment; no independent blind human evaluation',rows=rows,self_history=[dict(id=e['id'],success=False,reason='自己生成履歴でも無関係な内容・疑似語・反復が残る。EOSなしの途中停止と3ターン成立は区別する。')for e in data['self_history']],counts=counts,NLL=nll)
 write('evaluation/'+name+'-READING.json',obj);summary[name]=dict(counts=counts,NLL=nll,self_success=0)
# NLL only at midpoint; no posthoc semantic checkpoint selection.
for name in ['A-pilot9','B-pilot9']:
 data=read('evaluation/'+name+'.json');summary[name]=dict(NLL={p:sum(x['body_sum']for x in data['NLL']if x['partition']==p)/sum(x['body_tokens']for x in data['NLL']if x['partition']==p)for p in ['pilot_train','dev']},semantic_not_adjudicated=True,checkpoint_not_selected=True)
updates=[json.loads(x)for x in (P/'UPDATES.jsonl').read_text().splitlines()];delta=[json.loads(x)for x in (P/'UPDATE_DELTAS.jsonl').read_text().splitlines()];opt={}
for arm in ['A','B']:
 z=[x['trace']for x in updates if x['event']=='returned'and x['phase']=='pilot-retained'and x['arm']==arm];ds=[x for x in delta if x['phase']=='pilot-retained'and x['arm']==arm];opt[arm]=dict(retained=len(z),input_tokens=sum(x['input_tokens']for x in z),active_teachers=sum(x['active_teachers']for x in z),response_body_teachers=sum(x['response_body_teachers']for x in z),response_EOS_teachers=sum(x['response_EOS_teachers']for x in z),clip_count=sum(x['clipped']for x in z),gradient_min=min(x['gradient_norm']for x in z),gradient_median=statistics.median(x['gradient_norm']for x in z),gradient_max=max(x['gradient_norm']for x in z),first_loss=z[0]['loss'],last_loss=z[-1]['loss'],update_delta_L2_sum=sum(x['delta_L2']for x in ds),update_seconds=sum(x['seconds']for x in ds),loss_comparison='A/B teacher positions differ; TRAIN losses not directly ranked')
write('SUMMARY.json',dict(evaluations=summary,optimization=opt,formal_adoption='No-Go',broad_main_comparison='No-Go; narrow ASDC17-update pilot completed'))
# Teacher contributions by original source and type.
d=read('DATA.json');contrib={}
for source in ['main','vanilla','supplemental']:
 rs=[r for r in d['parts']['train']if r['source_file'].split('/')[1]==source];contrib[source]=dict(responses=len(rs),full_A=sum(len(r['tokens'])-1 for r in rs),body_B=sum(r['body_tokens']for r in rs),EOS_B=len(rs),all_B=sum(r['body_tokens']+1 for r in rs))
write('SOURCE_CONTRIBUTION.json',contrib)
# Same fixed reference NLL per source, not a new independent human/TEST score.
source_by_id={r['id']:r['source_file'].split('/')[1]for rs in d['parts'].values()for r in rs};sn={}
for name in scopes:
 sn[name]={}
 for part in ['pilot_train','dev']:
  sn[name][part]={}
  for s in ['main','vanilla','supplemental']:
   z=[r for r in read('evaluation/'+name+'.json')['NLL']if r['partition']==part and source_by_id[r['id']]==s];sn[name][part][s]=dict(cases=len(z),body_tokens=sum(r['body_tokens']for r in z),body_NLL=sum(r['body_sum']for r in z)/sum(r['body_tokens']for r in z))
write('SOURCE_NLL.json',sn)
print(json.dumps(dict(opt=opt,terminal={n:summary[n]['NLL']for n in scopes},generations={n:summary[n]['counts']for n in scopes}),ensure_ascii=False))
