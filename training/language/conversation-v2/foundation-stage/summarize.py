"""Aggregate receipts, loss/gradient traces and generation flags, no semantic auto-pass."""
import json,pathlib,statistics
H=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads((H/p).read_text())
def main():
 summary=dict(subagents_used=False,formal_model_adoption=False,independent_native_human_evaluation=False,original_text_accounting=read('ORIGINAL_TEXT_ACCOUNTING.json'),models={},training={})
 for name in ['initial','foundation','foundation-mixed','foundation-lr','qa-only','qa-rehearsal']:
  d=read('evaluation/'+name+'.json');r=dict(prose_tf_nll=d['prose_tf_nll'],prose_tf_targets=d['prose_tf_targets'],prose_EOS=sum(x['eos']for x in d['prose_dev']),prose_mechanical_repetition=sum(x['repeated4gram']is not None for x in d['prose_dev']),old_content_not_automatically_scored=True)
  for panel in ['native24','provided23']:r[panel+'_EOS']=sum(x['eos']for x in d['legacy']if x['panel']==panel)
  for key in ['grounded36','context12']:r[key+'_EOS']=sum(x['eos']for x in d[key])
  for suffix in ['human32','response-probe']:
   p=H/'evaluation'/(name+'-'+suffix+'.json')
   if p.exists():
    cs=json.loads(p.read_text())['cases'];groups={x.get('panel',suffix)for x in cs};r[suffix]={}
    for group in sorted(groups):
     rows=[x for x in cs if x.get('panel',suffix)==group];n=sum(x['reference_target_tokens']if'reference_target_tokens'in x else len(x['reference_tokens'])for x in rows);r[suffix][group]=dict(count=len(rows),tf_nll=sum(x['reference_nll_sum']for x in rows)/n,EOS=sum(x['eos']for x in rows),necessary_string_candidates=sum(x['necessary_string_candidate']for x in rows),not_semantic_pass=True)
  p=H/'evaluation'/(name+'-RP.json')
  if p.exists():
   rp=json.loads(p.read_text());r['RP_gold_history_body_nll']=rp['stats']['body']['nll'];r['RP_gold_end_mean_EOS_probability']=rp['gold_end_mean_EOS_probability']
  p=H/'evaluation'/(name+'-reading.json')
  if p.exists():r['manual_full_prose_reading']=json.loads(p.read_text())
  p=H/'evaluation'/(name+'-semantic-reading.json')
  if p.exists():r['manual_response_reading']=json.loads(p.read_text())
  summary['models'][name]=r
 for folder in ['run','mixed-run','lr-run']:
  receipt=read(folder+'/receipt.json');rs=[e['trace']for e in map(json.loads,(H/folder/'updates.jsonl').read_text().splitlines())if e['event']=='completed'and e['phase']=='retained'];norms=sorted(r['gradient_norm_before_clip']for r in rs);receipt.update(gradient_norm_min=norms[0],gradient_norm_median=statistics.median(norms),gradient_norm_max=norms[-1],clipped_updates=sum(n>1 for n in norms),weighted_train_nll=sum(r['loss']*r['target_tokens']for r in rs)/sum(r['target_tokens']for r in rs));summary['training'][folder]=receipt
 summary['training']['response-run']=read('response-run/receipt.json');summary['actual_optimizer_calls']=sum(r['actual_optimizer_updates']for r in summary['training'].values());summary['retained_optimizer_updates']=sum(r['retained_updates']for r in summary['training'].values());summary['replayed_optimizer_updates']=summary['actual_optimizer_calls']-summary['retained_optimizer_updates'];summary['retained_supervised_targets']=sum(summary['training'][x]['actual_targets']for x in ['run','mixed-run','lr-run'])+2*read('RESPONSE_PLAN.json')['supervised_targets_each'];summary['foundation_comparisons_do_not_triple_independent_corpus_volume']=True
 (H/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print('Actual / retained / replay:',summary['actual_optimizer_calls'],summary['retained_optimizer_updates'],summary['replayed_optimizer_updates'])
if __name__=='__main__':main()
