"""Freeze and check new own Python/JS text encoding; no model/updates/answers."""
import argparse,collections,datetime,hashlib,json,pathlib,subprocess,sys,time
from new_tokenizer import Encoder
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[2]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def key(s):return hashlib.sha256(s.encode()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def prepare():
    out=H/'tokenizer-parity';plan_path=H/'TOKENIZER_PARITY_PLAN.json'
    if out.exists()or plan_path.exists():raise ValueError('Refuse to overwrite existing parity freeze')
    out.mkdir();base=H/'data';data=read(base/'data.json');tokpath=ROOT/data['tokenizerPath'];tok=read(tokpath)
    assert sha(tokpath)==data['tokenizerSha256'];enc=Encoder(tok);pieces=[bytes.fromhex(x)for x in tok['bytes']]
    utterances={};selected=[]
    for part in ['train','dev']:
        docs=[json.loads(line)for line in (base/(part+'.docs.jsonl')).read_text().splitlines()]
        utterances[part]=[{'document':d['id'],'ordinal':u['ordinal'],'text':u['text']}for d in docs for u in d['utterances']]
        ranked=sorted(utterances[part],key=lambda r:key('v2-tokenizer-parity-v1|'+part+'|'+r['document']+'|'+str(r['ordinal'])))
        for r in ranked[:256]:selected.append(dict(r,source=part,id=part+'-sha256-'+str(len(selected)).zfill(3)))
    unknown=set(read(base/'unknown-character-audit.json')['dev']);assert len(unknown)==19
    for c in sorted(unknown):
        r=next(r for r in utterances['dev']if c in r['text'])
        selected.append(dict(r,source='dev-unknown-glyph-first-utterance',fallbackCharacter=c,
            id='fallback-u'+format(ord(c),'x')))
    rows=[]
    for r in selected:
        tokens=enc(r['text']);raw=b''.join(pieces[t]for t in tokens)
        assert raw==r['text'].encode('utf8')and raw.decode('utf8')==r['text']
        rows.append(dict(r,expectedTokens=tokens,utf8Hex=raw.hex()))
    assert len(rows)==531
    input_path=out/'inputs.json';write(input_path,{'scope':'Only original human utterances and deterministic encoder expectations; no generated answers',
        'selection':'SHA256(v2-tokenizer-parity-v1|partition|document|ordinal) ascending256 per partition, plus first original DEV utterance for each of19 unknown glyph types',
        'unknownDevGlyphTypes':sorted(unknown),'rows':rows})
    code=[pathlib.Path(__file__),H/'tokenizer-parity.mjs',H/'new_tokenizer.py',ROOT/'training/dialogue/tokenizer.py',
        ROOT/'training/language/round10/word_bpe.py',ROOT/'training/dialogue/tokenizer.mjs',ROOT/'training/dialogue/bpe_heap.mjs']
    sources=[base/'data.json',base/'train.docs.jsonl',base/'dev.docs.jsonl',base/'unknown-character-audit.json',tokpath,input_path]
    plan={'schemaVersion':1,'status':'FROZEN_TOKENIZER_PARITY_ONLY','frozenAtUtc':now(),'cases':531,'trainCases':256,'devCases':256,'unknownGlyphCases':19,
        'exactTokenIdsRequired':True,'exactUtf8RoundtripRequired':True,'unknownDevGlyphTypes':sorted(unknown),
        'algorithm':'Existing own tokenizer.mjs createTokenizer.encode adjacent-heap versus new_tokenizer.Encoder',
        'specials':'Rename exactly six API names to pad,bos,eos,user,assistant,turn; IDs0..5 and byteOffset6 unchanged; no prompt normalization called',
        'codeSha256':{str(p.relative_to(ROOT)):sha(p)for p in code},'inputSha256':{str(p.relative_to(ROOT)):sha(p)for p in sources},
        'modelObjectsConstructed':0,'optimizerUpdates':0,'generatedAnswers':0,'modelWeightsRead':False,
        'limits':'Encoder tokenization equality only; not dialogue quality, new generation or full-model inference parity',
        'execution':'Run is allowed only after this exact plan/input/code freeze; a mismatch fails without changing encoder/model/data.'}
    write(plan_path,plan)
    write(out/'freeze-receipt.json',{'frozenAtUtc':plan['frozenAtUtc'],'planSha256':sha(plan_path),'inputsSha256':sha(input_path),
        'nodeExecuted':False,'optimizerUpdates':0,'generatedAnswers':0})
    print(json.dumps({'status':'FROZEN','planSha256':sha(plan_path),'inputsSha256':sha(input_path),'cases':len(rows)}))
def run(a):
    plan_path=H/'TOKENIZER_PARITY_PLAN.json';out=H/'tokenizer-parity';plan=read(plan_path)
    if sha(plan_path)!=a.plan_sha256:raise ValueError('Explicit frozen plan hash mismatch')
    for group in ['codeSha256','inputSha256']:
        for p,h in plan[group].items():
            if sha(ROOT/p)!=h:raise ValueError('Frozen code/input changed: '+p)
    if (out/'receipt.json').exists()or(out/'node-results.json').exists():raise ValueError('Refuse repeated execution')
    inputs=read(out/'inputs.json');start=time.monotonic();started=now();tokpath=ROOT/read(H/'data/data.json')['tokenizerPath']
    command=['node',str(H/'tokenizer-parity.mjs'),'--tokenizer',str(tokpath),'--inputs',str(out/'inputs.json'),'--output',str(out/'node-results.json')]
    result=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=60)
    (out/'node.log').write_text(result.stdout+result.stderr)
    if result.returncode!=0:raise RuntimeError('JS encoder failed; retain artifacts and do not change test conditions')
    js=read(out/'node-results.json');assert len(js['rows'])==len(inputs['rows'])==531
    byid={r['id']:r for r in js['rows']};fallback=set();failures=[]
    for r in inputs['rows']:
        s=byid[r['id']]
        if s['actualTokens']!=r['expectedTokens']or s['utf8Hex']!=r['utf8Hex']or s['reconstructedUtf8Hex']!=r['utf8Hex']:
            failures.append(r['id'])
        if 'fallbackCharacter'in r:fallback.add(r['fallbackCharacter'])
    assert fallback==set(plan['unknownDevGlyphTypes'])and not failures
    unchanged=all(sha(ROOT/p)==h for group in ['codeSha256','inputSha256']for p,h in plan[group].items())
    assert unchanged and sha(plan_path)==a.plan_sha256
    receipt={'status':'PASS','planSha256':a.plan_sha256,'frozenAtUtc':plan['frozenAtUtc'],'startedAtUtc':started,'finishedAtUtc':now(),
        'elapsedSeconds':time.monotonic()-start,'cases':531,'trainCases':256,'devCases':256,'unknownGlyphCases':19,
        'unknownGlyphTypesCovered':len(fallback),'unknownGlyphTypes':sorted(fallback),'tokenIdMismatches':0,'utf8RoundtripFailures':0,
        'sourceCounts':dict(collections.Counter(r['source']for r in inputs['rows'])),'uniqueOriginalUtteranceInputs':len({(r['document'],r['ordinal'])for r in inputs['rows']}),
        'codeInputAndTokenizerUnchanged':unchanged,'nodeVersion':js['nodeVersion'],'pythonVersion':sys.version,
        'nodeResultsSha256':sha(out/'node-results.json'),'inputsSha256':sha(out/'inputs.json'),
        'modelObjectsConstructed':0,'optimizerUpdates':0,'generatedAnswers':0,'modelWeightsRead':False,
        'scope':'Actual own JS adjacent-heap encoder matches own Python fresh glyph+word encoder on fixed human utterances; does not evaluate language ability'}
    write(out/'receipt.json',receipt);print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','run']);p.add_argument('--plan-sha256');a=p.parse_args()
    if a.stage=='prepare':prepare()
    else:run(a)
