import gzip,hashlib,json,unittest
from build_candidates import HERE,serialize,extract_oasst,encoder

class CandidateContracts(unittest.TestCase):
 def test_only_genuine_turn_eos(self):
  us=[dict(id='root',parent_id=None,source_role='prompter',text='a'),dict(id='answer',parent_id='root',source_role='assistant',text='bb')]
  s,b=serialize(us,lambda t:[10]*len(t));self.assertEqual(s,[1,3,10,2,4,10,10,2]);self.assertEqual([x['eos_offset']for x in b],[3,7])
 def test_missing_ancestor_rejected(self):
  with self.assertRaises(ValueError):serialize([dict(id='a',parent_id='missing',source_role='assistant',text='a')],lambda t:[10])
 def test_reordered_parent_rejected(self):
  us=[dict(id='root',parent_id=None,source_role='prompter',text='a'),dict(id='answer',parent_id='wrong',source_role='assistant',text='b')]
  with self.assertRaises(ValueError):serialize(us,lambda t:[10])
 def test_body_never_special(self):
  with self.assertRaises(ValueError):serialize([dict(id='a',parent_id=None,source_role='prompter',text='a')],lambda t:[2])
 def test_census_metadata_has_no_republished_body_or_ids(self):
  rows=[json.loads(l)for l in gzip.open(HERE/'derived/oasst-response-candidate-metadata.jsonl.gz','rt')];self.assertEqual(len(rows),len({r['id']for r in rows}));self.assertEqual(len(rows),361)
  for r in rows:
   self.assertNotIn('history',r);self.assertNotIn('response',r);self.assertNotIn('serialized_ids',r);self.assertFalse(r['admitted_for_training'])
 def test_census_source_ids_retained(self):
  raw=HERE.parent/'sns-data/derived/oasst-conversations.jsonl.gz';ids={u['id']for l in gzip.open(raw,'rt')for u in json.loads(l)['utterances']if u['source_role']=='assistant'}
  export={json.loads(l)['id']for l in gzip.open(HERE/'derived/oasst-response-candidate-metadata.jsonl.gz','rt')};self.assertEqual(ids,export)
if __name__=='__main__':unittest.main()
