from common import *
import collections
rows={r['id']:r for r in gzrows(D/'corpus.jsonl.gz')};batches=json.load(gzip.open(D/'schedule.json.gz','rt'))['batches'];groups=collections.defaultdict(collections.Counter);pos=collections.Counter()
for b in batches:
 for w in b:
  c=groups[w['source']];c['windows']+=1;c['targets']+=len(w['tokens'])-1
  for j,t in enumerate(w['tokens'][1:]):
   c['EOS']+=t==2;c['role']+=t in [3,4];c['BOS']+=t==1;c['PAD']+=t==0;c['body']+=t>=6
   if t==2:pos[str((j//32)*32)+'-'+str((j//32)*32+31)]+=1
  original=rows[w['unit_id']];terminal=w['start']+len(w['tokens'])==len(original['tokens']);c['window_end_EOS']+=w['tokens'][-1]==2;c['arbitrary_cut_windows']+=not terminal;c['arbitrary_cut_assigned_false_EOS']+=not terminal and w['tokens'][-1]==2 and original['kind']!='human_dialogue'
for g in groups.values():assert not g['BOS']and not g['PAD']
assert groups['jaquad']['EOS']==0
# Genuine human turn EOS may coincide with a context cut; it remains an original utterance endpoint.
write(D/'TARGET_DISTRIBUTION.json',dict(source_targets={k:dict(v)for k,v in groups.items()},EOS_position_histogram_in_input_window=pos,teacher_total=sum(v['targets']for v in groups.values()),EOS_total=sum(v['EOS']for v in groups.values()),EOS_semantics='human original turn end; approved original whole paragraph/page boundary; complete JMA FAQ answer-section task end. Arbitrary cuts never receive appended EOS.',original_prose_page_end_units=sum(r.get('original_page_end',False)and r['EOS']for r in rows.values()if r['split']=='train'and r['kind']=='prose'),note='All counts refer to actual fixed one-pass teacher positions, not proposed amount. EPOS at a natural boundary coincident with a cut is not fabricated. EOS_unit flag per conversation must not be confused with per-turn EOS count.'))
