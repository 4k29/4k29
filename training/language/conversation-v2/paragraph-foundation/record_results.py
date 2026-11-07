"""Persist actual receipts plus explicit main-assistant terminal judgments.
No metric is interpreted as a language pass without the separate reading decisions.
"""
import json,pathlib,collections,hashlib
P=pathlib.Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text())
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')

def main():
 results=[];base_read=read(pathlib.Path('/workspace/4k29/training/language/conversation-v2/modern-corpus/next-foundation/evaluation/B-6361-READING.json'));screen=read(P/'CONTENT_FAILURE_SCREEN.json')
 for name in ['base-0','A-579','B-579']:
  evaluation=read(P/'evaluation'/(name+'.json'));panel=read(P/'panels'/(name+'.json'));r=dict(model=name,checkpoint_sha256=evaluation['summary']['checkpoint_sha256'],NLL=evaluation['summary']['NLL'],generation_panels=evaluation['summary']['panels'],old_developed_prose_success=0,old_developed_prose_cases=45,new_connected_two_sentence_success=0,new_paragraph_cases=5,content24_strict_success=0,provided23_strict_success=0,grounded36_strict_success=0,context12_strict_success=0,self_history_strict_success=0,self_history_episodes=4,self_history_actual_turns=[len(e['turns'])for e in panel['self_history']],self_history_mechanical_three_turn_completion=sum(len(e['turns'])==3 and all(t.get('eos',False)for t in e['turns'])for e in panel['self_history']),independent_human_evaluation=False)
  captions=[c for c in evaluation['cases']if c['panel']=='new-caption32'];judgments=[]
  if name=='base-0':
   assert read(P/'BASELINE_REPRODUCTION.json')['matched_prior_cases']==97;r['caption_prefix_plus_continuation_clear']=21;r['caption_uncertain_not_passed']=4;r['caption_ending_heavy_within_clear']=4;judgments=base_read['caption_cases'];r['content24_uncertain_not_passed']=0;r['reading_source']='PR105 reading reused only after exact full-prefix/token/raw-byte reproduction proof; new5 read in this study'
  else:
   uncertain={'stair:40291','stair:117870'}if name=='A-579'else{'stair:401499'}
   failures={'stair:522263','stair:91227','stair:746796','stair:414909','stair:17039','stair:343877'}if name=='A-579'else{c['id']for c in captions if c['id']not in {'stair:705596','stair:346709','stair:401499'}}
   endings={'stair:709013','stair:54096','stair:808794','stair:287488','stair:90795'}if name=='A-579'else set()
   for c in captions:
    decision='uncertain_not_passed'if c['id']in uncertain else'fails_natural_text'if c['id']in failures else'natural_short_text_only'
    reason='Uncertain physical scale/scene relation; held consistently with earlier conservative scope'if decision=='uncertain_not_passed'else'Malformed word/argument relation, harmful loop or topic drift; source prefix plus full output does not form a natural coherent caption'if decision=='fails_natural_text'else'Natural supplied-prefix plus short continuation; not an independently generated paragraph, assistant answer or image-truth claim'
    judgments.append(dict(id=c['id'],judgment=decision,mostly_ending_or_supplied_noun_completion=c['id']in endings,reason=reason))
   r['caption_prefix_plus_continuation_clear']=sum(c['judgment']=='natural_short_text_only'for c in judgments);r['caption_uncertain_not_passed']=len(uncertain);r['caption_ending_heavy_within_clear']=len(endings);r['content24_uncertain_not_passed']=1 if name=='B-579'else 0;r['reading_source']='Main assistant terminal full-generation reading; mechanically obvious full-output loops screened as necessary failures; remaining full outputs read against requirements'
   reviews=[]
   screened={(c['panel'],c['index']):c for c in screen[name]['screened_necessary_failures']}
   for key in ['grounded36','legacy','context12']:
    for i,c in enumerate(panel[key]):
     kind=c.get('panel',key);uncertain_case=kind=='native24'and c.get('id')=='v2-content-dev-014'and name=='B-579';match=screened.get((kind,i))
     reason=match['reason']if match else'Grammatical positive-attitude fragment 最近のも好きです, but unresolved recent referent and no clear task-specific account of the drama; ambiguous partial response, not confidently counted as strict success'if uncertain_case else'Entire remaining output read: irrelevant assent/pseudo-words/repetition, missing required fact/choice/reason, or does not answer the stated question'
     reviews.append(dict(panel=kind,index=i,id=c.get('id',str(i)),decision='uncertain_not_passed'if uncertain_case else'fail',reason=reason,review_method='mechanically obvious necessary failure'if match else'main assistant full output reading'))
   write(P/'evaluation'/(name+'-CONTENT_REVIEW.json'),dict(rows=reviews,counts=r,formal_human_evaluation=False,source_file_sha256=hashlib.sha256((P/'panels'/(name+'.json')).read_bytes()).hexdigest()))
  r['caption_cases']=32;r['caption_judgments']=judgments;write(P/'evaluation'/(name+'-READING.json'),r);results.append(r)
 probes={}
 for name in ['base-0','A-579','B-579']:
  rows=read(P/'train-probes'/(name+'.json'))['cases'];probes[name]={}
  for panel_name in ['new_TRAIN_A','new_TRAIN_B']:
   rs=[r for r in rows if r['panel']==panel_name];n=sum(r['teacher_forced_positions']for r in rs);probes[name][panel_name]=dict(cases=len(rs),teacher_forced_positions=n,NLL=sum(r['teacher_forced_positions']*r['teacher_forced_nll']for r in rs)/n,exact_reference_prefix_reproduction=sum(r['reference_prefix_exact']for r in rs),EOS=sum(r['eos']for r in rs),repeat4=sum(r['repeated4gram']is not None for r in rs))
 write(P/'RESULTS.json',dict(results=results,TRAIN_probes=probes,comparison='Terminal579 only; intermediate checkpoints not selected posthoc',main_hypothesis='New coherent source prose alone yields two or more coherent new Japanese sentences',main_hypothesis_supported=False,formal_adoption='No-Go',public_replacement=False,sealed_TEST_opened=False,language_criteria_unchanged=True,uncertainty='B native24 contains one ambiguous positive-opinion fragment; independent native-human adjudication unavailable. Not claimed a clear failure or a pass.',midpoint_scope='Full raw generation, automatic metrics and new5 full reading; not separately complete semantic rescoring of every inherited intermediate item.',corpus_goal_shortfall='New592132 body tokens versus2–5M planning goal; one government provider, not broad contemporary everyday prose.'))
 print(json.dumps([{k:r[k]for k in ['model','old_developed_prose_success','new_connected_two_sentence_success','caption_prefix_plus_continuation_clear','content24_strict_success','content24_uncertain_not_passed','self_history_strict_success']}for r in results]))
if __name__=='__main__':main()
