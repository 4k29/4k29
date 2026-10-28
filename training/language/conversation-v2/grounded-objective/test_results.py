"""Standard-library publication checks, also run in GitHub CI without new learning."""
import collections, hashlib, json, pathlib, unittest
H=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads((H/p).read_text())
class Results(unittest.TestCase):
    def test_ledgers_include_replay_and_no_missing_completions(self):
        calls=[]
        for p in ['updates.jsonl','contrast-updates.jsonl']:
            rows=[json.loads(l)for l in(H/'run'/p).read_text().splitlines()]
            by=lambda event:collections.Counter((r['arm'],r['step'],r.get('replay',False))for r in rows if r['event']==event)
            self.assertEqual(by('intent'),by('completed'));calls +=[r for r in rows if r['event']=='completed']
        self.assertEqual(len(calls),1248);self.assertEqual(sum(r.get('replay',False)for r in calls),32)
        for arm in ['full','response']:self.assertTrue(read('run/'+arm+'-resume-audit.json')['steps16_to32_exact'])
    def test_executed_source_and_frozen_plan(self):
        self.assertEqual(hashlib.sha256((H/'TRAIN_EXECUTED.py').read_bytes()).hexdigest(),read('PLAN.json')['train_code_sha256'])
        self.assertEqual(hashlib.sha256((H/'data.json').read_bytes()).hexdigest(),read('PLAN.json')['data_sha256'])
        for name,r in read('EXECUTED_CODE.json').items():self.assertEqual(hashlib.sha256((H/r['executed_copy']).read_bytes()).hexdigest(),r['sha256'])
    def test_no_entity_or_case_leakage(self):
        d=read('data.json');e=read('contrast-data.json');a=d['train'][:2048]
        self.assertFalse({r['entity']for r in a}&{r['entity']for r in e})
        self.assertFalse({r['entity']for r in d['train']+e}&{r['entity']for r in d['dev']})
        self.assertEqual(len({r['id']for r in a+e}),2432)
    def test_raw_generation_bytes_are_unrepaired(self):
        tok=json.loads((H.parent/'data/tokenizer.json').read_text());pieces=[bytes.fromhex(v)for v in tok['bytes']]
        for folder,names in [('evaluation',['initial3470','full32','response32','full512','response512']),('evaluation-extra',['full-extra','response-extra'])]:
            for name in names:
                d=read(folder+'/'+name+'.json');rows=d['cases']+d['legacy']+[t for e in d['self_history']for t in e['turns']if 'tokensIncludingEos'in t]
                for r in rows:
                    self.assertEqual(r['eos'],r['tokensIncludingEos'][-1]==2)
                    b=b''.join(pieces[t]for t in r['nonEosTokens']);self.assertEqual(b.hex(),r['rawBytesHex'])
                    if r['strictUtf8']:self.assertEqual(b.decode('utf-8'),r['text'])
    def test_semantic_counts_differ_from_naive_automatic_matches(self):
        self.assertEqual(read('evaluation/PRIMARY_MANUAL_REVIEW.json')['full512_success'],0)
        self.assertEqual(read('evaluation/PRIMARY_MANUAL_REVIEW.json')['response512_success'],16)
        self.assertEqual(read('evaluation-extra/MANUAL_REVIEW.json')['response_extra_success'],7)
        self.assertEqual(read('evaluation/summary.json')['full512']['DEV_auto_candidates'],5)
    def test_full_state_counter_manifests(self):
        manifests=list((H/'run').glob('*/archive/checkpoint.json'));self.assertEqual(len(manifests),6)
        for p in manifests:
            d=json.loads(p.read_text());self.assertEqual(d['optimizer_steps'],[3470+d['retained_new_updates']]);self.assertFalse(d['formal_adoption'])
            self.assertTrue(all(c['bytes']<=32*1024**2 for c in d['chunks']))
if __name__=='__main__':unittest.main()
