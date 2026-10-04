"""Own tokenizer + document-disjoint Japanese next-token pretraining data.

Government text is attributable under recorded public-data terms. Wikipedia,
outside pretrained tokenizers/weights and generated AI answers are excluded.
"""
import copy
import hashlib
import json
import pathlib
import re
from tokenizer import fit,encode,prompt,SPECIALS

HERE=pathlib.Path(__file__).resolve().parent
def sentences(text):
    return [s.strip() for s in re.findall(r'[^。！？\n]+[。！？]?|[^。！？\n]+$',text) if s.strip()]
def chunks(text,tokenizer,maximum=64):
    result=[];tokens=encode(text,tokenizer);start=0
    pieces=[bytes.fromhex(h) for h in tokenizer['bytes']]
    # Bound complete BPE spans, then retreat only if a token boundary falls in
    # the middle of a UTF-8 character. Re-encoding verifies the standalone span
    # fits, including changes in merge priority at its boundaries.
    while start<len(tokens):
        end=min(start+maximum,len(tokens))
        while end>start:
            try:part=b''.join(pieces[t] for t in tokens[start:end]).decode('utf-8')
            except UnicodeDecodeError:end-=1;continue
            if len(encode(part,tokenizer))<=maximum:break
            end-=1
        if end==start:raise ValueError('No complete Unicode span fits')
        result.append(part);start=end
    return result
def main():
    base=json.loads((HERE/'generalization-corpus.json').read_text())
    documents=[json.loads(line) for line in (HERE/'web-language-documents.jsonl').read_text().splitlines()]
    sources=json.loads((HERE/'web-language-sources.json').read_text())
    assert 'Wikipedia' in sources['excludedSources']
    assert {d['site'] for d in documents}=={'jma','maff'}
    rows=copy.deepcopy(base['rows']);raw=[];qa_count=0
    for document in documents:
        if hashlib.sha256(document['text'].encode()).hexdigest()!=document['textSha256']:raise ValueError('Source text changed')
        for block in document['blocks']:
            if block['tag'] in ['h1','h2','h3','p','li']:
                raw.append(dict(document=document['id'],partition=document['partition'],text=block['text']))
        if document['partition']!='train':continue
        question=None;used=0
        for block in document['blocks']:
            if block['tag'] in ['h1','h2']:
                question=block['text'] if re.search(r'[？?]|ですか|ください',block['text']) else None
            elif block['tag']=='p' and question:
                text=block['text'];question_copy=question;question=None
                if re.search(r'当庁|当省|私たち|気象庁では|農林水産省では|詳しくは|ご覧ください|リンク|次の|以下|下記|ホームページ|ページ|参照|例にします|○○|図を|表を',text):continue
                # A complete paragraph is the label. Cutting the first one or
                # two sentences can discard a condition or leave an example
                # unfinished; long passages remain raw-language data only.
                if not text.endswith('。') or len(text)>150:continue
                answer=text
                intent='web-qa-'+str(qa_count);qa_count+=1;used+=1
                for i,wrapper in enumerate(['{}','教えてほしい。{}','ねえ、{}','質問です。{}']):
                    rows.append(dict(id=f'{intent}:{i}',intent=intent,group=intent+':train',partition='train',kind='web-qa',question=wrapper.format(question_copy),answer=answer,history=[],factIds=[],sourceUrl=document['url'],sourceDocument=document['id'],weight=1))
                if used>=5:break
    fit_strings=[r['text'] for r in raw if r['partition']=='train']
    for row in rows:
        if row['partition']!='train':continue
        fit_strings.extend([row['question'],row['answer']])
        for turn in row['history']:fit_strings.extend([turn['question'],turn['answer']])
    tokenizer=fit(fit_strings,merges=1024)
    kept=[];skipped=[]
    for row in rows:
        prefix=prompt(row['question'],row['history'],tokenizer)
        row['prefixLength']=len(prefix);row['tokens']=prefix+encode(row['answer'],tokenizer)+[SPECIALS['eos']]
        if row['kind']=='web-qa' and len(row['tokens'])>127:skipped.append(row['id']);continue
        if len(row['tokens'])>127:raise ValueError('Existing QA no longer fits; never silently truncate')
        kept.append(row)
    rows=kept
    # One exact passage cannot cross raw-language splits through repeated
    # boilerplate. Remove duplicate text from validation/test, preserving train.
    raw.sort(key=lambda r: {'train':0,'validation':1,'test':2}[r['partition']])
    seen=set();raw_unique=[]
    for r in raw:
        if r['text'] in seen:continue
        seen.add(r['text']);raw_unique.append(r)
    language={p:[] for p in ['train','validation','test']}
    for row in raw_unique:
        for text in chunks(row['text'],tokenizer):
            language[row['partition']].append(dict(text=text,document=row['document'],tokens=[SPECIALS['bos']]+encode(text,tokenizer)+[SPECIALS['eos']]))
    # Mix authored known-fact language with varied external explanatory prose.
    language['train'].extend(dict(text=r['text'],document='authored-train',tokens=[SPECIALS['bos']]+encode(r['text'],tokenizer)+[SPECIALS['eos']]) for r in base['pretraining'])
    counts={}
    for r in rows:
        if r['partition']=='train':counts[r['intent']]=counts.get(r['intent'],0)+1
    for r in rows:
        scale=4 if r['kind']=='unknown' else 0.5 if r['kind']=='web-qa' else 1
        r['weight']=scale/counts.get(r['intent'],1)
    result=dict(schemaVersion=3,tokenizer=tokenizer,rows=rows,pretraining=language['train'],pretrainingValidation=language['validation'],pretrainingTest=language['test'],provenance=dict(baseSourceSha256=base['sourceSha256'],webSourcesSha256=hashlib.sha256((HERE/'web-language-sources.json').read_bytes()).hexdigest(),excludedSources=sources['excludedSources'],labels='Authored approved profile/spec prose plus attributed full standalone source paragraphs as QA labels. Incomplete introductions, references and long answers are excluded. No external generative model, pretrained tokenizer or weights.',partition='Article-disjoint raw-language train/validation/test. Existing authored QA families retain their frozen partitions; web source QA labels are train-only. Exact raw passages deduplicated across partitions.',modifications='HTML prose already extracted with source notices. Own byte BPE fitted only on train strings. Text split on Unicode boundaries into at most 64 BPE token chunks; no unseen article text fits tokenizer.'))
    result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    (HERE/'web-curriculum-corpus.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    manifest=dict(sourceSha256=result['sourceSha256'],baseSourceSha256=base['sourceSha256'],rawSamples={p:len(language[p]) for p in language},qaPartitions={p:sum(r['partition']==p for r in rows) for p in ['train','validation','test']},webQATrainRows=sum(r['kind']=='web-qa' for r in rows),skippedWebRows=skipped,vocabulary=len(tokenizer['bytes']),maxSequence=max(len(r['tokens']) for r in rows+language['train']),excludedSources=sources['excludedSources'])
    (HERE/'web-curriculum-data.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest),flush=True)
if __name__=='__main__':main()
