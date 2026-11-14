"""Evidence-only aggregation and serialization of main-agent readings; no model import."""
import json,pathlib,hashlib,statistics,collections
P=pathlib.Path(__file__).resolve().parent
STATES=['A-base','B-base','SFT-A-93','SFT-B-93']
def load(f):return json.loads((P/f).read_text())
def sha(f):return hashlib.sha256((P/f).read_bytes()).hexdigest()
def write(f,v):(P/f).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
BASE=set('709013 164607 780709 54096 363439 468221 705596 808794 269737 728815 314944 822181 287488 372931 90795 293007 322805 401499 526115 346709 337807'.split())
MINIMAL=set('54096 808794 287488 372931 90795 337807'.split())
REGRESS={'A-base':set(),'B-base':set(),'SFT-A-93':{'468221','822181'},'SFT-B-93':{'780709','468221','822181','322805'}}
CRITERIA={'source-heldout-prose12':'提示済み第1文を数えず、新たな2〜3文の主題・意味接続と自然さが必要。', 'new_source_heldout_paragraph5':'新たな複数文で入力の主題と説明を維持。', 'native24':'固定の内容必須条件を具体的に充足。汎用相槌だけでは不合格。','provided23':'仮定資料の料金・理由・条件・履歴に沿う具体回答が必要。','ASDC-condition-dev15':'元会話の指定条件を確認・参照する具体応答が必要。'}
summary={}
for state in STATES:
 d=load('evaluation/'+state+'.json'); rows=[]
 for r in d['cases']:
  panel=r['panel'];text=r.get('text');key=r['id'].split(':')[-1]
  ok=panel=='new-caption32' and key in BASE-REGRESS[state]
  reason='入力の必要情報を返さず、無関係な定型応答・疑似語・反復へ逸脱。原文完全一致を判定条件にはしない。'
  if panel in ['old24','oldNew9','new-MAFF12','new_source_heldout_paragraph5','source-heldout-prose12']:
   reason='意味のつながった新たな複数文が成立しない。語尾補完・既提示文・単なるEOSは段落成功に数えない。'
  if panel=='new-caption32':
   reason=('入力と結合して場面として読める短文。画像事実の正しさは未検証。' if ok else '場面の意味・構文・対象対応に疑義があり、自然候補として確認できない。')
   if state=='SFT-B-93' and key=='322805':reason='「草の中で2頭の象が草原にいる」は場所表現が冗長で判定保留。厳格な確認数には含めず、緩い基準なら追加1件の不確実性。'
   if key in MINIMAL:reason+=' 既提示名詞・動作への短い語尾補完なので自立した長文生成とは区別。'
  if text=='':reason='真EOSのみで出力本文なし。UTF-8破損ではない。'
  elif text is not None and not text.strip():reason='空白・改行だけが継続し、意味のある本文がない。'
  elif r.get('repeated4gram'):reason+=' 保存された4-gram反復proxyも陽性だが、proxyだけで意味判定していない。'
  rows.append({'id':r['id'],'panel':panel,'raw_case_sha256':hashlib.sha256(json.dumps(r,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'strict_task_success':ok,'minimal_ending_completion':panel=='new-caption32' and key in MINIMAL,'judgment':'confirmed-natural-caption' if ok else ('hold' if panel=='new-caption32' else 'not-established'),'criterion':CRITERIA.get(panel,'固定された元DEVの必要内容・根拠に従う。'),'reason':reason})
 selfrows=[{'id':r['id'],'success':False,'reason':'自己生成履歴で最初の条件回答から外れ、必要な料金比較・場所・食品選択を保持できない。途中停止も成功とはしない。'}for r in d['self_history']]
 write('evaluation/'+state+'-READING.json',{'evidence_sha256':sha('evaluation/'+state+'.json'),'reviewer':'main Codex agent only; nonblind; no independent native-speaker review','cached_A_base_prior_judgments_reused':state=='A-base','cases':rows,'self_history':selfrows})
 nll={}
 for partition in ['train','dev']:
  rr=[x for x in d['NLL']if x['partition']==partition];nll[partition]={'rows':len(rr),'body_tokens':sum(x['body_tokens']for x in rr),'body_NLL':sum(x['body_sum']for x in rr)/sum(x['body_tokens']for x in rr),'with_EOS_NLL':sum(x['with_EOS_sum']for x in rr)/sum(x['with_EOS_tokens']for x in rr)}
 panels={}
 for panel in sorted(set(x['panel']for x in rows)):
  rr=[x for x in d['cases']if x['panel']==panel];jj=[x for x in rows if x['panel']==panel]
  panels[panel]={'n':len(rr),'strict_success':sum(x['strict_task_success']for x in jj),'EOS':sum(x['eos']for x in rr),'repeated4gram_proxy':sum(bool(x['repeated4gram'])for x in rr),'empty':sum(x.get('text')==''for x in rr),'whitespace_only_nonempty':sum(bool(x.get('text')) and not x['text'].strip()for x in rr),'starts_mata':sum((x.get('text')or'').lstrip().startswith('また')for x in rr)}
 pp=[x for rr in d['prose_NLL']for x in rr['positions']if x['token']not in [0,1,2,3,4,5,16]]
 summary[state]={'FAQ':nll,'prose_body_NLL':statistics.mean(x['nll']for x in pp),'source_NLL':d['source_dev_NLL']['groups'],'panels':panels,'self_success':0,'self_n':len(selfrows),'reading_sha256':sha('evaluation/'+state+'-READING.json')}
u=[json.loads(x)for x in(P/'UPDATES.jsonl').read_text().splitlines()];returned=[x for x in u if x['event']=='returned'];ret=[x for x in returned if x['phase']=='retained']
bytag={}
for tag in ['LM','SFT-A','SFT-B']:
 rr=[x['trace']for x in ret if x['tag']==tag];bytag[tag]={'updates':len(rr),'active_teachers':sum(x['active_teachers']for x in rr),'input_nonPAD':sum(x['input_nonPAD']for x in rr),'loss_first':rr[0]['loss'],'loss_last':rr[-1]['loss'],'mean_loss_not_target_weighted':statistics.mean(x['loss']for x in rr),'gradient_norm_min':min(x['gradient_norm']for x in rr),'gradient_norm_median':statistics.median(x['gradient_norm']for x in rr),'gradient_norm_max':max(x['gradient_norm']for x in rr),'clip_count':sum(x['clipped']for x in rr),'LR':sorted(set(x['LR']for x in rr)),'Adam_step_first':rr[0]['Adam_step'],'Adam_step_last':rr[-1]['Adam_step'],'weight_delta_L2_first':rr[0]['weight_delta_L2'],'weight_delta_L2_last':rr[-1]['weight_delta_L2']}
aa=[x['trace']for x in ret if x['tag']=='SFT-A'];bb=[x['trace']for x in ret if x['tag']=='SFT-B'];identical=all(all(a[k]==b[k]for k in ['step','torch_rng_before_sha256','mask_sha256','IDs','input_nonPAD','active_teachers'])for a,b in zip(aa,bb));assert len(aa)==len(bb)==93 and identical
summary['training']={'by_tag':bytag,'actual_calls':len(returned),'phases':dict(collections.Counter(x['phase']for x in returned)),'SFT_all_93_input_mask_RNG_before_equal':identical,'source_RESULT':load('RESULT.json')}
a=summary['A-base']['FAQ']['dev']['body_NLL'];b=summary['B-base']['FAQ']['dev']['body_NLL'];ap=summary['SFT-A-93']['FAQ']['dev']['body_NLL'];bp=summary['SFT-B-93']['FAQ']['dev']['body_NLL'];summary['absorption']={'A_NLL_gain':a-ap,'B_NLL_gain':b-bp,'difference_in_gain':(b-bp)-(a-ap),'interpretation':'NLL gain differences are descriptive; no generalization/semantic success claim.'}
write('SUMMARY.json',summary)
print(json.dumps({'training':summary['training']['by_tag'],'absorption':summary['absorption']},ensure_ascii=False,indent=2))
