"""Original paragraph bytes only; independent BPE across TRAIN-only cuts.

Cuts teach partial-word continuation without changing generated output, adding
teacher prose, inserting mid-sentence EOS or fitting any vocabulary again.
"""
import array,hashlib,json,pathlib,random,shutil,sys
ROOT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent.parent/'dialogue'))
from tokenizer import encode_stream,SPECIALS
def read(p):return json.loads(p.read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
    original=ROOT/'paragraph-bpe-8192';out=ROOT/'prefix-bpe-8192';out.mkdir(exist_ok=True)
    tok=read(original/'tokenizer.json');shutil.copyfile(original/'tokenizer.json',out/'tokenizer.json')
    data=read(original/'data.json');index=read(original/'train.index.json');raw=(original/'train.tokens.bin').read_bytes();assert sha(raw)==index['tokensSha256']
    values=array.array('I');values.frombytes(raw)
    if sys.byteorder!='little':values.byteswap()
    docs={d['id']:d for d in map(json.loads,(ROOT/'documents.jsonl').read_text().splitlines())};parts={d['document']:d['partition'] for d in read(ROOT/'split.json')['assignments']};selections=[s for s in read(original/'paragraphs.json') if s['partition']=='train'];cuts=[];rows=index['rows'];units=index['documents']
    for n,s in enumerate(selections):
        assert parts[s['document']]=='train';p=docs[s['document']]['text'].splitlines()[s['line']];assert sha(p.strip().encode())==s['paragraphSha256']
        rng=random.Random(int(sha(('1229|'+s['document']+'|'+str(s['line'])).encode())[:16],16));positions=sorted(rng.sample(range(1,min(len(p)-1,96)+1),4))
        for cut in positions:
            encoded=encode_stream(p[:cut],tok)+encode_stream(p[cut:],tok)
            assert b''.join(bytes.fromhex(tok['bytes'][t]) for t in encoded)==p.encode()
            full=[SPECIALS['bos']]+encoded+[SPECIALS['eos']];offset=len(values);values.extend(full);start=0;covered=[];unit=s['document']+':paragraph:'+str(s['line'])+':prefix-cut:'+str(cut)
            while start<len(full)-1:
                end=min(start+257,len(full));prefix=1 if start==0 else 32
                rows.append(dict(document=s['document'],unit=unit,site=s['site'],variant='prefix-cut',offset=offset+start,length=end-start,prefixLength=prefix,start=start,end=end))
                covered.extend(full[start+prefix:end])
                if end==len(full):break
                start=end-32
            assert covered==full[1:]
            units.append(dict(id=unit,sourceDocument=s['document'],site=s['site'],offset=offset,length=len(full),characters=len(p),utf8Bytes=len(p.encode()),textSha256=sha(p.encode()),variant='prefix-cut',line=s['line'],cutCharacters=cut,originalLayoutPreserved=True))
            cuts.append(dict(document=s['document'],line=s['line'],cutCharacters=cut,normalizedParagraphSha256=s['paragraphSha256'],rawParagraphSha256=sha(p.encode()),originalBytesPreserved=True,originalLayoutPreserved=True))
        if n%2000==0:print(json.dumps(dict(paragraphs=n+1,total=len(selections),addedViews=len(cuts))),flush=True)
    if sys.byteorder!='little':values.byteswap()
    tokenfile=out/'train.tokens.bin';tokenfile.write_bytes(values.tobytes());index['tokensSha256']=sha(tokenfile.read_bytes());index['unit']='Complete original paragraph, with four extra TRAIN-only independently encoded prefix/suffix views. One true paragraph BOS/EOS; no separator or EOS at the internal cut.';write(out/'train.index.json',index)
    for part in ['validation','test']:
        for suffix in ['tokens.bin','index.json']:shutil.copyfile(original/f'{part}.{suffix}',out/f'{part}.{suffix}')
    shutil.copyfile(original/'paragraphs.json',out/'paragraphs.json');write(out/'prefix-cuts.json',cuts)
    report={**data,'trainingViews':dict(canonical=.5,mergeDropout015=.1,mergeDropout030=.1,prefixCut=.3),'prefixCutSource':'Same attributed TRAIN paragraphs including original layout, four seeded independent BPE boundaries at Unicode positions1..min(length-1,96). No words rewritten, vocabulary fitting, QA, teacher output or inference repair. Held canonical files byte-identical. Extra views repeat the same source bytes. Unique source character/byte stats retain the parent normalized paragraph convention; view stats include original layout.','prefixCutSeed':1229,'prefixCutsSha256':sha((out/'prefix-cuts.json').read_bytes()),'stats':{**data['stats'],'train':{**data['stats']['train'],'views':len(units),'windows':len(rows),'targetTokens':sum(u['length']-1 for u in units),'viewUtf8Bytes':sum(u['utf8Bytes'] for u in units),'tokensSha256':index['tokensSha256']}}}
    write(out/'data.json',report);print(json.dumps(dict(addedViews=len(cuts),trainingWindows=len(rows),heldFilesCopiedUnchanged=True)),flush=True)
if __name__=='__main__':main()
