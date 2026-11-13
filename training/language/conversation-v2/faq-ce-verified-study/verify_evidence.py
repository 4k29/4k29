"""Small evidence-only CI: stdlib, existing receipts, zero optimizer/model forward."""
import pathlib,json,hashlib,collections,math,unittest,os
P=pathlib.Path(__file__).resolve().parent;V=pathlib.Path(os.environ.get('STUDY_SIBLINGS',P.parent));BASE=pathlib.Path(os.environ.get('V2_ROOT',P.parent));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());SERIES=[('faq-ce-study',393,99,50,204),('faq-ce-clean-study',385,97,49,200),('faq-ce-verified-study',372,93,47,192)]
class Evidence(unittest.TestCase):
 def test_ledger_actual_calls(self):
  for folder,c,n,mid,actual in SERIES:
   p=V/folder;d=read(p/'DATA.json');r=read(p/'RESULT.json');u=[json.loads(s)for s in(p/'UPDATES.jsonl').read_text().splitlines()];self.assertEqual(len(u),2*actual)
   self.assertEqual(collections.Counter(x['phase']for x in u if x['event']=='returned'),{'study-retained':2*n,'preflight-original':4,'preflight-replay':2});self.assertEqual(r['actual_optimizer_returns'],actual);self.assertEqual(r['intents'],actual)
   self.assertTrue(all(u[k]['event']=='intent'and u[k+1]['event']=='returned'and all(u[k][x]==u[k+1][x]for x in['phase','arm'])for k in range(0,len(u),2)))
   for arm in'AB':
    rows=[x['trace']for x in u if x['event']=='returned'and x['phase']=='study-retained'and x['arm']==arm];self.assertEqual([x['step']for x in rows],list(range(1,n+1)));ids=[]
    for t,b in zip(rows,d['batch_order']):
     z=[d['parts']['train'][i]for i in b];self.assertEqual(t['ids'],[x['id']for x in z]);self.assertEqual(t['input_tokens'],sum(len(x['tokens'])-1 for x in z));self.assertEqual(t['active_teachers'],sum((len(x['tokens'])-1)if arm=='A'else x['body_tokens']+1 for x in z));self.assertEqual(t['lr'],1e-5);self.assertTrue(math.isfinite(t['loss'])and math.isfinite(t['gradient_norm']));ids+=t['ids']
    self.assertEqual(len(ids),len(set(ids)));self.assertEqual(len(ids),c)
 def test_forward_ledger(self):
  for folder,*_ in SERIES:
   p=V/folder;f=[json.loads(s)for s in(p/'FORWARDS.jsonl').read_text().splitlines()];r=read(p/'RESULT.json');self.assertEqual(len(f),2*r['model_forward_returns']);self.assertTrue(all(f[i]['event']=='intent'and f[i+1]['event']=='returned'and f[i]['phase']==f[i+1]['phase']for i in range(0,len(f),2)))
 def test_cold_manifests(self):
  for folder,c,n,mid,_ in SERIES:
   p=V/folder
   for a in'AB':
    for k in[mid,n]:
     m=read(p/f'artifacts/{a}-FAQ{k}/checkpoint.json');cold=read(p/f'COLD-{a}-{k}.json');self.assertTrue(cold['passed']and cold['remote_only_no_alternates']and cold['all_model_Adam_RNG_sampler_trace_equal']);self.assertEqual(cold['sha256'],m['sha256']);self.assertEqual(m['Adam_steps'],[6940+k]);self.assertEqual(m['plan_sha256'],sha(p/'PLAN.json'));self.assertEqual(sum(x['bytes']for x in m['chunks']),m['bytes']);self.assertTrue(all(x['bytes']<=32*1024**2 for x in m['chunks']));self.assertFalse(m['formal_adoption'])
 def test_initial_state_and_masks(self):
  for folder,*_ in SERIES:
   p=V/folder;s=read(p/'SOURCE_STATE.json');self.assertEqual(s['checkpoint_sha256'],'fc24624bcd3a298e3d0b32ecf8b419af32354c6196c764544249d05abcd980f7');self.assertEqual(s['initial_Adam_steps'],[6940]);z=read(p/'PREFLIGHT.json');self.assertTrue(z['passed']and z['initial_forward_identical']);self.assertEqual(z['actual_optimizer_calls'],6)
   for a in'AB':
    x=z['arms'][a];self.assertTrue(x['Adam_storage_nonshared']and x['separate_process_full_state_resume_exact']);self.assertEqual(x['first_update_audit']['masked_out_logit_gradient_abs_sum'],0);self.assertGreater(x['first_update_audit']['question_body_activation_gradient_L2'],0)
 def test_raw_generation_and_reading(self):
  pieces=[bytes.fromhex(x)for x in read(BASE/'data/tokenizer.json')['bytes']]
  for arm in'AB':
   p=P/f'evaluation/{arm}-study93.json';e=read(p);j=read(P/f'evaluation/{arm}-study93-READING.json');self.assertEqual(len(e['cases']),167);self.assertEqual(len(j['rows']),167);self.assertEqual(j['source_sha256'],sha(p));self.assertTrue(e['whole_vocabulary_greedy']and e['raw_unmodified']);self.assertEqual(len(e['self_history']),4)
   for x in e['cases']+[t for z in e['self_history']for t in z['turns']if'nonEosTokens'in t]:
    raw=b''.join(pieces[t]for t in x['nonEosTokens']);self.assertEqual(raw.hex(),x['rawBytesHex']);self.assertEqual(x['tokensIncludingEos'],x['nonEosTokens']+([2]if x['eos']else[]));self.assertEqual([s['chosen']for s in x['steps']],x['tokensIncludingEos']);self.assertLessEqual(len(x['prefix'])+len(x['tokensIncludingEos']),256)
   dev={x['id']:x for x in read(P/'DEV_PROTOCOL.json')['cases']};self.assertTrue(all(x['prefix']==dev[x['id']]['prefix']for x in e['cases']if x['panel']=='FAQ-dev'))
 def test_primary_data_gate_and_no_old_replacement(self):
  d=read(P/'DATA.json');ok=set(read(P/'ANSWER_BOUNDARY_STRICT_AUDIT.json')['pass_ids']);self.assertEqual(len(d['parts']['train']),372);self.assertTrue(all(x['id']in ok for x in d['parts']['train']));self.assertNotIn('jagov:12541',{x['id']for x in d['parts']['train']});self.assertEqual(read(P/'DEV_PROTOCOL.json'),read(V/'faq-ce-study/DEV_PROTOCOL.json'));self.assertTrue(read(P/'REBUILD_RECEIPT.json')['passed']);self.assertTrue(read(P/'NUMERICAL_CONTRACT.json')['passed']);self.assertEqual(read(V/'faq-ce-study/IMPORT_FIX.json')['actual_optimizer_calls'],0)
 def test_aggregate(self):
  s=read(P/'SUMMARY.json');self.assertEqual(s['actual_optimizer_calls'],596);self.assertEqual(s['retained'],578);self.assertEqual(s['discarded_original'],12);self.assertEqual(s['replay'],6);self.assertEqual(s['model_forwards'],sum(read(V/f/'RESULT.json')['model_forward_returns']for f,*_ in SERIES));self.assertEqual(len(read(P/'CHECKPOINT_INDEX.json')['states']),12)
if __name__=='__main__':unittest.main()
