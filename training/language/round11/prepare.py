"""Original-byte-preserving segmentation views, using only our existing vocabulary."""
import array, hashlib, json, pathlib, random, sys
ROOT = pathlib.Path(__file__).resolve().parent
PARENT = ROOT.parent / 'round10'
sys.path.append(str(PARENT))
from word_bpe import apply_rules
sys.path.append(str(ROOT.parents[1] / 'dialogue'))
from tokenizer import SPECIALS, encode_stream

def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v): p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def segmented(text, glyph_encode, rules, rng):
    """Cut only between Unicode characters; concatenate without invented boundaries."""
    out=[]; start=0; cuts=[]
    while start<len(text):
        end=min(len(text),start+rng.randint(8,24))
        out.extend(apply_rules(glyph_encode(text[start:end]),rules)); cuts.append(end); start=end
    return out,cuts

def main():
    policy=read(ROOT/'policy.json')
    for name, expected in policy['sourceHashes'].items():
        assert sha(PARENT/name)==expected, name
    for name, expected in policy['codeHashes'].items(): assert sha(ROOT/name)==expected,name
    units=read(PARENT/'units.json'); tok=read(PARENT/'word-bpe-512/tokenizer.json')
    glyph=read(PARENT / policy['glyphTokenizer'])
    rules=tok['merges'][len(glyph['merges']):]; vocab=[bytes.fromhex(x) for x in tok['bytes']]
    frequencies=read(PARENT/'character-frequencies.json'); ids={r['character']:r['token'] for r in frequencies}; cache={}
    def glyph_encode(text):
        result=[]
        for char in text:
            if char in ids: result.append(ids[char])
            else:
                if char not in cache: cache[char]=encode_stream(char,glyph)
                result.extend(cache[char])
        return result
    directory=ROOT/'multiview'; assert not directory.exists(),'Use a new experiment; frozen streams cannot be overwritten'
    directory.mkdir(); (directory/'tokenizer.json').write_bytes((PARENT/'word-bpe-512/tokenizer.json').read_bytes()); statistics={}
    # TEST text is not encoded or emitted by this experiment.
    for part in ['train','validation']:
        selected=[u for u in units if u['partition']==part]; values=array.array('I'); rows=[]; documents=[]; stats={}
        for u in selected:
            glyph_ids=glyph_encode(u['text']); canonical=apply_rules(glyph_ids,rules)
            seed=int(hashlib.sha256(('2049|'+u['document']+'|'+str(u['startLine'])).encode()).hexdigest(),16)
            cut_ids,cuts=segmented(u['text'],glyph_encode,rules,random.Random(seed))
            for variant,encoded in [(0,canonical),(1,glyph_ids),(2,cut_ids)]:
                assert b''.join(vocab[t] for t in encoded)==u['text'].encode('utf-8')
                uid=u['document']+':chain:'+str(u['startLine'])+':view:'+str(variant)
                full=[SPECIALS['bos']]+encoded+[SPECIALS['eos']]; offset=len(values);values.extend(full); start=0; covered=[]
                while start<len(full)-1:
                    end=min(start+257,len(full)); prefix=1 if start==0 else 32
                    rows.append(dict(document=u['document'],unit=uid,site=u['site'],variant=variant,offset=offset+start,length=end-start,prefixLength=prefix,start=start,end=end))
                    covered.extend(full[start+prefix:end])
                    if end==len(full): break
                    start=end-32
                assert covered==full[1:]
                documents.append(dict(id=uid,sourceDocument=u['document'],site=u['site'],variant=variant,offset=offset,length=len(full),characters=len(u['text']),utf8Bytes=len(u['text'].encode()),textSha256=u['textSha256'],startLine=u['startLine'],endLine=u['endLine'],characterCuts=cuts if variant==2 else []))
        if sys.byteorder!='little': values.byteswap()
        path=directory/f'{part}.tokens.bin';path.write_bytes(values.tobytes())
        write(directory/f'{part}.index.json',dict(rows=rows,documents=documents,tokensSha256=sha(path)))
        for variant in range(3):
            ds=[d for d in documents if d['variant']==variant]
            stats[str(variant)]=dict(units=len(ds),windows=sum(r['variant']==variant for r in rows),targetTokens=sum(d['length']-1 for d in ds),utf8Bytes=sum(d['utf8Bytes'] for d in ds))
        statistics[part]=stats; print(json.dumps(dict(partition=part,views=stats)),flush=True)
    write(directory/'data.json',dict(stats=statistics,sourceSha256=sha(PARENT/'documents.jsonl'),splitSha256=sha(PARENT/'split.json'),tokenizerSha256=sha(directory/'tokenizer.json'),rawUnitsSha256=sha(PARENT/'units.json'),policySha256=sha(ROOT/'policy.json'),testRead=False,validationStatus='Previously inspected development data; not fresh unseen evaluation'))
if __name__=='__main__': main()
