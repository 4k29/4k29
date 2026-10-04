"""Own fast BPE equivalence and complete nonduplicated next-token coverage."""
import json
import pathlib
import random
import unittest
from tokenizer import encode,encode_stream,decode,SPECIALS
from stream_windows import windows
HERE=pathlib.Path(__file__).resolve().parent
class StreamTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tokenizer=json.loads((HERE/'binding-corpus.json').read_text())['tokenizer']
    def test_adjacent_heap_matches_original_learned_rule_passes(self):
        rng=random.Random(429)
        samples=['','𠮷と🦉','CMF BudsはハイブリッドANCに対応しています。','a'*45+'b'*23]
        samples += [''.join(rng.choice('日本語です。abc()123\nあいうえお学校写真') for _ in range(rng.randrange(1,120))) for _ in range(100)]
        for text in samples:self.assertEqual(encode_stream(text,self.tokenizer),encode(text,self.tokenizer))
    def test_every_document_target_is_predicted_exactly_once(self):
        text='日本語の文章を途中で終わったことにしません。次の文も続けて読めます。'*20
        full=[SPECIALS['bos']]+encode(text,self.tokenizer)+[SPECIALS['eos']]
        rows=windows(text,self.tokenizer,'test',maximum_input=32,lookback=8)
        covered=[]
        for row in rows:
            self.assertLessEqual(len(row['tokens']),33)
            self.assertEqual(row['tokens'],full[row['start']:row['end']])
            covered.extend(row['tokens'][row['prefixLength']:])
        self.assertEqual(covered,full[1:])
        self.assertEqual(sum(r['tokens'][r['prefixLength']:].count(SPECIALS['eos']) for r in rows),1)
        self.assertEqual(sum(SPECIALS['bos'] in r['tokens'] for r in rows),1)
    def test_empty_document_still_has_one_real_eos(self):
        rows=windows('',self.tokenizer,'empty');self.assertEqual(rows[0]['tokens'],[SPECIALS['bos'],SPECIALS['eos']])
if __name__=='__main__':unittest.main()
