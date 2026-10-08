"""Check original byte/label coverage and unchanged own initialization before fitting."""
import array, collections, hashlib, json, pathlib, random, unittest
import torch
from prepare import ROOT,PARENT,read,sha
from batching import sampler,VIEWS
from initialization import initialize
import sys
sys.path.insert(0,str(ROOT.parent))
from model import Decoder

class Preflight(unittest.TestCase):
    def test_all_views_reconstruct_raw_source_and_cover_targets(self):
        units={(u['document'],u['startLine']):u for u in read(PARENT/'units.json') if u['partition'] in ['train','validation']}
        tok=read(ROOT/'multiview/tokenizer.json');vocab=[bytes.fromhex(b) for b in tok['bytes']]
        for part in ['train','validation']:
            info=read(ROOT/'multiview'/f'{part}.index.json');path=ROOT/'multiview'/f'{part}.tokens.bin'
            self.assertEqual(sha(path),info['tokensSha256']);values=array.array('I');values.frombytes(path.read_bytes());byunit=collections.defaultdict(list)
            for row in info['rows']:byunit[row['unit']].append(row)
            seen=collections.Counter()
            for doc in info['documents']:
                u=units[(doc['sourceDocument'],doc['startLine'])];self.assertEqual(u['partition'],part)
                full=list(values[doc['offset']:doc['offset']+doc['length']]);self.assertEqual(full[0],1);self.assertEqual(full[-1],2)
                self.assertEqual(b''.join(vocab[t] for t in full[1:-1]),u['text'].encode())
                covered=[]
                for row in byunit[doc['id']]:covered.extend(values[row['offset']+row['prefixLength']:row['offset']+row['length']])
                self.assertEqual(covered,full[1:]);seen[(doc['sourceDocument'],doc['startLine'])]+=1
                if doc['variant']==2:
                    prior=0
                    for index,cut in enumerate(doc['characterCuts']):
                        self.assertTrue(0<cut-prior<=24)
                        if index<len(doc['characterCuts'])-1:self.assertGreaterEqual(cut-prior,8)
                        prior=cut
                    self.assertEqual(prior,len(u['text']))
            self.assertTrue(all(n==3 for n in seen.values()))
        self.assertFalse((ROOT/'multiview/test.tokens.bin').exists())
    def test_each_genre_view_retains_declared_sampling_mass(self):
        rows=read(ROOT/'multiview/train.index.json')['rows']
        genres={'aozora':.45,'mic':.1,'env':.1,'mdn':.15,'jma':.1,'maff':.025,'stat':.05,'bunka':.025}
        strata,weights,masses=sampler(rows,genres)
        for site in genres:
            for variant in VIEWS:
                mass=sum(v for (s,k,w),v in weights.items() if s==site and k==variant)
                self.assertAlmostEqual(mass,genres[site]*VIEWS[variant])
        self.assertAlmostEqual(sum(masses.values()),1)
    def test_initial_weights_are_exactly_the_owned_selected_parent(self):
        torch.set_num_threads(2);saved=torch.load(PARENT/'word-512-continue-10000/checkpoint.pt',weights_only=False,map_location='cpu')
        model=Decoder(saved['config']);meta=initialize(model,read(ROOT/'multiview/tokenizer.json'))
        for key,value in model.state_dict().items():self.assertTrue(torch.equal(value,saved['beststate'][key]),key)
        self.assertEqual(meta['parentSelectedLineageUpdates'],39000)
        optimizer=torch.optim.AdamW(model.parameters());self.assertEqual(len(optimizer.state),0)
        self.assertEqual(read(ROOT/'policy.json')['completedUpdatesAtFreeze'],0)

if __name__=='__main__':unittest.main()
