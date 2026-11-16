"""Lightweight completed-run consistency tests; never import Torch or rerun models."""
import pathlib,json,gzip,hashlib,unittest,math,collections,subprocess,sys
P=pathlib.Path(__file__).resolve().parent;V=P.parent;R=V.parents[2]
read=lambda p:json.loads(pathlib.Path(p).read_text());sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def rows(p):return [json.loads(x)for x in gzip.decompress(pathlib.Path(p).read_bytes()).splitlines()]
def ledger(n):return [json.loads(x)for x in(P/n).read_text().splitlines()]
class CompletedPilot(unittest.TestCase):
 def test_01_frozen_execution_and_data(self):
  p=read(P/'PLAN.json');self.assertTrue(p['training_GO']);self.assertEqual(p['study_type'],'limited-distribution-pilot');self.assertEqual(sha(P/'PLAN.json'),(P/'PLAN.sha256').read_text().strip())
  for f,h in p['sha256'].items():self.assertEqual(sha(R/f),h,f)
 def test_02_old67_byte_metadata_preserved(self):
  old=rows(V/'novel-continuous-study/REVIEWED_PROSE.jsonl.gz')+rows(V/'staged-prose-study/ADDITIONAL_PROSE.jsonl.gz');self.assertEqual(rows(P/'corpus-C.jsonl.gz')[:67],old)
 def test_03_review_scope_and_held_decisions(self):
  d=read(P/'GV_REVIEW.json');self.assertEqual(len(d['cases']),90);self.assertEqual(len({r['id']for r in d['cases']}),90);self.assertTrue(d['new65_individually_read']);self.assertTrue(d['provisional7_resolved']);old=read(V/'staged-prose-study/GV_INTRO_READING.json')['cases']
  for i in range(25):
   if i not in [4,5,6,7,11,19,24]:self.assertEqual(d['cases'][i]['decision'],old[i]['decision']);self.assertEqual(d['cases'][i]['SHA'],old[i]['SHA'])
 def test_04_only_verified4_added(self):
  a=rows(P/'GV_ADDITIONAL.jsonl.gz');self.assertEqual(len(a),4);rv={r['id']:r for r in read(P/'GV_REVIEW.json')['cases']};receipt={r['index']:r for r in read(P/'SOURCE_RECEIPTS.json')}
  for r in a:
   self.assertEqual(r['text_SHA'],rv[r['id']]['text_SHA']);self.assertEqual(rv[r['id']]['final_decision'],'admit_historical_report_LM');self.assertTrue(any('翻訳'in c['role']for c in r['attribution']));self.assertTrue(any('記者'in c['role']for c in r['attribution']));self.assertIn(rv[r['id']]['index'],receipt)
 def test_05_no_duplicate_original_paragraph_or_fake_EOS(self):
  seen=set()
  for r in rows(P/'corpus-C.jsonl.gz'):
   self.assertFalse(r['EOS']);self.assertNotIn(2,r['tokens'])
   for h in r['original_paragraph_hashes']:self.assertNotIn(h,seen);seen.add(h)
 def test_06_equal_teacher_budget(self):
  s=read(P/'SCHEDULE.json')
  for arm in ['B','C']:
   self.assertEqual(len(s[arm]),14);self.assertEqual([sum(x['targets']for x in b)for b in s[arm]],[1024]*13+[344])
  self.assertEqual(read(P/'DATA_AUDIT.json')['conditions']['B']['targets'],13656);self.assertEqual(read(P/'DATA_AUDIT.json')['conditions']['C']['targets'],13656)
 def test_07_exact_physical_optimizer_ledger(self):
  u=ledger('UPDATES.jsonl');o=ledger('OPTIMIZER_CALLS.jsonl');result=read(P/'RESULT.json');self.assertTrue(result['passed']);self.assertEqual(result['actual_optimizer_calls'],34)
  for ls in [u,o]:self.assertEqual(sum(x['event']=='intent'for x in ls),34);self.assertEqual(sum(x['event']=='returned'for x in ls),34)
  done=[x for x in u if x['event']=='returned'];self.assertEqual(collections.Counter(x['phase']for x in done),{'retained':28,'discarded-original':4,'resume-replay':2})
  for arm in ['B','C']:
   a=[r['trace']for r in done if r['phase']=='retained'and r['condition']==arm];self.assertEqual([x['step']for x in a],list(range(1,15)));self.assertEqual(sum(x['active_teachers']for x in a),13656);self.assertEqual([x['Adam_step']for x in a],list(range(6941,6955)))
   for r in a:self.assertEqual(r['LR'],3e-5);self.assertTrue(math.isfinite(r['loss'])and math.isfinite(r['gradient_norm']));self.assertEqual(r['clipped'],r['gradient_norm']>1.)
 def test_08_actual_forwards_and_reuse(self):
  f=ledger('FORWARDS.jsonl');self.assertEqual(sum(x['event']=='intent'for x in f),6265);self.assertEqual(sum(x['event']=='returned'for x in f),6265);r=read(P/'RESULT.json');self.assertEqual(r['model_forwards'],6265);self.assertEqual(r['reused_caption_generations'],32);self.assertEqual(r['reused_saved_logit_tensors'],0)
 def test_09_all6_complete_cold_restores(self):
  ix=read(P/'CHECKPOINT_INDEX.json')['checkpoints'];self.assertEqual({(r['condition'],r['cursor'])for r in ix},{(a,n)for a in ['B','C']for n in [4,7,14]})
  for r in ix:
   m=read(P/r['manifest']);cold=read(P/f"COLD-{r['condition']}-{r['cursor']}.json");self.assertEqual(sha(P/r['manifest']),r['manifest_SHA']);self.assertEqual(m['sha256'],r['fullstate_SHA']);self.assertEqual(sum(z['bytes']for z in m['chunks']),m['bytes']);self.assertEqual(cold['sha256'],m['sha256']);self.assertTrue(cold['passed']and cold['all_state_equal']and cold['remote_only_no_alternates']);self.assertEqual(m['Adam_steps'],[6940+r['cursor']])
 def test_10_independent_updated_state_resume(self):
  b=read(P/'PREFLIGHT-B.json');c=read(P/'PREFLIGHT-C.json');self.assertEqual(b['initial'],c['initial']);self.assertTrue(read(P/'RESULT.json')['initials_equal']);self.assertTrue(read(P/'RESULT.json')['source_unchanged'])
  for x in [b,c]:self.assertTrue(x['passed']and x['update_resume_exact']and x['Adam_storage_nonshared']);self.assertEqual((x['discarded_original'],x['replay'],x['retained']),(2,1,0))
 def test_11_raw_bytes_fixed_prefix_no_repair(self):
  pieces=[bytes.fromhex(x)for x in read(V/'data/tokenizer.json')['bytes']];initial={x['id']:x for x in read(P/'evaluation/initial.json')['cases']}
  dev=read(P/'EVALUATION_INPUTS.json')['prose'];prior=read(V/'novel-continuous-study/NEW_PROSE_DEV.json')['cases']+read(V/'foundation-absorption-study/PROSE_DEV.json')['cases'];by={r['id']:r for r in prior}
  for r in dev:self.assertEqual(r['prefix'],by[r['id']]['prefix']);self.assertEqual(r['teacher_continuation'],by[r['id']]['teacher_continuation'])
  cached=read(V/'mixed-retention-study/evaluation/terminal-MIX.json');self.assertEqual(cached['checkpoint_sha256'],'fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7')
  for r in cached['cases']:
   if r['panel']=='new-caption32':self.assertEqual(r['tokensIncludingEos'],initial[r['id']]['tokensIncludingEos']);self.assertEqual(r['prefix'],initial[r['id']]['prefix'])
  for name in ['initial','B-terminal','C-terminal']:
   d=read(P/'evaluation'/f'{name}.json');self.assertEqual(len(d['cases']),50);self.assertEqual(len(d['NLL']),18);self.assertTrue(d['whole_vocabulary_greedy']and d['raw_unmodified'])
   for r in d['cases']:
    self.assertEqual(r['prefix'],initial[r['id']]['prefix']);self.assertEqual(r['maxNewTokens'],initial[r['id']]['maxNewTokens']);self.assertEqual(r['eos'],r['tokensIncludingEos'][-1]==2);self.assertEqual(b''.join(pieces[t]for t in r['nonEosTokens']).hex(),r['rawBytesHex']);self.assertLessEqual(len(r['prefix'])+len(r['tokensIncludingEos']),256)
    if r['strictUtf8']:self.assertEqual(bytes.fromhex(r['rawBytesHex']).decode(),r['text'])
 def test_12_semantic_counts_not_proxy_success(self):
  s=read(P/'SEMANTIC_REVIEW.json');self.assertEqual([s['counts'][n]['caption_natural']for n in ['initial','B-terminal','C-terminal']],[21,20,22]);self.assertEqual(s['counts']['C-terminal']['caption_initial21_retained'],20)
  for n in ['initial','B-terminal','C-terminal']:self.assertEqual(s['counts'][n]['paragraph_new6'],0);self.assertEqual(s['counts'][n]['paragraph_old12'],0)
  self.assertFalse(read(P/'RESULT.json')['formal_adoption']);self.assertTrue(read(P/'PLAN.json')['no_SFT'])
if __name__=='__main__':unittest.main()
