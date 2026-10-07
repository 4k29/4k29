"""Verify weighted word-pair learning against an independent naive reference."""
import collections,copy,pathlib,sys,unittest
from word_bpe import extend,apply_rules
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'dialogue'))
from tokenizer import SPECIALS,merge
class WordTests(unittest.TestCase):
 def test_frequency_ties_overlap_limits_and_duplicate_weights_match_reference(self):
  # Algorithm fixtures only; never model training records.
  base=dict(specials=SPECIALS,bytes=['']*6+[bytes([c]).hex() for c in b'abc\n'],merges=[],wordMerges=0)
  sequences=[[6,6,6,6,7,8],[7,6,7,6,7],[6,6,6,6,7,8],[8,7,6,9,6,7]]
  expected=copy.deepcopy(base);seq=collections.Counter(tuple(s) for s in sequences)
  for _ in range(12):
   vocab=[bytes.fromhex(b) for b in expected['bytes']];counts=collections.Counter()
   for row,weight in seq.items():
    for pair in zip(row,row[1:]):
     if len(vocab[pair[0]])+len(vocab[pair[1]])<=4:counts[pair]+=weight
   if not counts:break
   pair,n=min(counts.items(),key=lambda i:(-i[1],i[0]))
   if n<2:break
   token=len(vocab);expected['bytes'].append((vocab[pair[0]]+vocab[pair[1]]).hex());expected['merges'].append([*pair,token])
   updated=collections.Counter()
   for row,weight in seq.items():updated[tuple(merge(row,pair,token))]+=weight
   seq=updated
  actual=extend(sequences,base,merges=12,max_piece_bytes=4)
  self.assertEqual(actual['bytes'],expected['bytes']);self.assertEqual(actual['merges'],expected['merges']);self.assertEqual(base['merges'],[])
  for row in sequences:
   naive=list(row)
   for a,b,t in actual['merges']:naive=merge(naive,(a,b),t)
   self.assertEqual(apply_rules(row,actual['merges']),naive)
 def test_complete_unicode_word_pieces_and_existing_ids_are_preserved(self):
  chars=['統','計','を','学','ぶ','。'];base=dict(specials=SPECIALS,bytes=['']*6+[c.encode().hex() for c in chars],merges=[],wordMerges=0)
  sequences=[[6,7,8,9,10,11]]*4;actual=extend(sequences,base,merges=8,max_piece_bytes=12)
  self.assertEqual(actual['bytes'][:len(base['bytes'])],base['bytes'])
  for b in actual['bytes'][len(base['bytes']):]:self.assertTrue(bytes.fromhex(b).decode('utf-8'));self.assertLessEqual(len(bytes.fromhex(b)),12)
  self.assertEqual(b''.join(bytes.fromhex(actual['bytes'][t]) for t in apply_rules(sequences[0],actual['merges'])).decode(),'統計を学ぶ。')
if __name__=='__main__':unittest.main()
