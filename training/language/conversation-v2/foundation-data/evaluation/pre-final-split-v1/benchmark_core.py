"""Read-only benchmark contracts, source checks and mechanical output inventory."""
import hashlib,json,pathlib,sys,unicodedata
HERE=pathlib.Path(__file__).resolve().parent
BASE=HERE.parents[1]
REPO=HERE.parents[4]
sys.path.insert(0,str(BASE))
from new_tokenizer import Encoder

def read(path):return json.loads(pathlib.Path(path).read_text())
def sha(path):return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()
def normalize_question(s):return ''.join(unicodedata.normalize('NFC',s).split())
def encode_history(history,encoder):
    if not history or any(not isinstance(x,str)or not x.strip()for x in history):raise ValueError('Nonempty complete diagnostic history required')
    prefix=[1];role=3
    for text in history:
        body=encoder(text)
        if not body or any(x<6 for x in body):raise ValueError('Original text must encode as ordinary tokens')
        prefix.extend([role]+body+[2]);role=7-role
    return prefix+[role]

def prepare_cases(human,synthetic,tokenizer):
    encoder=Encoder(tokenizer);pieces=[bytes.fromhex(x)for x in tokenizer['bytes']];rows=[]
    for source,kind,budget in [(human['cases'],'human-grounded-qa',64),(human['proseCases'],'human-prose-continuation',128)]:
        for c in source:
            row=dict(c);prefix=c['prefixTokens'];gold=c['goldTokens']
            if not prefix or prefix[:2]!=[1,3]or any(t<6 for t in gold):raise ValueError('Malformed frozen source prefix/reference')
            if b''.join(pieces[x]for x in gold)!=c['referenceAnswer'].encode('utf8'):raise ValueError('Original reference byte mismatch')
            if len(prefix)+len(gold)>256:raise ValueError('Full teacher-forced reference does not fit')
            row.update(kind=kind,maxNewTokens=budget,generationSupported=len(prefix)+budget<=256)
            rows.append(row)
    for c in synthetic['cases']:
        if c['referenceAnswer']is not None or c['humanReference']or c['trainingAllowed']:raise ValueError('Researcher proposals cannot become human/reference training data')
        row=dict(c);prefix=encode_history(c['history'],encoder)
        row.update(prefixTokens=prefix,maxNewTokens=64,generationSupported=len(prefix)+64<=256,goldTokens=None)
        rows.append(row)
    ids=[r['id']for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate benchmark IDs')
    return rows

def mechanical_summary(rows):
    valid=[r for r in rows if r['generationSupported']]
    return dict(totalCases=len(rows),supported=len(valid),unsupported=len(rows)-len(valid),
        eos=sum(r['generation']['eos']for r in valid),strictUtf8=sum(r['generation']['strictUtf8']for r in valid),
        nonEosSpecial=sum(r['generation']['nonEosContainsSpecialTokens']for r in valid),
        repeated4gram=sum(r['generation']['repeated4gram']is not None for r in valid),
        semanticSuccess=None,independentFullOutputReadingRequired=True,
        interpretation='Mechanical properties only; EOS/UTF8/NLL are not content or language success')

def check_final_split(human,split):
    source_rows=split['articles']if isinstance(split,dict)else split
    by_family={r['family']:r for r in source_rows};train_components={r['component']for r in source_rows if r['split']=='train'}
    for c in human['cases']+human['proseCases']:
        if c['family']not in by_family:raise ValueError('Benchmark family missing from final corpus split')
        actual=by_family[c['family']]
        if actual['split']!='dev' or actual['component']in train_components:raise ValueError('Benchmark source leaked into candidateTRAIN')
        if c['component']!=actual['component']:raise ValueError('Benchmark component changed; rebuild before freezing, not after output')
    return dict(passed=True,finalCandidateTrainComponentOverlap=0,
        allBenchmarkFamiliesRemainDev=True,sealedTestCreated=False,
        semanticFamilyLimit='Article + exact/normalized/near-paragraph connected components; no claim all semantic paraphrase families discovered')
