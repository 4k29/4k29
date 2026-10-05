"""Deterministic own BPE fitting, weighted overlaps and numeric boundaries."""
import random
import unittest
from tokenizer import fit,fit_fast,encode,encode_stream,decode

class FitTests(unittest.TestCase):
    def test_local_updates_match_full_recount_with_weights_and_overlaps(self):
        rng=random.Random(429)
        samples=[[],[''],['aaaaa']*3,['日本語の順序です。']*4+['文章を続けます。'],['abababa','aaaaaa','bbbbbb']*3]
        for _ in range(25):
            texts=[''.join(rng.choice('あいうabc123。 ' ) for _ in range(rng.randrange(1,60))) for _ in range(8)]
            samples.append(texts+texts[:3]*2)
        for texts in samples:self.assertEqual(fit(texts,merges=80),fit_fast(texts,merges=80))
    def test_numeric_runs_never_merge_into_units_or_words(self):
        texts=['17個と16個を合わせます。17+16=33です。']*12+['Stringとtextareaの説明です。']*8
        tokenizer=fit_fast(texts,merges=120,numeric_boundaries=True)
        for hex_piece in tokenizer['bytes'][6:]:
            piece=bytes.fromhex(hex_piece)
            if any(48<=b<=57 for b in piece):self.assertTrue(all(48<=b<=57 for b in piece))
        self.assertIn(b'17'.hex(),tokenizer['bytes']);self.assertIn(b'16'.hex(),tokenizer['bytes'])
        for text in texts:
            self.assertEqual(encode(text,tokenizer),encode_stream(text,tokenizer));self.assertEqual(decode(encode_stream(text,tokenizer),tokenizer),text)

if __name__=='__main__':unittest.main()
