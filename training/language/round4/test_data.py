"""Check raw byte preservation, prefix masks and unchanged held partitions."""
import array,hashlib,json,pathlib,sys,unittest
ROOT=pathlib.Path(__file__).resolve().parent;PARENT=ROOT.parent/'round3'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class DataTests(unittest.TestCase):
    def test_every_focused_view_preserves_source_and_supervises_only_raw_suffix(self):
        source=PARENT/'raw-bpe-8192';directory=ROOT/'boundary-bpe-8192'
        info=read(directory/'train.index.json');old=read(source/'train.index.json');cuts=read(directory/'boundary-cuts.json');meta=read(directory/'data.json');tok=read(directory/'tokenizer.json')
        self.assertEqual(meta['focusedViews'],17992);self.assertEqual(len(cuts),17992)
        self.assertEqual(meta['newSourceDocuments'],0);self.assertTrue(meta['allCanonicalTargetsRetained'])
        self.assertEqual(meta['preparerSourceSha256'],sha(ROOT/'prepare_boundary_focus.py'))
        self.assertEqual(info['rows'][:len(old['rows'])],old['rows'])
        self.assertEqual(info['documents'][:len(old['documents'])],old['documents'])
        self.assertTrue((directory/'train.tokens.bin').read_bytes().startswith((source/'train.tokens.bin').read_bytes()))
        self.assertEqual(info['tokensSha256'],sha(directory/'train.tokens.bin'))
        values=array.array('I');values.frombytes((directory/'train.tokens.bin').read_bytes())
        if sys.byteorder!='little':values.byteswap()
        units={(u['document'],u['startLine'],u['endLine']):u for u in read(PARENT/'units.json')}
        focused={r['unit']:r for r in info['rows'][len(old['rows']):]};total=0
        for view in info['documents'][len(old['documents']):]:
            u=units[(view['sourceDocument'],view['startLine'],view['endLine'])];self.assertEqual(u['partition'],'train')
            ids=values[view['offset']:view['offset']+view['length']]
            self.assertEqual(ids[0],1);self.assertEqual(ids[-1],2);self.assertTrue(all(t>=6 for t in ids[1:-1]))
            text=b''.join(bytes.fromhex(tok['bytes'][t]) for t in ids[1:-1]);self.assertEqual(text,u['text'].encode())
            row=focused[view['id']];self.assertEqual(row['offset'],view['offset'])
            prefix=b''.join(bytes.fromhex(tok['bytes'][t]) for t in ids[1:row['prefixLength']])
            self.assertEqual(prefix,u['text'][:view['cutCharacters']].encode())
            self.assertEqual(row['length'],min(view['length'],row['prefixLength']+32))
            labels=ids[row['prefixLength']:row['length']];self.assertTrue(0<len(labels)<=32)
            self.assertNotIn(1,labels)
            if 2 in labels:self.assertEqual(row['length'],view['length'])
            total+=len(labels)
        self.assertEqual(total,meta['focusedLabelTokens'])
    def test_tokenizer_and_all_held_files_are_byte_identical(self):
        source=PARENT/'raw-bpe-8192';directory=ROOT/'boundary-bpe-8192'
        for name in ['tokenizer.json']+[f'{p}.{e}' for p in ['validation','test'] for e in ['tokens.bin','index.json']]:
            self.assertEqual(sha(source/name),sha(directory/name),name)
        policy=read(ROOT/'generation-policy.json');old=read(PARENT/'generation-policy.json')
        self.assertEqual(policy['acceptance'],old['acceptance']);self.assertEqual(policy['generation'],old['generation']);self.assertEqual(policy['probes'],old['probes'])
    def test_actual_training_pack_masks_prefix_and_labels_true_suffix(self):
        import numpy as np
        import torch
        from train import pack
        directory=ROOT/'boundary-bpe-8192';info=read(directory/'train.index.json')
        values=np.memmap(directory/'train.tokens.bin',dtype='<u4',mode='r')
        focused=[r for r in info['rows'] if r['variant']=='boundary-focus']
        for r in focused[::max(1,len(focused)//128)]:
            x,y=pack([r],values,256);p=r['prefixLength'];end=r['length']
            self.assertTrue(bool((y[0,:p-1]==-100).all()));self.assertTrue(bool((y[0,end-1:]==-100).all()))
            self.assertTrue(torch.equal(y[0,p-1:end-1],torch.tensor(values[r['offset']+p:r['offset']+end].astype('int64'))))
            self.assertEqual(int((y!=-100).sum()),end-p)
            self.assertEqual(int(x[0,p-1]),int(values[r['offset']+p-1]))
if __name__=='__main__':unittest.main()
