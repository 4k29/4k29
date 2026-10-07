"""Validate learned character coverage and unmodified raw source/target bytes."""
import array,collections,hashlib,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parent;PARENT=ROOT.parent/'round3'
sys.path.insert(0,str(ROOT.parent.parent/'dialogue'))
from tokenizer import encode_stream
def read(p):return json.loads(p.read_text())
class DataTests(unittest.TestCase):
    def test_character_vocabulary_comes_only_from_train_and_aligns_every_cut(self):
        units=read(PARENT/'units.json');counts=collections.Counter(c for u in units if u['partition']=='train' for c in u['text']);freq=read(ROOT/'character-frequencies.json');meta=read(ROOT/'preparation.json');directory=ROOT/f"unicode-bpe-{meta['merges']}";tok=read(directory/'tokenizer.json')
        self.assertEqual({r['character']:r['frequency'] for r in freq},dict(counts));self.assertEqual(tok['characterTypes'],4259);self.assertEqual(tok['wordMerges'],0)
        self.assertEqual(meta['preparerSourceSha256'],hashlib.sha256((ROOT/'prepare_characters.py').read_bytes()).hexdigest())
        for r in freq:
            b=bytes.fromhex(tok['bytes'][r['token']]);self.assertEqual(b.decode(),r['character']);self.assertEqual(encode_stream(r['character'],tok),[r['token']])
        for u in units[::max(1,len(units)//32)]:
            text=u['text'];full=encode_stream(text,tok)
            for cut in [1,min(32,len(text)-1),min(80,len(text)-1)]:self.assertEqual(encode_stream(text[:cut],tok)+encode_stream(text[cut:],tok),full)
    def test_every_stream_preserves_original_chains_and_all_canonical_targets(self):
        units=read(PARENT/'units.json');lookup={(u['document'],u['startLine'],u['endLine']):u for u in units};meta=read(ROOT/'preparation.json');directory=ROOT/f"unicode-bpe-{meta['merges']}";tok=read(directory/'tokenizer.json');vocab=[bytes.fromhex(b) for b in tok['bytes']]
        for part in ['train','validation','test']:
            idx=read(directory/f'{part}.index.json');b=(directory/f'{part}.tokens.bin').read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),idx['tokensSha256'])
            values=array.array('I');values.frombytes(b)
            if sys.byteorder!='little':values.byteswap()
            groups=collections.defaultdict(list)
            for row in idx['rows']:groups[row['unit']].append(row)
            for d in idx['documents']:
                u=lookup[(d['sourceDocument'],d['startLine'],d['endLine'])];self.assertEqual(u['partition'],part)
                ids=values[d['offset']:d['offset']+d['length']];self.assertEqual(ids[0],1);self.assertEqual(ids[-1],2)
                self.assertTrue(all(t>=6 for t in ids[1:-1]));self.assertEqual(b''.join(vocab[t] for t in ids[1:-1]),u['text'].encode())
                if part=='train':
                    self.assertEqual(len(ids)-2,len(u['text']))
                    self.assertTrue(all(len(vocab[t].decode())==1 for t in ids[1:-1]))
                labels=[]
                for row in groups[d['id']]:labels.extend(values[row['offset']+row['prefixLength']:row['offset']+row['length']])
                self.assertEqual(labels,list(ids[1:]))
        policy=read(ROOT/'generation-policy.json');old=read(PARENT/'generation-policy.json')
        self.assertEqual(policy['probes'],old['probes']);self.assertEqual(policy['acceptance'],old['acceptance']);self.assertEqual(policy['generation']['maxNewTokens'],192)
if __name__=='__main__':unittest.main()
