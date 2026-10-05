"""Revise approved own-profile labels and add complete source paragraphs.

Uses the previous OWN byte BPE unchanged for numerical weight continuation.
No generated teacher answers, outside vocabulary, weights, API or Wikipedia.
Fresh controls are prepared by a separate script before any new fitting.
"""
import collections,copy,functools,hashlib,json,pathlib,re,unicodedata
from tokenizer import SPECIALS,encode_stream,prompt
from stream_windows import windows

HERE=pathlib.Path(__file__).resolve().parent
CONTEXT=512
def sha(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def normal(text):return unicodedata.normalize('NFKC',text).lower()
def main():
    base=json.loads((HERE/'switch-corpus.json').read_text())
    profile_path=HERE.parents[1]/'docs/profile.json'
    profile=json.loads(profile_path.read_text());facts=profile['facts'];by_id={f['id']:f for f in facts}
    favorite_facts=([f for f in facts if f['ja']['relation']=='interest' and not f.get('interestOnly')]
                    +[f for f in facts if f['ja']['relation']=='favoriteThing']
                    +[f for f in facts if f['ja']['relation']=='favorite'])
    interest_facts=[f for f in facts if f['topic']=='interests']
    short=lambda f:f['ja'].get('shortName',f['ja']['value'])
    favorites='、'.join(short(f) for f in favorite_facts)
    interests='、'.join(short(f) for f in interest_facts)+'に関心があります。'
    detail=('Nothing Headphone (1)は、透明なイヤーカップとアルミの質感が特徴のヘッドホンです。'
            '40mmダイナミックドライバーを搭載し、Bluetooth 5.3、AAC・SBC・LDAC、IP52に対応しています。'
            '重さは329gで、USB-Cと3.5mmでの有線接続も可能です。'
            '最大再生時間は、AAC接続でANCオン35時間・オフ80時間、LDAC接続でオン30時間・オフ54時間です。')
    brief='Nothing Headphone (1)は、透明なイヤーカップが特徴で、40mmダイナミックドライバーを搭載し、Bluetooth 5.3とIP52に対応するヘッドホンです。'
    def wants_brief(q):
        if '詳しく聞く前に' in q:return True
        return bool(re.search(r'一言|ひとこと|一文|短く|簡単|簡潔|要点|brief|short',q,re.I)) and not re.search(r'詳しく|詳細|in detail',q,re.I)
    reps={}
    for r in base['rows']:
        if r['partition']=='train' and not r['history']:reps.setdefault(r['intent'],r)
    replacements={reps['favorites']['answer']:favorites,reps['headphone-spec']['answer']:detail}
    def current(text):
        for old,new in replacements.items():text=text.replace(old,new)
        return text
    rows=copy.deepcopy(base['rows']);revised=collections.Counter()
    for r in rows:
        new=current(r['answer'])
        if new!=r['answer']:revised[r['intent']]+=1;r['answer']=new
        if r['intent']=='favorites':r['factIds']=[f['id'] for f in favorite_facts]
        if r['intent']=='headphone-spec' and wants_brief(r['question']):r.update(intent='headphone-brief',answer=brief,semantic=dict(subject='headphones',attribute='description-brief'))
        for h in r['history']:
            h['answer']=current(h['answer'])
            if h['answer']==detail and wants_brief(h['question']):h['answer']=brief
    reps={}
    for r in rows:
        if r['partition']=='train' and not r['history']:reps.setdefault(r['intent'],r)
    targets={intent:r['answer'] for intent,r in reps.items()}
    targets['interests']=interests
    targets['headphone-brief']=brief
    targets.update({'interest-'+f['id']:short(f)+'に関心があります。' for f in interest_facts})
    targets['interest-hci']=by_id['hci']['ja']['value']+'に関心があります。'
    fragments={
      'favorites':['好きなもの','お気に入りのもの','気に入っているものの名前'],
      'interests':['興味のあるもの','関心のある分野','気になっているもの'],
      'headphone-spec':['Nothing Headphone (1)の特徴と仕様','Headphone1についての詳しい情報','Nothing Headphone1の概要'],
      'headphone-brief':['Headphone (1)の短い紹介','Headphone1の簡潔な特徴と仕様','Nothing Headphone (1)の要点'],
    }
    for f in interest_facts:
        fragments['interest-'+f['id']]=list(dict.fromkeys([short(f)]+f['aliases'][:2]))
    # Explicit detailed requests must beat an ownership answer. Brand questions
    # and category/count questions keep their separate approved label/intents.
    forms=[
      '{f}は？','{f}を教えて。','{f}について教えて。','{f}を聞かせて。',
      '質問です。{f}は何ですか。','{f}を知りたい。','{f}について少し教えて。',
      'いま知りたいのは{f}です。','{f}をもう一度教えて。','{f}について答えて。',
      '{f}って、どんなもの？','{f}のことを聞いていい？',
      '話題を変えて、{f}を教えて。','{f}の説明をお願い。','{f}について知りたいんだけど。',
      'ちょっと聞きたい。{f}はどう？','{f}を教えてもらってもいい？','{f}に関して答えてください。',
      '{f}に関心があるのか知りたい。','{f}について確認させて。',
      '聞きたいことは{f}です。','{f}について聞いてもよろしいですか。',
      '{f}を一言で答えると？','{f}に関して教えていただけますか。',
      '気になるので、{f}を説明して。','{f}を聞きたいです。',
      '{f}を答えてもらえるかな。','{f}について話せますか。',
      '{f}のことを教えてほしいです。','{f}を確認したいです。',
      '今度は{f}の話を聞かせて。','{f}を回答してもらえますか。',
    ]
    # Questions about names only must not ask for explanation/deep detail.
    bare={
      'favorites':['好きなものは何','好きなものだけ挙げて','好きなものの名前だけ教えて','何が好き？','お気に入りは何？'],
      'interests':['興味のあるものは何','何に興味がある？','関心のあるものは？','興味は何？'],
      'headphone-spec':['Nothing Headphone (1)について詳しく教えて','Headphone (1)のスペックは','nothing headphone1を詳しく説明して','Nothing Headphone1の特徴は？'],
      'headphone-brief':['Headphone (1)を一文で紹介して','Nothing Headphone1を短く紹介して','Headphone1の特徴と仕様を簡潔に教えて'],
    }
    for f in interest_facts:bare['interest-'+f['id']]=list(dict.fromkeys([short(f)]+f['aliases']))
    seen={(normal(r['question']),json.dumps(r['history'],ensure_ascii=False,sort_keys=True)) for r in rows}
    used_questions={normal(r['question']) for r in base['rows']}
    prior_audit_questions=set()
    for filename in ['switch-audit.json','prefix-audit.json','continuous-audit.json','fresh-probe.json','binding-audit.json','prefix-rollouts.json','switch-rollouts.json']:
        d=json.loads((HERE/filename).read_text())
        prior_audit_questions.update(normal(r['question']) for r in d.get('rows',[]))
        prior_audit_questions.update(normal(t['question']) for c in d.get('conversations',[]) for t in c['turns'])
    added=collections.Counter();conflicts=collections.Counter()
    histories=[[],*[ [dict(question=q,answer=targets[i])] for q,i in [('MERは？','mer'),('VIVANTは？','vivant'),('趣味は？','hobbies'),('何のイヤホンを使ってる？','audio'),('Tecircでは何をしている？','tecirc'),('先に好きなものを教えて。','favorites'),('名前は？','name'),('Headphone (1)の重さは？','headphones-weight')]]]
    histories.extend([[dict(question='先にHeadphone1を詳しく紹介して。',answer=detail)],
                      [dict(question='まず趣味を教えて。',answer=targets['hobbies']),dict(question='次はHeadphone1の詳しい特徴と仕様を教えて。',answer=detail)]])
    def add(intent,q,partition,family,history):
        q=normal(q)
        if not intent.startswith('interest-') and 'に関心があるのか知りたい' in q:conflicts['scope-changing-interest-wrapper']+=1;return
        if intent=='headphone-spec' and re.search(r'一言|ひとこと|一文|短く|簡単|簡潔|要点',q):conflicts['detail-with-brief-instruction']+=1;return
        if q in prior_audit_questions:return
        identity=(q,json.dumps(history,ensure_ascii=False,sort_keys=True))
        if identity in seen:return
        if q in used_questions:return
        if intent in reps:r=copy.deepcopy(reps[intent])
        else:r=dict(kind='profile',factIds=[f['id'] for f in interest_facts] if intent=='interests' else [intent.removeprefix('interest-')],semantic=dict(subject='owner' if intent=='interests' else intent.removeprefix('interest-'),attribute='interests' if intent=='interests' else 'interest'))
        r.update(id='owner-aligned:'+str(len(rows)),intent=intent,group='owner-aligned:form:'+family,question=q,answer=targets[intent],partition=partition,history=copy.deepcopy(history))
        rows.append(r);seen.add(identity);added[intent]+=1
    for intent,phrases in fragments.items():
        for index,form in enumerate(forms):
            partition='train' if index<24 else 'validation' if index<28 else 'test'
            for phrase in phrases:
                for history in histories:add(intent,form.format(f=phrase),partition,str(index),history)
        for q in bare[intent]:
            for history in histories:add(intent,q,'train','bare',history)
    tokenizer=copy.deepcopy(base['tokenizer'])
    @functools.lru_cache(maxsize=60000)
    def enc(text):return encode_stream(text,tokenizer)
    def make_prefix(q,history):
        result=[SPECIALS['bos']]
        for h in history:result+=[SPECIALS['user']]+enc(normal(h['question']))+[SPECIALS['assistant']]+enc(h['answer'])+[SPECIALS['turn']]
        return result+[SPECIALS['user']]+enc(normal(q))+[SPECIALS['assistant']]
    kept=[];skipped=[]
    for r in rows:
        prefix=make_prefix(r['question'],r['history']);full=prefix+enc(r['answer'])+[SPECIALS['eos']]
        if len(full)>=CONTEXT:skipped.append(dict(id=r['id'],intent=r['intent'],tokens=len(full)));continue
        r.update(tokens=full,prefixLength=len(prefix));kept.append(r)
    counts=collections.Counter(tuple(r['semantic'].values()) for r in kept if r['partition']=='train')
    unknown_count=sum(r['partition']=='train' and r['kind']=='unknown' for r in kept)
    for r in kept:
        scale=0.25 if r['intent']=='addition' else 1.5 if r['kind']=='context' else 0.5 if r['kind']=='web-qa' else 3 if r['intent'] in fragments else 1
        r['weight']=8/unknown_count if r['kind']=='unknown' else scale/counts.get(tuple(r['semantic'].values()),1)
    raw={p:copy.deepcopy(base[k]) for p,k in [('train','pretraining'),('validation','pretrainingValidation'),('test','pretrainingTest')]}
    docs=copy.deepcopy(base['provenance']['documents']);paragraph_counts={p:0 for p in raw};texts={}
    for p in raw:
        by_doc=collections.defaultdict(list)
        for r in raw[p]:by_doc[r['document']].extend(r['tokens'][r['prefixLength']:])
        for document,tokens in by_doc.items():texts[document]=bytes.fromhex(''.join(tokenizer['bytes'][t] for t in tokens[:-1])).decode('utf-8')
    assert all(hashlib.sha256(texts[d['id']].encode()).hexdigest()==d['textSha256'] for d in docs)
    # Keep government/MDN source text unchanged. Only the authored profile text
    # is brought up to date, with both old and new hashes recorded.
    for d in docs:
        if d.get('site')=='authored' or d['id']=='authored-train':
            before=texts[d['id']];after=current(before);texts[d['id']]=after
            if after!=before:
                d['parentTextSha256']=d['textSha256'];d['textSha256']=hashlib.sha256(after.encode()).hexdigest()
                raw[d['partition']]=[r for r in raw[d['partition']] if r['document']!=d['id']]
                frames=windows(after,tokenizer,d['id'],maximum_input=128,lookback=16)
                for r in frames:r['weight']=1/len(frames)
                raw[d['partition']].extend(frames)
    seen_raw=set()
    for partition in ['train','validation','test']:
        for d in [d for d in docs if d['partition']==partition]:
            spans=[]
            for paragraph in texts[d['id']].splitlines():
                if not paragraph.endswith('。') or len(paragraph)<25:continue
                tokens=enc(paragraph)
                if len(tokens)>192 or len(tokens)<12:continue
                if paragraph in seen_raw:continue
                seen_raw.add(paragraph);spans.append(paragraph)
            for paragraph in spans:
                r=dict(document=d['id'],tokens=[SPECIALS['bos']]+enc(paragraph)+[SPECIALS['eos']],prefixLength=1,weight=0.5/max(1,len(spans)),unit='complete-paragraph',paragraphSha256=hashlib.sha256(paragraph.encode()).hexdigest())
                if d['id'].startswith('mdn:'):r.update(license='CC BY-SA 4.0',sourceUrl=d['url'])
                raw[partition].append(r);paragraph_counts[partition]+=1
    own_text='\n'.join(targets[i] for i in fragments)
    own_id='owner-current-20261005'
    for i in fragments:raw['train'].append(dict(document=own_id,tokens=[SPECIALS['bos']]+enc(targets[i])+[SPECIALS['eos']],prefixLength=1,weight=0.5/len(fragments),unit='approved-owner-paragraph'))
    docs.append(dict(id=own_id,site='authored',partition='train',url=None,textSha256=hashlib.sha256(own_text.encode()).hexdigest(),characters=len(own_text),license='Author-approved profile prose; no external generated teacher',profileSha256=hashlib.sha256(profile_path.read_bytes()).hexdigest()))
    for d in docs:d['frames']=sum(r['document']==d['id'] for r in raw[d['partition']])
    provenance=copy.deepcopy(base['provenance']);provenance.update(parentCorpusSha256=base['sourceSha256'],context=CONTEXT,architectureChange=dict(extendedPositionEmbeddings=dict(parent=256,current=CONTEXT,initialization='Keep own selected positions0-255; new rows retain seed429 random initialization.')),currentProfileSha256=hashlib.sha256(profile_path.read_bytes()).hexdigest(),productDataSha256=hashlib.sha256((HERE.parent/'product-specifications.json').read_bytes()).hexdigest(),documents=docs,ownerAlignment='Approved current profile names/interestOnly distinction; distinct brief and detailed verified Headphone overview. Replace stale answers in targets and histories. New whole-question-form families split before fitting; earlier audits excluded from additions. Contradictory brief/detail or scope-changing wrappers excluded before fitting.',tokenizer='Unchanged own switch byte BPE, fitted on its original training strings only. No new fitting on validation/test or outside vocabulary.',rawParagraphs='Full sentence-ending source paragraphs at most192 own tokens, preserving whole paragraphs and source-page partitions; government/MDN text unchanged. Only authored stale labels updated. Extra owner-current prose is train only.',labels='Authored approved owner/profile/spec labels plus existing attributable source QA; no model-generated output used as a target.')
    result=dict(schemaVersion=7,tokenizer=tokenizer,rows=kept,pretraining=raw['train'],pretrainingValidation=raw['validation'],pretrainingTest=raw['test'],provenance=provenance)
    result['sourceSha256']=sha(result)
    (HERE/'owner-aligned-corpus.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    manifest=dict(sourceSha256=result['sourceSha256'],parentCorpusSha256=base['sourceSha256'],profileSha256=provenance['currentProfileSha256'],context=CONTEXT,partitions=dict(collections.Counter(r['partition'] for r in kept)),added=dict(added),revisedTargets=dict(revised),excludedContradictoryForms=dict(conflicts),skipped=skipped,rawFrames={p:len(raw[p]) for p in raw},completeParagraphFrames=paragraph_counts,vocabulary=len(tokenizer['bytes']),maximumFullSequence=max(len(r['tokens']) for r in kept),targets={i:targets[i] for i in fragments},favoriteFactIds=[f['id'] for f in favorite_facts],interestFactIds=[f['id'] for f in interest_facts],scope='Additional own learning on revised approved data; retained old diagnostics are not fresh tests.')
    (HERE/'owner-aligned-data.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k not in ['targets','skipped']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
