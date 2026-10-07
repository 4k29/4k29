"""TRAIN-only independent BPE cuts, with loss focused on raw continuations.

Canonical rows keep all source targets. Additional rows supervise up to32 true
continuation tokens after Unicode cuts; no words or artificial EOS are added.
"""
import array,copy,hashlib,json,pathlib,random,shutil,sys
ROOT=pathlib.Path(__file__).resolve().parent
PARENT=ROOT.parent/'round3'
sys.path.insert(0,str(ROOT.parent.parent/'dialogue'))
from tokenizer import encode_stream,SPECIALS
def read(p):return json.loads(p.read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n')
def main():
    source=PARENT/'raw-bpe-8192';out=ROOT/'boundary-bpe-8192';out.mkdir(exist_ok=True)
    if (out/'data.json').exists():raise ValueError('Prepared data is immutable; choose a new experiment instead of overwriting')
    index=copy.deepcopy(read(source/'train.index.json'));raw=(source/'train.tokens.bin').read_bytes();assert sha(raw)==index['tokensSha256']
    values=array.array('I');values.frombytes(raw)
    if sys.byteorder!='little':values.byteswap()
    tok=read(source/'tokenizer.json');parts={r['document']:r['partition'] for r in read(PARENT/'split.json')['assignments']}
    units=[u for u in read(PARENT/'units.json') if u['partition']=='train'];cuts=[]
    ids={(d['sourceDocument'],d['startLine'],d['endLine']):d['id'] for d in index['documents']}
    for n,u in enumerate(units):
        assert parts[u['document']]=='train';text=u['text'];assert sha(text.encode())==u['textSha256']
        source_id=ids[(u['document'],u['startLine'],u['endLine'])]
        rng=random.Random(int(sha(('1529|'+source_id).encode())[:16],16))
        positions=list(range(1,min(len(text)-1,96)+1));rng.shuffle(positions);accepted=0
        for cut in positions:
            prefix=encode_stream(text[:cut],tok);suffix=encode_stream(text[cut:],tok)
            if len(prefix)+1>224:continue
            full=[SPECIALS['bos']]+prefix+suffix+[SPECIALS['eos']]
            assert b''.join(bytes.fromhex(tok['bytes'][t]) for t in full[1:-1])==text.encode()
            assert all(t>=6 for t in full[1:-1])
            offset=len(values);values.extend(full);prefix_length=len(prefix)+1;end=min(len(full),prefix_length+32)
            uid=source_id+':boundary-focus:'+str(cut)
            index['rows'].append(dict(document=u['document'],unit=uid,site=u['site'],variant='boundary-focus',offset=offset,length=end,prefixLength=prefix_length,start=0,end=end))
            index['documents'].append(dict(id=uid,sourceDocument=u['document'],site=u['site'],offset=offset,length=len(full),characters=len(text),utf8Bytes=len(text.encode()),textSha256=u['textSha256'],startLine=u['startLine'],endLine=u['endLine'],variant='boundary-focus',cutCharacters=cut,supervisedContinuationTokens=end-prefix_length,originalBytesPreserved=True))
            cuts.append(dict(unit=source_id,view=uid,document=u['document'],cutCharacters=cut,prefixTokens=len(prefix),supervisedContinuationTokens=end-prefix_length,sourceTextSha256=u['textSha256']))
            accepted+=1
            if accepted==4:break
        assert accepted==4
        if n%500==0:print(json.dumps(dict(units=n+1,total=len(units),focusedViews=len(cuts))),flush=True)
    if sys.byteorder!='little':values.byteswap()
    (out/'train.tokens.bin').write_bytes(values.tobytes());index['tokensSha256']=sha((out/'train.tokens.bin').read_bytes())
    index['unit']='Canonical full chains plus TRAIN-only raw Unicode prefix/suffix views. Focused rows label at most32 suffix tokens; canonical rows retain all targets. Only true chain boundaries carry BOS/EOS.'
    write(out/'train.index.json',index);write(out/'boundary-cuts.json',cuts)
    for part in ['validation','test']:
        for ext in ['tokens.bin','index.json']:shutil.copyfile(source/f'{part}.{ext}',out/f'{part}.{ext}')
    shutil.copyfile(source/'tokenizer.json',out/'tokenizer.json')
    data=read(source/'data.json')
    write(out/'data.json',dict(**data,parentDataSha256=sha((source/'data.json').read_bytes()),rawUnitsSha256=sha((PARENT/'units.json').read_bytes()),boundaryCutsSha256=sha((out/'boundary-cuts.json').read_bytes()),preparerSourceSha256=sha(pathlib.Path(__file__).read_bytes()),seed=1529,trainingViews={'canonical':.5,'boundaryFocus':.5},focusedViews=len(cuts),focusedLabelTokens=sum(c['supervisedContinuationTokens'] for c in cuts),allCanonicalTargetsRetained=True,heldFilesByteIdentical=True,newSourceDocuments=0,teacherProse=False,qaInstruction=False,note='Repeated original TRAIN bytes, not additional independent text. No vocab fitting, synthetic EOS, output repair or TEST generation. Each focused row supervises at most32 suffix tokens and masks its original prefix.'))
    print(json.dumps(dict(prepared=True,focusedViews=len(cuts),newSourceDocuments=0,heldFilesByteIdentical=True)),flush=True)
if __name__=='__main__':main()
