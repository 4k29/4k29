"""Fit own Unicode character assembly rules from TRAIN only; preserve raw text.

Retains the own byte-BPE representation/decoder interface. No word merges,
external vocabulary, output filtering, teacher text or QA records.
"""
import array,collections,hashlib,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parent;PARENT=ROOT.parent/'round3'
sys.path.insert(0,str(ROOT.parent.parent/'dialogue'))
from tokenizer import SPECIALS,encode_stream
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,separators=(',',':'))+'\n')
def main():
    if (ROOT/'preparation.json').exists():raise ValueError('Prepared data is immutable; use a new experiment')
    units=read(PARENT/'units.json');train=[u for u in units if u['partition']=='train']
    counts=collections.Counter(c for u in train for c in u['text']);prefixes=collections.Counter()
    for c,frequency in counts.items():
        b=c.encode()
        for n in range(2,len(b)+1):prefixes[b[:n]]+=frequency
    vocab=[b'']*6+[bytes([i]) for i in range(256)];ids={b:i for i,b in enumerate(vocab) if b};rules=[]
    for n in [2,3,4]:
        for b in sorted((b for b in prefixes if len(b)==n),key=lambda b:(-prefixes[b],b)):
            left=ids[b[:-1]];right=ids[b[-1:]];token=len(vocab);vocab.append(b);ids[b]=token;rules.append([left,right,token])
    tok=dict(schemaVersion=1,specials=SPECIALS,bytes=[b.hex() for b in vocab],merges=rules,maxPieceBytes=4,unicodeCharacterAssembly=True,wordMerges=0,characterTypes=len(counts),trainingCharacters=sum(counts.values()),note='Own TRAIN-derived Unicode character assembly; rank by prefix length then TRAIN frequency/bytes. Retains byte fallback and all vocabulary at inference; no learned outside tokenizer, word merges or output filter.')
    glyphs={c:ids[c.encode()] for c in counts};cache={}
    for c,t in glyphs.items():assert encode_stream(c,tok)==[t]
    def encode(text):
        values=[]
        for c in text:
            if c in glyphs:values.append(glyphs[c])
            else:
                if c not in cache:cache[c]=encode_stream(c,tok)
                values.extend(cache[c])
        return values
    directory=ROOT/f'unicode-bpe-{len(rules)}';directory.mkdir(exist_ok=True);write(directory/'tokenizer.json',tok)
    write(ROOT/'character-frequencies.json',[dict(character=c,frequency=n,token=glyphs[c]) for c,n in sorted(counts.items())])
    stats={}
    for part in ['train','validation','test']:
        values=array.array('I');documents=[];rows=[];unknown=collections.Counter()
        selected=[u for u in units if u['partition']==part]
        for n,u in enumerate(selected):
            encoded=encode(u['text']);assert b''.join(vocab[t] for t in encoded)==u['text'].encode()
            if n%max(1,len(selected)//32)==0:assert encoded==encode_stream(u['text'],tok)
            if part=='train':assert len(encoded)==len(u['text'])
            unknown.update(c for c in u['text'] if c not in glyphs)
            full=[SPECIALS['bos']]+encoded+[SPECIALS['eos']];offset=len(values);values.extend(full);start=0;covered=[];uid=u['document']+':chain:'+str(u['startLine'])
            while start<len(full)-1:
                end=min(start+257,len(full));prefix=1 if start==0 else 32
                rows.append(dict(document=u['document'],unit=uid,site=u['site'],variant=0,offset=offset+start,length=end-start,prefixLength=prefix,start=start,end=end))
                covered.extend(full[start+prefix:end])
                if end==len(full):break
                start=end-32
            assert covered==full[1:]
            documents.append(dict(id=uid,sourceDocument=u['document'],site=u['site'],offset=offset,length=len(full),characters=len(u['text']),utf8Bytes=len(u['text'].encode()),textSha256=u['textSha256'],startLine=u['startLine'],endLine=u['endLine']))
        if sys.byteorder!='little':values.byteswap()
        path=directory/f'{part}.tokens.bin';path.write_bytes(values.tobytes())
        write(directory/f'{part}.index.json',dict(rows=rows,documents=documents,tokensSha256=sha(path),unit='Exact original chains; TRAIN tokenizes one observed Unicode character per token, plus true boundary BOS/EOS. Unknown held characters retain unmodified byte fallback.'))
        stats[part]=dict(units=len(documents),windows=len(rows),targetTokens=sum(u['length']-1 for u in documents),utf8Bytes=sum(u['utf8Bytes'] for u in documents),unknownCharacterTypes=len(unknown),unknownCharacterOccurrences=sum(unknown.values()))
        print(json.dumps(dict(partition=part,**stats[part])),flush=True)
    meta=dict(sourceSha256=sha(PARENT/'documents.jsonl'),splitSha256=sha(PARENT/'split.json'),rawUnitsSha256=sha(PARENT/'units.json'),tokenizerSha256=sha(directory/'tokenizer.json'),characterFrequenciesSha256=sha(ROOT/'character-frequencies.json'),preparerSourceSha256=sha(pathlib.Path(__file__)),merges=len(rules),vocabulary=len(vocab),unicodeCharacterAssembly=True,wordMerges=0,trainCharacterTypes=len(counts),trainingCharacterCount=sum(counts.values()),previousWeightsNotAllowed=True,externalTokenizer=False,rawNextTokenOnly=True,stats=stats)
    write(directory/'data.json',meta);write(ROOT/'preparation.json',meta)
    print(json.dumps(dict(prepared=True,vocabulary=len(vocab),assemblyRules=len(rules),trainCharacterTypes=len(counts),wordMerges=0)),flush=True)
if __name__=='__main__':main()
