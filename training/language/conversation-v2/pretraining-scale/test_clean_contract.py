import unittest,json,gzip,pathlib,hashlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3]
def load(p):return json.loads(p.read_text())
class CleanContract(unittest.TestCase):
 def test_source_resolved_family_hold_and_actual_exposure(self):
  fix=load(P/'FAMILY_EXCLUSION_FIX.json');old=list(map(json.loads,gzip.open(P/'corpus.jsonl.gz','rt')));new=list(map(json.loads,gzip.open(P/'corpus-clean.jsonl.gz','rt')));by={r['id']:r for r in old};self.assertEqual(by['jawikivoyage:5078:2']['component'],fix['held_component']);self.assertNotEqual(by['jawikivoyage:5078:2']['component'],'jawikivoyage|飲食を楽しむ');self.assertFalse({r['id']for r in new}&set(fix['held_ids']));self.assertFalse(any(r['component']==fix['held_component']for r in new));self.assertEqual(fix['excluded_tail_updates'],28)
 def test_comparison_and_pre_exposure_prefix_unchanged(self):
  a=json.load(gzip.open(P/'schedule.json.gz','rt'))['batches'];b=json.load(gzip.open(P/'schedule-clean.json.gz','rt'))['batches'];self.assertEqual(a[:759],b[:759]);self.assertEqual(len(a),len(b));self.assertEqual(sum(len(w['tokens'])-1 for batch in b for w in batch),2039162);self.assertEqual(sum(len(w['tokens'])-1 for batch in b[:512]for w in batch),351219)
 def test_no_remaining_held_teacher_target(self):
  fix=load(P/'FAMILY_EXCLUSION_FIX.json');seen=set();body=0
  for r in map(json.loads,gzip.open(P/'corpus-clean.jsonl.gz','rt')):
   if r['split']=='train':body+=len(r['body_tokens'])
  self.assertEqual(body,2045786)
  for b in json.load(gzip.open(P/'schedule-clean.json.gz','rt'))['batches']:
   for w in b:
    self.assertNotIn(w['unit_id'],fix['held_ids'])
    for j in range(w['start']+1,w['start']+len(w['tokens'])):self.assertNotIn((w['unit_id'],j),seen);seen.add((w['unit_id'],j))
  self.assertEqual(len(seen),2039162)
 def test_frozen_clean_input_sha(self):
  for name,want in load(P/'CLEAN_PLAN.json')['input_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),want)
if __name__=='__main__':unittest.main()
