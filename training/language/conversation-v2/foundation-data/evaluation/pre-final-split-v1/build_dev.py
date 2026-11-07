"""Build DEV only from finalized article/component split and original human QA.

No model call, generated reference, TEST fetch or tokenizer fitting. Source text
is retained byte-for-byte. Input labels are evaluator serialization, not human
utterances or a claim that the current human-A/B model has AI-role training.
"""
import argparse, collections, hashlib, json, pathlib, sys, unicodedata
HERE=pathlib.Path(__file__).resolve().parent
BASE=HERE.parents[1]
sys.path.insert(0,str(BASE))
from new_tokenizer import Encoder

def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def hashkey(s):return hashlib.sha256(s.encode()).hexdigest()
def category(question):
    if any(t in question for t in ['なぜ','何故','どうして','理由']):return 'reason'
    if any(t in question for t in ['比べ','最も','一番','どちら','より多','より長','どっち']):return 'comparison'
    if any(t in question for t in ['どのよう','どういう','どんな','意味','とは何']):return 'explanation'
    return 'question-answer'
def prompt(context,question):return '資料：\n'+context+'\n質問：'+question
def eligible_prefix(enc,context,question,max_input=192):
    tokens=[1,3]+enc(prompt(context,question))+[2,4]
    return tokens if len(tokens)<=max_input else None
def split_lookup(record):
    rows=record['articles'] if isinstance(record,dict) else record
    if isinstance(rows,dict):return {unicodedata.normalize('NFC',k):v for k,v in rows.items()}
    return {unicodedata.normalize('NFC',r['title']):r for r in rows if r.get('source','jaquad')=='jaquad'}
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def build(a):
    source=read(a.source_manifest);split=split_lookup(read(a.article_splits))
    tokpath=BASE/'data/tokenizer.json';tok=read(tokpath);enc=Encoder(tok)
    pieces=[bytes.fromhex(x)for x in tok['bytes']]
    quality=read(HERE/'source-quality-issues.json');excluded=set(quality['excludeQuestionIds'])
    candidates=[];paragraphs={};all_train_contexts=set();all_train_questions=set();train_components=set();all_dev_articles=set();rejected=collections.Counter()
    for shard in source['shards']:
        raw=pathlib.Path(shard['rawPath'])
        if sha(raw)!=shard['sha256']:raise ValueError('Raw source SHA mismatch')
        for article in read(raw)['data']:
            title=article['title'];key=unicodedata.normalize('NFC',title)
            info=split[key]
            if info['split']=='train':train_components.add(info['component'])
            for ordinal,p in enumerate(article['paragraphs']):
                context=p['context'];context_sha=hashkey(context)
                if info['split']=='train':
                    all_train_contexts.add(context_sha)
                    all_train_questions.update(''.join(unicodedata.normalize('NFC',q['question']).split())for q in p['qas'])
                if info['split']!='dev':continue
                all_dev_articles.add(key)
                paragraph_key=(key,context_sha)
                paragraphs[paragraph_key]=dict(title=title,context=context,paragraphOrdinal=ordinal,
                    article=info,sourceUrl=shard['url'],sourceRawSha256=shard['sha256'])
                for q in p['qas']:
                    answers=q['answers']
                    if not answers or any(context[z['answer_start']:z['answer_start']+len(z['text'])]!=z['text'] for z in answers):
                        rejected['answer-offset-invalid']+=1;continue
                    prefix=eligible_prefix(enc,context,q['question'])
                    if prefix is None:rejected['full-source-prefix-exceeds192']+=1;continue
                    gold=enc(answers[0]['text'])
                    if len(prefix)+len(gold)>256:rejected['reference-score-does-not-fit256']+=1;continue
                    if not gold or any(t<6 for t in gold):rejected['empty-or-special-reference']+=1;continue
                    if len(gold)>=64:rejected['reference-exceeds-fixed-generation-budget']+=1;continue
                    assert b''.join(pieces[t]for t in gold)==answers[0]['text'].encode()
                    candidates.append(dict(q=q,title=title,key=key,article=info,context=context,
                        prefixTokens=prefix,goldTokens=gold,sourceUrl=shard['url'],sourceRawSha256=shard['sha256'],
                        paragraphOrdinal=ordinal,category=category(q['question']),contextSha256=context_sha))
    clean=[]
    for row in candidates:
        if ''.join(unicodedata.normalize('NFC',row['q']['question']).split())in all_train_questions:
            rejected['exact-normalized-question-seen-in-train']+=1
        else:clean.append(row)
    candidates=clean
    candidates.sort(key=lambda x:hashkey('foundation-human-dev-v1|'+x['q']['id']))
    chosen=[];used=set()
    # Seek scarce categories first. Coverage remains reported actual, never invented.
    for wanted,limit in [('reason',8),('comparison',8),('explanation',8),('question-answer',24)]:
        n=0
        for row in candidates:
            if row['category']!=wanted or row['key']in used:continue
            chosen.append(row);used.add(row['key']);n+=1
            if n==limit:break
    for row in candidates:
        if len(chosen)>=48:break
        if row['key']not in used:chosen.append(row);used.add(row['key'])
    chosen=chosen[:48]
    initial_ids=[r['q']['id']for r in chosen]
    quarantined=[r for r in chosen if r['q']['id']in excluded]
    chosen=[r for r in chosen if r['q']['id']not in excluded]
    rejected['source-semantic-quality-quarantine']=len(quarantined)
    write(HERE/'selection-history.json',dict(initialSelectionQuestionIds=initial_ids,
        initialSelectionCount=len(initial_ids),removedQuestionIds=[r['q']['id']for r in quarantined],
        replacementsAdded=False,reason='Source-semantic defects found before any model call; no refill or source correction',
        modelCallsBeforeFilter=0,sourceSemanticAuditSha256=sha(HERE/'source-quality-issues.json')))
    write(HERE/'quarantined-source-cases.json',dict(trainingAllowed=False,benchmarkAllowed=False,
        originalTextAndLabelsUnchanged=True,cases=[dict(questionId=r['q']['id'],title=r['title'],family=r['article']['family'],
            component=r['article']['component'],split=r['article']['split'],sourceUrl=r['sourceUrl'],sourceRawSha256=r['sourceRawSha256'],
            context=r['context'],question=r['q']['question'],originalHumanAnswers=r['q']['answers'])for r in quarantined]))
    rows=[]
    for row in chosen:
        q=row['q'];rows.append(dict(id='foundation-human-dev-'+q['id'],kind='human-grounded-qa',
            split='DEV',trainingAllowed=False,contentRequired=True,authorship='Original JaQuAD human-annotated question/answer; Wikipedia context authorship requires source audit',
            knowledgeMode='provided-context',externalKnowledgeRequired=False,
            answerability='Answer spans occur in full provided source; semantic answerability needs independent reading',
            category=quality['categoryOverrides'].get(q['id'],row['category']),selectionCandidateTag=row['category'],
            categoryAssignment='Lexical candidate selection with pre-output Codex source-reading corrections; native-human validation pending',
            articleTitle=row['title'],family=row['article']['family'],component=row['article']['component'],
            priorCandidateViewed=row['article'].get('priorCandidateViewed',False),
            source=dict(dataset='JaQuAD',revision=source['revision'],partition='upstreamTRAIN',license='CC-BY-SA-3.0',
                url=row['sourceUrl'],rawSha256=row['sourceRawSha256'],questionId=q['id'],paragraphOrdinal=row['paragraphOrdinal']),
            context=row['context'],contextSha256=row['contextSha256'],question=q['question'],
            humanAnswers=q['answers'],questionType=q.get('question_type'),
            inputText=prompt(row['context'],q['question']),prefixTokens=row['prefixTokens'],
            goldTokens=row['goldTokens'],referenceAnswer=q['answers'][0]['text'],
            referencePolicy='Human extractive span is TF/coverage diagnostic, not a unique natural reply or generated training target',
            evaluationRequirement='Answer the specific question from supplied evidence; acknowledgement or question echo alone fails. Full grammar, relevance, coherence, no harmful repetition/drift, and appropriate EOS required.'))
    prose=[]
    for key,row in sorted(paragraphs.items(),key=lambda x:hashkey('foundation-prose-dev-v1|'+x[0][0]+'|'+x[0][1])):
        context=row['context'];boundaries=[i+1 for i,c in enumerate(context)if c in '。！？']
        for boundary in boundaries:
            first=context[:boundary];rest=context[boundary:]
            if not first.strip() or not rest.strip():continue
            prefix=[1,3]+enc(first);gold=enc(rest)
            if 16<=len(prefix)<=128 and 8<=len(gold)<128 and len(prefix)+len(gold)<=256:
                prose.append(dict(id='foundation-prose-dev-'+hashkey(row['title']+'|'+key[1])[:16],kind='human-prose-continuation',
                    split='DEV',trainingAllowed=False,authorship='Verbatim Wikipedia-derived JaQuAD context; human/bot source authorship unverified',
                    category='prose-continuation',knowledgeMode='language-continuation',externalKnowledgeRequired=False,
                    articleTitle=row['title'],family=row['article']['family'],component=row['article']['component'],
                    source=dict(dataset='JaQuAD',revision=source['revision'],partition='upstreamTRAIN',license='CC-BY-SA-3.0',
                        url=row['sourceUrl'],rawSha256=row['sourceRawSha256'],paragraphOrdinal=row['paragraphOrdinal']),
                    context=context,inputText=first,referenceAnswer=rest,prefixTokens=prefix,goldTokens=gold,
                    contentRequired=True,maxNewTokens=128,evaluationRequirement='Continue the whole text coherently in natural Japanese; exact original continuation is not required.'))
                break
        if len(prose)==12:break
    families={r['family']for r in rows+prose}
    assert all(r['contextSha256']not in all_train_contexts for r in rows)
    assert not {r['component']for r in rows+prose}&train_components
    result=dict(status='DEV prepared; no inference or training, not a sealed TEST',schemaVersion=1,
        createdBy='Codex builder selecting original source; no model-generated reference answers',
        tokenizerSha256=sha(tokpath),sourceManifestSha256=sha(a.source_manifest),articleSplitSha256=sha(a.article_splits),
        sourceSemanticAuditSha256=sha(HERE/'source-quality-issues.json'),
        promptContract='BOS1,human-role3,evaluator-authored supplied-evidence wrapper,EOS2,human-role4; diagnostic serialization only, no claim of learned AI-role semantics',
        generation=dict(method='full-vocabulary-greedy',qaMaxNewTokens=64,proseMaxNewTokens=128,context=256,eos=2,filters=False,repair=False,crop=False),
        cases=rows,proseCases=prose)
    write(HERE/'human-dev.json',result)
    audit=dict(passed=True,humanQaCases=len(rows),proseContinuationCases=len(prose),uniqueFamilies=len(families),
        eligibleHumanQa=len(candidates),sourceDevArticles=len(all_dev_articles),rejected=dict(rejected),
        actualCategories=dict(collections.Counter(r['category']for r in rows)),oneQaPerArticle=len({r['articleTitle']for r in rows})==len(rows),
        trainExactContextOverlap=0,trainExactNormalizedQuestionOverlap=0,trainComponentOverlap=0,sourceSplitFrozenBeforeSelection=True,
        originalReferenceOffsetsChecked=True,fullOriginalContexts=True,noSourceParaphrase=True,
        humanNativeEvaluationCompleted=False,sealedTestCreated=False,sealedTestRead=False,optimizerUpdates=0,modelCalls=0,
        limitations=['DEV source is upstream TRAIN held out before this new corpus; source inspection is not sealed evaluation',
                    'Source-license/third-party quoting review and independent source-semantic reading remain pending',
                    'Short complete contexts selected to fit existing256/64 contract; long-context coverage is limited',
                    'Human-QA corpus does not supply human daily advice or conditional-request gold replies'])
    write(HERE/'human-dev-audit.json',audit);print(json.dumps(audit,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-manifest',type=pathlib.Path,required=True);p.add_argument('--article-splits',type=pathlib.Path,required=True);build(p.parse_args())
