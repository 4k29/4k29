"""CI artifact validation without importing Torch or performing model updates."""
import collections,gzip,hashlib,json,pathlib,struct,unittest
H=pathlib.Path(__file__).resolve().parent;V=H.parent
def read(p):return json.loads((H/p).read_text())
class Results(unittest.TestCase):
 def test_retained_replay_and_actual_counts(self):
  for folder in ['run','mixed-run','lr-run']:
   r=read(folder+'/receipt.json');events=list(map(json.loads,(H/folder/'updates.jsonl').read_text().splitlines()));by=lambda kind:collections.Counter((e['phase'],e['step'])for e in events if e['event']==kind)
   self.assertEqual(by('intent'),by('completed'));self.assertEqual(r['actual_optimizer_updates'],sum(e['event']=='completed'for e in events));self.assertEqual(r['retained_updates'],1576);self.assertEqual(r['actual_targets'],1111459);self.assertEqual(r['replay_updates'],2);self.assertTrue(read(folder+'/RESUME_AUDIT.json')['real_updates_3_to4_exact_after_process_restart'])
 def test_response_actual_and_replay(self):
  r=read('response-run/receipt.json');events=list(map(json.loads,(H/'response-run/updates.jsonl').read_text().splitlines()))
  for event in ['intent','completed']:self.assertEqual(sum(e['event']==event for e in events),516)
  self.assertEqual(r['actual_optimizer_updates'],516);self.assertEqual(r['retained_updates'],512);self.assertEqual(r['replayed_updates'],4);self.assertTrue(r['initial_state_identical_and_isolated'])
  schedule=json.load(gzip.open(H/'response-schedule.json.gz','rt'))
  for arm in ['control','treatment']:
   self.assertEqual(sum(len(x['answer_ids'])for b in schedule for x in b[arm]),6720);self.assertEqual(sum(len(x['sequence'])-1 for b in schedule for x in b[arm]),167711)
 def test_LR_is_only_additional_training_change(self):
  s=(H/'train_mixed.py').read_text().replace('MIXED_PLAN.json','LR_PLAN.json').replace("H/'mixed-run'","H/'lr-run'").replace("H/'train_mixed.py'","H/'train_lr.py'")
  s=s.replace(" st=saved['trajectory'];source_digest=digest(st);model,opt,rng=restore_isolated(st)\n"," st=saved['trajectory'];source_digest=digest(st);model,opt,rng=restore_isolated(st)\n for group in opt.param_groups:group['lr']=1e-4\n").replace("g['lr']==3e-5","g['lr']==1e-4")
  self.assertEqual(s,(H/'train_lr.py').read_text())
 def test_original_volume_excludes_join_separators(self):
  r=read('ORIGINAL_TEXT_ACCOUNTING.json');self.assertEqual(r['original_independent_paragraph_BPE_tokens'],1111717);self.assertEqual(r['joined_training_body_tokens']-r['original_independent_paragraph_BPE_tokens'],2836);self.assertEqual(r['actual_training_targets'],1111459)
 def test_same_loop_except_allocation_instrumentation(self):
  s=(H/'train.py').read_text().replace('from runtime import','from mixed_runtime import').replace("H/'PLAN.json'","H/'MIXED_PLAN.json'").replace("H/'schedule.json.gz'","H/'mixed-schedule.json.gz'").replace("H/'run'","H/'mixed-run'").replace("H/'train.py'","H/'train_mixed.py'")
  self.assertEqual(s,(H/'train_mixed.py').read_text())
 def test_known_families_and_original_bytes(self):
  tok=json.loads((V/'data/tokenizer.json').read_text());pieces=[bytes.fromhex(s)for s in tok['bytes']];rows=list(map(json.loads,gzip.open(H/'data.jsonl.gz','rt')))
  for key in ['family','component']:self.assertFalse({r[key]for r in rows if r['split']=='train'}&{r[key]for r in rows if r['split']=='dev'})
  for r in rows:self.assertEqual(b''.join(pieces[t]for t in r['tokens']).decode(),r['text'])
 def test_RP_windows_are_original_TRAIN_positions(self):
  meta=json.loads((V/'data/data.json').read_text());data=(H.parents[3]/meta['trainTokensPath']).read_bytes();mix=json.load(gzip.open(H/'mixed-schedule.json.gz','rt'));pure=json.load(gzip.open(H/'schedule.json.gz','rt'));ranges=[]
  for a,b in zip(pure['batches'],mix['batches']):
   self.assertEqual([len(w['tokens'])for w in a],[len(w['tokens'])for w in b]);self.assertEqual(a[:2],b[:2])
   for w in b[2:]:
    n=w['rp_length'];off=w['rp_offset'];self.assertEqual(list(struct.unpack('<'+str(n)+'I',data[4*off:4*(off+n)])),w['tokens']);self.assertEqual(meta['trainWindows'][w['rp_window']]['document'],w['document']);ranges.append((off+1,off+n))
  ranges.sort();self.assertTrue(all(a[1]<=b[0]for a,b in zip(ranges,ranges[1:])))
 def test_generated_bytes_never_repaired(self):
  pieces=[bytes.fromhex(b)for b in json.loads((V/'data/tokenizer.json').read_text())['bytes']]
  def walk(obj):
   if isinstance(obj,dict):
    if 'nonEosTokens'in obj and'rawBytesHex'in obj:
     b=b''.join(pieces[i]for i in obj['nonEosTokens']);self.assertEqual(b.hex(),obj['rawBytesHex'])
     if obj['strictUtf8']:self.assertEqual(b.decode(),obj['text'])
    for v in obj.values():walk(v)
   elif isinstance(obj,list):
    for v in obj:walk(v)
  for p in(H/'evaluation').glob('*.json'):walk(json.loads(p.read_text()))
 def test_fixed_primary_failure_is_preserved(self):
  self.assertEqual(read('evaluation/initial-reading.json')['coherent_full_continuations'],2);r=read('evaluation/foundation-reading.json');self.assertEqual(r['coherent_full_continuations'],0);self.assertFalse(r['primary_condition_pass']);self.assertEqual(read('PREFIX_TOKENIZATION_AUDIT.json')['mismatches'],4)
if __name__=='__main__':unittest.main()
