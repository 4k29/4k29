"""Validate learned character coverage and unmodified raw source/target bytes."""
import array,collections,hashlib,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parent;PARENT=ROOT
sys.path.insert(0,str(ROOT.parent.parent/'dialogue'))
from tokenizer import encode_stream
def read(p):return json.loads(p.read_text())
class DataTests(unittest.TestCase):
    def test_character_vocabulary_comes_only_from_train_and_aligns_every_cut(self):
        units=read(PARENT/'units.json');counts=collections.Counter(c for u in units if u['partition']=='train' for c in u['text']);freq=read(ROOT/'character-frequencies.json');meta=read(ROOT/'preparation.json');directory=ROOT/f"unicode-bpe-{meta['merges']}";tok=read(directory/'tokenizer.json')
        self.assertEqual({r['character']:r['frequency'] for r in freq},dict(counts));self.assertEqual(tok['characterTypes'],4315);self.assertEqual(tok['wordMerges'],0)
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
        policy=read(ROOT/'generation-policy.json');old=read(ROOT.parent/'round6/generation-policy.json')
        self.assertEqual(policy['probes']['validation'][:9],old['probes']['validation']);self.assertEqual(policy['probes']['test'][:24],old['probes']['test']);self.assertEqual(policy['acceptance'],old['acceptance']);self.assertEqual(policy['generation']['maxNewTokens'],192)
    def test_parent_fold_units_and_token_ids_remain_unchanged(self):
        old=read(ROOT.parent/'round3/split.json');new=read(ROOT/'split.json');parts={a['document']:a['partition'] for a in new['assignments']}
        for a in old['assignments']:self.assertEqual(parts[a['document']],a['partition'])
        groups=collections.defaultdict(set)
        for a in new['assignments']:groups[a['group']].add(a['partition'])
        self.assertTrue(all(len(p)==1 for p in groups.values()))
        units=read(ROOT/'units.json');old_units=read(ROOT.parent/'round3/units.json');lookup={(u['document'],u['startLine'],u['endLine']):u for u in units}
        for u in old_units:self.assertEqual(lookup[(u['document'],u['startLine'],u['endLine'])],u)
        tok=read(ROOT/'unicode-bpe-4578/tokenizer.json');oldtok=read(ROOT.parent/'round5/unicode-bpe-4503/tokenizer.json')
        self.assertEqual(tok['bytes'][:len(oldtok['bytes'])],oldtok['bytes']);self.assertEqual(tok['merges'][:len(oldtok['merges'])],oldtok['merges'])
        train='\n'.join(u['text'] for u in units if u['partition']=='train')
        for probes in read(ROOT/'generation-policy.json')['probes'].values():
            for probe in probes:self.assertNotIn(probe['prefix'],train)
if __name__=='__main__':unittest.main()
