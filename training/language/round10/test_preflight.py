"""Raw source, owned initialization and sampler checks; no optimizer updates."""
import array,collections,hashlib,json,pathlib,sys,unittest
import torch
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent));from model import Decoder
from initialization import initialize
from batching import sampler
sys.path.insert(0,str(ROOT.parents[1]/'dialogue'));from tokenizer import encode_stream

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class Preflight(unittest.TestCase):
 def test_original_bytes_labels_folds_and_held_isolation(self):
  units=read(ROOT/'units.json');lookup={(u['document'],u['startLine'],u['endLine']):u for u in units}
  old=read(ROOT.parent/'round8/units.json')
  for u in old:self.assertEqual(lookup[(u['document'],u['startLine'],u['endLine'])],u)
  parts={a['document']:a['partition'] for a in read(ROOT/'split.json')['assignments']}
  for a in read(ROOT.parent/'round8/split.json')['assignments']:self.assertEqual(parts[a['document']],a['partition'])
  train='\n'.join(u['text'] for u in units if u['partition']=='train');policy=read(ROOT/'generation-policy.json');oldpolicy=read(ROOT.parent/'round8/generation-policy.json')
  for part,probes in policy['probes'].items():
   self.assertEqual(probes[:len(oldpolicy['probes'][part])],oldpolicy['probes'][part])
   for p in probes:self.assertNotIn(p['prefix'],train)
  base=read(ROOT/'unicode-bpe-4681/tokenizer.json')
  for merges in [512,1024]:
   directory=ROOT/f'word-bpe-{merges}';meta=read(directory/'data.json');tok=read(directory/'tokenizer.json');vocab=[bytes.fromhex(b) for b in tok['bytes']]
   self.assertEqual(meta['tokenizerSha256'],sha(directory/'tokenizer.json'));self.assertEqual(meta['rawUnitsSha256'],sha(ROOT/'units.json'))
   self.assertEqual(tok['bytes'][:len(base['bytes'])],base['bytes']);self.assertEqual(tok['merges'][:len(base['merges'])],base['merges'])
   for b in vocab[len(base['bytes']):]:self.assertTrue(b.decode('utf8'));self.assertLessEqual(len(b),18)
   for part in ['train','validation','test']:
    idx=read(directory/f'{part}.index.json');blob=(directory/f'{part}.tokens.bin').read_bytes();self.assertEqual(idx['tokensSha256'],hashlib.sha256(blob).hexdigest());values=array.array('I');values.frombytes(blob)
    if sys.byteorder!='little':values.byteswap()
    groups=collections.defaultdict(list)
    for r in idx['rows']:groups[r['unit']].append(r)
    variants=set()
    for n,d in enumerate(idx['documents']):
     variants.add(d['variant']);u=lookup[(d['sourceDocument'],d['startLine'],d['endLine'])];self.assertEqual(u['partition'],part)
     ids=values[d['offset']:d['offset']+d['length']];self.assertEqual((ids[0],ids[-1]),(1,2));self.assertTrue(all(t>=6 for t in ids[1:-1]));self.assertEqual(b''.join(vocab[t] for t in ids[1:-1]),u['text'].encode())
     labels=[]
     for r in groups[d['id']]:labels.extend(values[r['offset']+r['prefixLength']:r['offset']+r['length']])
     self.assertEqual(labels,list(ids[1:]))
     if d['variant']==0 and n%max(1,len(idx['documents'])//16)==0:self.assertEqual(list(ids[1:-1]),encode_stream(u['text'],tok))
    self.assertEqual(variants,{0,1} if part=='train' else {0})
 def test_owned_weights_and_training_gradient(self):
  torch.set_num_threads(1);saved=torch.load(ROOT.parent/'round8/expanded-characters-10000/checkpoint.pt',map_location='cpu',weights_only=False);old=Decoder(saved['config']);old.load_state_dict(saved['beststate']);old.eval()
  glyphs={r['character']:r['token'] for r in read(ROOT/'character-frequencies.json')};base=read(ROOT/'unicode-bpe-4681/tokenizer.json');refs=read(ROOT.parent/'round8/expanded-characters-10000/validation.json')['references']
  sys.path.insert(0,str(ROOT))
  from train import load_partition,pack
  for merges in [512,1024]:
   tok=read(ROOT/f'word-bpe-{merges}/tokenizer.json');config=dict(saved['config'],vocabulary=len(tok['bytes']));model=Decoder(config);info=initialize(model,tok);model.eval()
   self.assertEqual(info['parentSelectedWeightLineageUpdates'],28000);self.assertTrue(torch.equal(model.token.weight[:4840],old.token.weight));self.assertEqual(int(model.token.weight[4840:len(base['bytes'])].count_nonzero()),0)
   with torch.no_grad():
    for t in range(len(base['bytes']),len(tok['bytes'])):
     chars=bytes.fromhex(tok['bytes'][t]).decode();expected=.95*model.token.weight[[glyphs[c] for c in chars]].mean(0);torch.testing.assert_close(model.token.weight[t],expected,rtol=0,atol=0)
    for ref in refs:
     x=torch.tensor([ref['tokens']]);a=old(x)[0,-1];b=model(x)[0,-1];torch.testing.assert_close(a,b[:4840],rtol=0,atol=2e-4)
   self.assertTrue(all(p.requires_grad for p in model.parameters()));idx,values=load_partition(ROOT/f'word-bpe-{merges}','train');x,y=pack(idx['rows'][:2],values,256);model.train();loss=torch.nn.functional.cross_entropy(model(x).reshape(-1,config['vocabulary']),y.reshape(-1));loss.backward()
   self.assertGreater(float(model.token.weight.grad[len(base['bytes']):].abs().sum()),0)
   for b in model.blocks:self.assertGreater(float(b.fc2.weight.grad.abs().sum()),0)
 def test_sampling_preserves_genre_and_view_masses(self):
  genres={'aozora':.45,'mic':.1,'env':.1,'mdn':.15,'jma':.1,'maff':.025,'stat':.05,'bunka':.025}
  for merges in [512,1024]:
   rows=read(ROOT/f'word-bpe-{merges}/train.index.json')['rows'];strata,weights,masses=sampler(rows,genres);counts=collections.Counter((r['site'],r['variant']) for r in rows)
   for k,group in strata.items():self.assertAlmostEqual(weights[k]/len(group),genres[k[0]]*({0:.85,1:.15}[k[1]])/counts[k[:2]],places=14)
   for site,mass in genres.items():self.assertAlmostEqual(sum(w for k,w in weights.items() if k[0]==site),mass,places=12)
   for view,mass in {0:.85,1:.15}.items():self.assertAlmostEqual(sum(w for k,w in weights.items() if k[1]==view),mass,places=12)
if __name__=='__main__':unittest.main()
