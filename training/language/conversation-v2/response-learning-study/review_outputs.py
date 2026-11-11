"""Encode main-agent nonblind reading, reusing only byte-identical baseline verdicts."""
import json,pathlib,hashlib,collections,copy,os
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path(os.environ.get('CE_V2_ROOT',str(P.parent)));read=lambda p:json.loads(p.read_text())
old=read(V/'mixed-retention-study/evaluation/terminal-MIX-READING.json');baseline=read(V/'mixed-retention-study/evaluation/terminal-MIX.json');gold={(r['panel'],r['id']):r for r in old['rows']};raw={(r['panel'],r['id']):r for r in baseline['cases']};all=[]
explicit={'realpersona:01590:4','realpersona:08920:7','realpersona:12328:5','realpersona:06365:3','realpersona:05193:3','realpersona:06914:3','realpersona:13649:5','realpersona:02144:3','realpersona:13650:3','realpersona:12126:5','realpersona:03392:3','realpersona:05879:5','realpersona:09285:6'}
for name in ['initial','A-pilot4','B-pilot4']:
 x=read(P/f'evaluation/{name}.json');rows=[]
 for r in x['cases']:
  z=dict(id=r['id'],panel=r['panel'],eos_token=r['eos'],repeated4gram_proxy=r['repeated4gram']is not None,content_success=False,coherent_2_to_3_sentences=False,caption_natural=False,ending_only=False)
  if r['panel']=='human-dev19':
   z.update(method='main assistant read all outputs and original immediate question; nonblind',question_requires_answer=r['id']in explicit,decision='fail_specific_answer'if r['id']in explicit else'no_established_contextual_content_gain',reason='Question is not answered: generic acknowledgement, unrelated question, malformed words or no required concrete content.'if r['id']in explicit else'Open conversation turn: do not count as objectively grounded content-required question; no demonstrated new contextual information. Natural acknowledgement is not universally invalid.')
  else:
   b=raw[r['panel'],r['id']];prior=gold[r['panel'],r['id']];same=r['prefix']==b['prefix']and r['tokensIncludingEos']==b['tokensIncludingEos']and r['rawBytesHex']==b['rawBytesHex']and r['stopReason']==b['stopReason']
   z.update(method='reuse exact full-prefix/raw-token/stop-identical PR108 verdict'if same else'main assistant read changed unmodified output; baseline criterion unchanged',baseline_identical=same)
   if r['panel']=='new-caption32':
    z.update(caption_natural=prior['caption_natural'],ending_only=prior['ending_only_or_supplied_noun_completion'],reason=prior['reason'],decision=prior['decision'])
    if name=='A-pilot4'and r['id']=='stair:771030':z.update(caption_natural=True,decision='natural_short_text_only',reason='Complete prefix+output is ツヤのある床の上に白い犬が座っている: natural short scene description. Prior white banana held. No image truth or paragraph/generalization claim.')
   else:z.update(decision='fail',reason=prior['reason']if same else'Changed complete output remains repetitive, malformed or missing the question-specific facts. No coherent topic-preserving2–3 sentences.')
  rows.append(z)
 all.append(dict(model=name,rows=rows,caption_natural=sum(r['caption_natural']for r in rows)if any(r['panel']=='new-caption32'for r in rows)else None,human_required_question_subset=dict(cases=13,success=0),human_other_open_turns=dict(cases=6,formal_content_success_not_claimed=True),self_history_success=0 if x['self_history']else None,self_history_episodes=len(x['self_history'])))
extra=read(P/'EXTRA_EVALUATION.json');er=[]
for m in extra['models']:
 for r in m['cases']:
  reason='Does not supply required source-grounded fact(s); unrelated food/child text or acknowledgement only.'if r['panel']=='authored-grounded-dev7'else'Full original question/history and complete raw output read: no appropriate specific answer; generic acknowledgement, unrelated sweets/family topic or malformed text.'
  er.append(dict(model=m['model'],id=r['id'],panel=r['panel'],content_success=False,reason=reason,independent_human_evaluation=False))
(P/'READING.json').write_text(json.dumps(dict(reviewer='main assistant only, nonblind; no independent native human assessment',legacy_models=all,additional_DEV=er,raw_generation_changed=False,reference_string_mismatch_alone_not_failure=True,baseline_verdict_sha256=hashlib.sha256((V/'mixed-retention-study/evaluation/terminal-MIX-READING.json').read_bytes()).hexdigest(),caption_truth_limit='Text naturalness only; supplied caption prefix, no image verification',pilot_not_general_CE_superiority=True),ensure_ascii=False,indent=2)+'\n')
print([(m['model'],m['caption_natural'],len(m['rows']))for m in all])
