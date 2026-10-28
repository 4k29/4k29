import pathlib,json,gzip,hashlib,collections,importlib.util,sys
H=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(H/'pipeline'))
import build_candidates as b
enc,tok=b.encoder();rows=b.extract_oasst([json.loads(l)for l in gzip.open(H.parent/'sns-data/derived/oasst-conversations.jsonl.gz','rt')],enc,tok)
dec=json.loads((H/'quality/decisions.json').read_text());by={x['id']:x for x in dec};assert len(by)==361==len(rows);assert set(by)=={r['id']for r in rows}
selected=[];holds=[]
for r in rows:
 if by[r['id']]['decision']!='quality_candidate':continue
 reasons=[]
 if not r['token_audit']['full_ancestry_and_response_fit_context256']:reasons.append('full-context-over-256')
 if any(by.get(u['id'],{}).get('decision')!='quality_candidate'for u in r['history']if u['source_role']=='assistant'):reasons.append('ancestor-assistant-not-quality-approved')
 if reasons:holds.append({'id':r['id'],'reasons':reasons})
 else:selected.append(r)
b.write_gz(H/'final/oasst-conditional.jsonl.gz',selected)
train=[json.loads(l)for l in gzip.open(H/'derived/jmultiwoz-train-candidates.jsonl.gz','rt')]
receipt=json.loads((H/'evaluation/build-receipt.json').read_text());entities=receipt['must_quarantine_from_new_train']['entity_families']; seeds={r['id']for r in train if any(v in u['text']for v in entities for u in r['utterances'])}
blocked=set(seeds);authors=set()
while True:
 before=len(blocked)
 for r in train:
  if r['id']in blocked:authors.update(r['authors'])
 for r in train:
  if authors.intersection(r['authors']):blocked.add(r['id'])
 if len(blocked)==before:break
(H/'final/jmultiwoz-quarantine.json').write_text(json.dumps({'method':'DEV entity exact mention seed, then transitive source-local author component quarantine; no threshold tuning','seed_dialogues':len(seeds),'quarantined_ids':sorted(blocked),'quarantined_count':len(blocked),'remaining_count':len(train)-len(blocked),'official_dev_writer_overlap_source':'sources/jmultiwoz-speaker-overlap.json','formal_training_admitted':0},ensure_ascii=False,indent=2)+'\n')
s=importlib.util.spec_from_file_location('ev',H/'evaluation/benchmark.py');ev=importlib.util.module_from_spec(s);s.loader.exec_module(ev);cases=json.loads((H/'evaluation/dev.json').read_text())['cases'];evidence=json.loads((H/'evaluation/source-evidence.json').read_text())
for c in cases:ev.validate_case(c,evidence[c['source']['dialogue_id']])
prepared=ev.prepare(cases)
summary={'oasst_reviewed':len(dec),'decisions':dict(collections.Counter(x['decision']for x in dec)),'conditional_pairs':len(selected),'conditional_unique_families':len({x['family']for x in selected}),'conditional_authors':len({a for r in selected for a in r['source_authors']}),'conditional_response_body_tokens':sum(len(r['response_ids'])for r in selected),'conditional_categories':dict(collections.Counter(by[r['id']]['category']for r in selected)),'quality_candidates_additional_hold':holds,'new_train_acquired_dialogues':len(train),'new_train_quarantined':len(blocked),'dev_cases_evidence_and_context_passed':len(prepared),'independent_human_evaluation':False,'formal_training_admitted':0,'optimizer_updates':0,'go':'NO_GO','jmultiwoz_full_manual_sample_completed':False,'limitation':'Pending whole-sample review remains explicit; no unreviewed JMultiWOZ content admitted. Conditional OASST selection is assistant-reviewed, not human-certified.'}
(H/'final/SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False))
