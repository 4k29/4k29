"""Raw-only continuation curriculum: complete attributed source paragraphs.
TRAIN-only stochastic own BPE views teach subword continuation. Never rewrites
sentences, injects QA/grammar golds, refits a tokenizer or alters held openings.
"""
import argparse,array,collections,hashlib,heapq,json,pathlib,random,re,sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[2]/'dialogue'))
from tokenizer import SPECIALS,encode_stream
ROOT=pathlib.Path(__file__).resolve().parent

def read(p):return json.loads(p.read_text())
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def encode_dropout(text,tok,rng,probability):
    """Our adjacent BPE with stochastic merge omission, no outside vocabulary."""
    if not 0<=probability<=1:raise ValueError('Invalid merge dropout')
    values=[b+6 for b in text.encode()];n=len(values)
    if not n:return []
    ranks={(a,b):(i,c) for i,(a,b,c) in enumerate(tok['merges'])};before=list(range(-1,n-1));after=list(range(1,n))+[-1];alive=[True]*n;queue=[]
    def add(left):
        if left<0 or not alive[left] or after[left]<0:return
        right=after[left];pair=(values[left],values[right])
        if pair in ranks:
            rank,c=ranks[pair];heapq.heappush(queue,(rank,left,right,*pair,c))
    for i in range(n-1):add(i)
    while queue:
        _,left,right,a,b,c=heapq.heappop(queue)
        if not alive[left] or not alive[right] or after[left]!=right or values[left]!=a or values[right]!=b:continue
        if probability and rng.random()<probability:continue
        values[left]=c;alive[right]=False;after[left]=after[right]
        if after[right]>=0:before[after[right]]=left
        add(before[left]);add(left)
    return [t for t,keep in zip(values,alive) if keep]

def usable_paragraph(text):
    p=text.strip()
    if len(p)<40 or p[-1:] not in '。！？」':return False
    if len(re.findall(r'[ぁ-ゖァ-ヺ一-龯]',p))/len(p)<.25:return False
    if re.search(r'参考資料|相談電話|電話番号|お問い合わせ|お問合せ|消費者の部屋|^出典[：:]|^資料[：:]|Copyright|All Rights|ブラウザー互換性一覧表|^更新日|^担当',p,re.I):return False
    if re.search(r'0\d{1,4}[-ー]\d{1,4}[-ー]\d{3,4}',p):return False
    # Retain standalone complete quotation paragraphs, not split open quotations.
    if p.count('「')!=p.count('」') or p.count('（')!=p.count('）'):return False
    return True

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--merges',type=int,required=True);args=parser.parse_args()
    docs=[json.loads(s) for s in (ROOT/'documents.jsonl').read_text().splitlines()];parts={r['document']:r['partition'] for r in read(ROOT/'split.json')['assignments']};original=ROOT/f'bpe-{args.merges}';tok=read(original/'tokenizer.json');out=ROOT/f'paragraph-bpe-{args.merges}';out.mkdir(exist_ok=True);(out/'tokenizer.json').write_bytes((original/'tokenizer.json').read_bytes())
    source_sha=sha((ROOT/'documents.jsonl').read_bytes());stats={};selections=[];rejected=collections.Counter()
    for part in ['train','validation','test']:
        values=array.array('I');rows=[];units=[];unique_chars=0;unique_bytes=0;unitcount=0
        for doc in docs:
            if parts[doc['id']]!=part:continue
            for line,text in enumerate(doc['text'].splitlines()):
                if not usable_paragraph(text):rejected[part]+=1;continue
                p=text.strip();body_sha=sha(p.encode());unitcount+=1;unique_chars+=len(p);unique_bytes+=len(p.encode())
                selections.append(dict(document=doc['id'],partition=part,line=line,site=doc['site'],sourceTextSha256=doc['textSha256'],paragraphSha256=body_sha,characters=len(p),utf8Bytes=len(p.encode()),normalization='strip paragraph-layout whitespace only; no words changed'))
                probabilities=[0,.15,.3] if part=='train' else [0]
                for probability in probabilities:
                    seed=int(sha((str(829)+'|'+doc['id']+'|'+str(line)+'|'+str(probability)).encode())[:16],16)
                    encoded=encode_dropout(p,tok,random.Random(seed),probability)
                    assert b''.join(bytes.fromhex(tok['bytes'][t]) for t in encoded)==p.encode()
                    if not probability:assert encoded==encode_stream(p,tok)
                    full=[SPECIALS['bos']]+encoded+[SPECIALS['eos']];offset=len(values);values.extend(full);start=0;covered=[];unit=doc['id']+':paragraph:'+str(line)+':dropout:'+str(probability)
                    while start<len(full)-1:
                        end=min(start+257,len(full));prefix=1 if start==0 else 32
                        rows.append(dict(document=doc['id'],unit=unit,site=doc['site'],variant=probability,offset=offset+start,length=end-start,prefixLength=prefix,start=start,end=end))
                        covered.extend(full[start+prefix:end])
                        if end==len(full):break
                        start=end-32
                    assert covered==full[1:]
                    units.append(dict(id=unit,sourceDocument=doc['id'],site=doc['site'],offset=offset,length=len(full),characters=len(p),utf8Bytes=len(p.encode()),textSha256=body_sha,variant=probability,line=line))
        if sys.byteorder!='little':values.byteswap()
        path=out/f'{part}.tokens.bin';path.write_bytes(values.tobytes());write(out/f'{part}.index.json',dict(dtype='uint32-little-endian',context=256,lookback=32,documents=units,rows=rows,tokensSha256=sha(path.read_bytes()),unit='One complete original source paragraph; BOS/EOS only at true paragraph-text boundaries. Long paragraphs retain masked overlap, no invented mid-sentence EOS.'))
        stats[part]=dict(sourceDocuments=len({u['sourceDocument'] for u in units}),uniqueParagraphs=unitcount,uniqueSourceCharacters=unique_chars,uniqueSourceUtf8Bytes=unique_bytes,views=len(units),viewUtf8Bytes=sum(u['utf8Bytes'] for u in units),windows=len(rows),targetTokens=sum(u['length']-1 for u in units),tokensSha256=sha(path.read_bytes()))
    write(out/'paragraphs.json',selections)
    report=dict(schemaVersion=1,sourceSha256=source_sha,splitSha256=sha((ROOT/'split.json').read_bytes()),tokenizerSha256=sha((out/'tokenizer.json').read_bytes()),tokenizerFittedAgain=False,vocabulary=len(tok['bytes']),merges=args.merges,context=256,lookback=32,rawNextTokenOnly=True,paragraphSelectionsSha256=sha((out/'paragraphs.json').read_bytes()),stats=stats,seed=829,trainingViews=dict(canonical=.5,mergeDropout015=.25,mergeDropout030=.25),rejectedLines=dict(rejected),note='VALIDATION exposed layout/heading/contact repetition and broken completions inside BPE pieces. Select complete existing paragraphs and omit merges stochastically only in TRAIN, never add invented prose, profile QA, language corrections, teacher answers or outside weights. Round2 held document assignments and 24 new TEST openings stay frozen. Paragraph EOS is a true paragraph-text-unit end, not an artificial stop inside a sentence; it differs from whole-book/document EOS in the prior experiment. Expanded TRAIN views repeat identical source bytes; do not count them as new unique raw prose.')
    write(out/'data.json',report);print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
