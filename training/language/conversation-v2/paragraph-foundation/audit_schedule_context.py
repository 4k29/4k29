"""Measure actual immutable schedule row cuts, including equal-budget batch splits."""
import json,gzip,pathlib,collections
P=pathlib.Path(__file__).resolve().parent

def main():
 corpus=[json.loads(l)for l in gzip.open(P/'corpus.jsonl.gz','rt')];schedule=json.load(gzip.open(P/'schedule.json.gz','rt'));pieces=[bytes.fromhex(x)for x in json.loads((P.parent/'data/tokenizer.json').read_text())['bytes']];out={}
 for arm,bs in schedule['arms'].items():
  c=collections.Counter();hist=collections.Counter();restored_padding=0
  for batch in bs:
   widths=[]
   for r in batch:
    start=r['start'];n=r['length']-1;lost=start%256;c['rows']+=1;c['targets']+=n;c['rows_after_original_context256_boundary']+=start>=256
    if lost:c['rows_created_by_extra_batch_budget_split']+=1;c['targets_with_less_context_than_original256_window']+=n;c['summed_missing_prefix_context_tokens']+=lost
    c['maximum_lost_context_tokens']=max(c['maximum_lost_context_tokens'],lost)
    widths.append(lost+n)
    for j in range(1,n+1):hist[j]+=1
    if start:
     c['actual_history_reset_rows']+=1;raw=b''.join(pieces[t]for t in corpus[r['record']]['tokens'][:start+1])
     try:s=raw.decode('utf8');c['history_reset_after_sentence_mark']+=s.rstrip().endswith(('。','！','？'))
     except UnicodeDecodeError:c['history_reset_inside_UTF8_codepoint']+=1
   restored_padding=max(restored_padding,max(widths)*len(batch))
  total=sum(hist.values());c['targets_with_at_most16_left_tokens']=sum(n for h,n in hist.items()if h<=16);c['targets_with_at_most32_left_tokens']=sum(n for h,n in hist.items()if h<=32)
  out[arm]=dict(counts=dict(c),fraction_targets_extra_batch_split_context_loss=c['targets_with_less_context_than_original256_window']/total,mean_current_left_context=sum(h*n for h,n in hist.items())/total,max_padded_positions_if_original_window_prefix_restored=restored_padding)
 report=dict(analysis_only_no_schedule_or_model_changes=True,arms=out,finding='Exact1024-target batching can split a256-target source window again. The next row retains only one input token and resets positions; targets remain genuine and nonduplicated, but available history is shorter than the original window. Quantify rather than attributing a failed paragraph result to capacity alone.',possible_separate_followup='Same initial state/data/teacher positions/targets/LR/optimizer: restore the original256-window prefix at batch-created splits and mask prefix-only labels. This changes conditioning and position layout, not vocabulary/context size or loss on actual teacher positions. Do not mix into the running A/B comparison.',future_proof_required='Exact teacher-position masks, gradients, replay, padding/memory and original-window causal-score equivalence before any followup updates.')
 (P/'SCHEDULE_CONTEXT_LOSS_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
