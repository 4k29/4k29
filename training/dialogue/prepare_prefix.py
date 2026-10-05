"""Training-only numeric BPE, structural Japanese questions and references.

Existing audits are development diagnostics. No external model supplies labels,
tokenizer rules or weights. Source articles retain their existing partitions.
"""
import collections
import argparse
import copy
import functools
import hashlib
import json
import pathlib
import re
import unicodedata
from tokenizer import SPECIALS,fit_fast,encode_stream
from stream_windows import windows
HERE=pathlib.Path(__file__).resolve().parent
parser=argparse.ArgumentParser();parser.add_argument('--clarify-references',action='store_true');args=parser.parse_args()
stem='prefix-corrected' if args.clarify_references else 'prefix'
base=json.loads((HERE/'continuous-corpus.json').read_text())
rows=[copy.deepcopy(r) for r in base['rows'] if r['intent']!='addition']
answers={r['intent']:r['answer'] for r in rows if r['partition']=='train'}
semantics={r['intent']:r['semantic'] for r in rows if r['partition']=='train'}
normalize=lambda q:unicodedata.normalize('NFKC',q).lower()
def input_key(q,history):return json.dumps([normalize(q),[(normalize(t['question']),t['answer']) for t in history]],ensure_ascii=False)
inputs={input_key(r['question'],r['history']) for r in rows}
old_audits=[json.loads((HERE/name).read_text()) for name in ['fresh-probe.json','fresh-audit.json','binding-audit.json','continuous-audit.json'] if (HERE/name).exists()]
old_inputs={input_key(r['question'],r['history']) for a in old_audits for r in a['rows']}
def add(intent,q,answer,group,partition='train',history=None,kind='profile',semantic=None):
    history=history or [];key=input_key(q,history)
    if key in inputs or key in old_inputs:return
    inputs.add(key);rows.append(dict(id='prefix:'+str(len(rows)),intent=intent,group='prefix:'+group,partition=partition,kind=kind,question=normalize(q),history=history,answer=answer,factIds=[],semantic=semantic or semantics.get(intent,dict(subject='owner',attribute=intent))))
def family(intent,questions,answer=None,kind='profile'):
    for i,q in enumerate(questions):add(intent,q,answer or answers[intent],intent+':'+str(i),'train' if i<len(questions)-4 else 'validation' if i<len(questions)-2 else 'test',kind=kind)

# Full clauses specify both codec and ANC state rather than a field keyword only.
for codec in ['AAC','LDAC']:
    for state,verbs in [('on',['ANCを有効にする','ノイズキャンセリングを使う','ノイキャンを入れる']),('off',['ANCを無効にする','ノイズキャンセリングを使わない','ノイキャンを切る'])]:
        intent='headphones-battery-'+codec.lower()+'-'+state
        questions=[f'Headphone1で{codec}を選び、{v}と何時間聴ける？' for v in verbs]
        questions += [f'{codec}接続で{v}とき、Nothing Headphone (1)の電池持ちは？' for v in verbs]
        questions += [f'Nothing Headphone1は{codec}で再生し、{v}場合に最大何時間持つ？' for v in verbs]
        questions += [f'{v}設定のHeadphone (1)を{codec}で聴くときの再生時間は？' for v in verbs]
        family(intent,questions)
family('headphone-spec',['Headphone1の仕様全体を一段落で教えて','Nothing Headphone (1)の主な性能をまとめて','ヘッドホンのHeadphone1について、複数の仕様をまとめて知りたい','Headphone (1)はどんな製品か、性能も含めて説明して','Headphone1の特徴と仕様をひとまとめにして','NothingのHeadphone1は何に対応しているかまとめて','Headphone1について、全般的な仕様を紹介して','Headphone (1)の性能をまとめた説明がほしい','Headphone1の主要スペックを文章にまとめて','Nothing Headphone1の仕様を総合的に説明して','Headphone1という製品を性能込みで紹介して','Nothing Headphone (1)の特徴とスペックを一緒に聞かせて'])

# Missing categories must not inherit a known device merely through 聴く/機種.
unknown='その情報は分かりません。'
for noun,verbs in [('アーティスト',['よく聴く','気に入っている','普段聴く']),('曲',['よく聴く','好きな','気に入っている']),('パソコン',['普段使う','愛用する','使っている']),('スマートフォン',['普段使う','愛用する','使っている']),('映画',['好きな','気に入っている','よく観る'])]:
    questions=[f'{v}{noun}の名前を教えて' for v in verbs]+[f'{noun}は何が好きか聞かせて',f'あなたの{noun}の名前が知りたい',f'普段の{noun}について、名前を聞いてもいい？',f'{noun}の好みはどんなもの？',f'{noun}を名前で紹介してもらえる？']
    for i,q in enumerate(questions):add('unknown-category',q,unknown,f'unknown:{noun}:{i}','train' if i<4 else 'validation' if i<6 else 'test',kind='unknown',semantic=dict(subject='unverified',attribute='unknown'))

# Match morning/evening greetings instead of teaching こんにちは for every hour.
for r in rows:
    if r['intent']=='greeting':
        time='evening' if 'こんばんは' in r['question'] else 'morning' if 'おはよう' in r['question'] else 'day'
        word={'evening':'こんばんは','morning':'おはよう','day':'こんにちは'}[time]
        r['answer']=word+'。何について知りたい？';r['semantic']=dict(subject='conversation',attribute='greeting-'+time)
for time,word in [('day','こんにちは'),('evening','こんばんは'),('morning','おはよう')]:
    questions=[f'{word}、質問してもいい？',f'{word}。少し聞きたいことがあります。',f'{word}、ちょっと話したいです',f'{word}。よろしく。',f'{word}、聞きたいことがあるんだけど',f'{word}。話せるかな？',f'{word}、少し質問があります。',f'{word}。質問をしても大丈夫？']
    for i,q in enumerate(questions):add('greeting-'+time,q,word+'。何について知りたい？',f'greeting:{time}:{i}','train' if i<4 else 'validation' if i<6 else 'test',kind='dialogue',semantic=dict(subject='conversation',attribute='greeting-'+time))

# Ask about first and last topics; named history questions and brief/full answers
# vary independently, including gratitude and irrelevant owner/hobby turns.
for domain,pair,field in [('drama',['mer','vivant'],'actor'),('drama',['mer','vivant'],'station'),('product',['headphones','favorite-kyu'],'weight')]:
    names={'mer':'MER','vivant':'VIVANT','headphones':'Headphone1','favorite-kyu':'kyu camera'}
    descriptions={'mer':answers['mer'],'vivant':answers['vivant'],'headphones':answers['headphone-spec'],'favorite-kyu':answers['favorite-kyu-weight']}
    noun='ドラマ' if domain=='drama' else '製品';label={'actor':'主演','station':'放送局と枠','weight':'重さ'}[field]
    for order in [pair,pair[::-1]]:
        for first in [True,False]:
            subject=order[0 if first else 1];intent=subject+'-'+field
            references=['最初の','先に出た','一つ目の','初めに出た' if args.clarify_references else '前の'] if first else ['最後の','後に出た','二つ目の','直前の']
            questions=[f'{ref}{noun}の{label}は？' for ref in references]+[f'{ref}挙げた{noun}について、{label}を教えて' for ref in ['先に','初めに','後から','最後に'] if (first and ref in ['先に','初めに']) or (not first and ref in ['後から','最後に'])]
            questions += [f'この会話で{ref}紹介した{noun}の{label}を確認したい' for ref in (['先に','一番初めに'] if first else ['あとで','一番最後に'])]
            questions += [f'{ref}話題にした{noun}の{label}を聞かせて' for ref in (['最初に','一番先に' if args.clarify_references else '前に'] if first else ['二番目に','最後に'])]
            for layout in range(4):
                history=[dict(question=f'{names[s]}について教えて。',answer=descriptions[s] if layout%2==0 else names[s]+'です。') for s in order]
                if layout>=1:history.insert(0,dict(question='どんな立場の人？',answer=answers['role']))
                if layout>=2:history.insert(2,dict(question='趣味も紹介して。',answer=answers['hobbies']))
                if layout>=3:history.append(dict(question='説明ありがとう。',answer=answers['thanks']))
                for i,q in enumerate(questions):add('reference-'+intent,q,answers[intent],f'reference:{domain}:{field}:{order}:{first}:{layout}:{i}','train' if i<len(questions)-4 else 'validation' if i<len(questions)-2 else 'test',history=history,kind='context',semantic=semantics[intent])

# Same unordered operands have one partition, including their reversed order.
arithmetic=[]
for a in range(21):
    for b in range(21):
        lo,hi=sorted([a,b]);bucket=int(hashlib.sha256(f'prefix-unordered-addition:{lo}:{hi}'.encode()).hexdigest()[:8],16)%10
        partition='validation' if bucket==8 else 'test' if bucket==9 else 'train'
        answer=f'{a}+{b}={a+b}なので、合わせて{a+b}個です。'
        forms=[f'{a}個と{b}個を合わせると何個？',f'{a}個に{b}個を足すといくつ？',f'{a}個を持ち、さらに{b}個もらいました。合計は？',f'{a}個を持っていて、{b}個を受け取りました。何個になる？',f'りんごが{a}個、みかんが{b}個です。全部で何個？',f'最初に{a}個あり、あとで{b}個増えました。全部でいくつ？',f'{a}個あるところへ{b}個を追加したら、全部で何個？',f'{a}個を用意し、{b}個を加えました。合計何個ですか？',f'{a}個の品物と{b}個の品物を一緒にすると何個？',f'{a}個ある物に{b}個の物を足した合計は？',f'{a}個を持ち、{b}個をもらうと全部で何個になる？',f'{a}個に{b}個が追加されたとき、全部の数はいくつ？']
        chosen=forms[:8] if partition=='train' else forms[8:10] if partition=='validation' else forms[10:]
        for i,q in enumerate(chosen):add('addition',q,answer,f'addition:{lo}:{hi}',partition,kind='reasoning',semantic=dict(subject='provided-facts',attribute='addition'))
        arithmetic.append(dict(a=a,b=b,partition=partition))

documents=[]
for name in ['web','mdn']:documents.extend(json.loads(line) for line in (HERE/(name+'-language-documents.jsonl')).read_text().splitlines())
old_meta={d['id']:d for d in base['provenance']['documents']}
texts={}
for key in ['pretraining','pretrainingValidation','pretrainingTest']:
    by_doc=collections.defaultdict(list)
    for frame in base[key]:by_doc[frame['document']].extend(frame['tokens'][frame['prefixLength']:])
    for identity,tokens in by_doc.items():texts[identity]=bytes.fromhex(''.join(base['tokenizer']['bytes'][t] for t in tokens[:-1])).decode('utf-8')
# fit_fast sees only training texts; validation/test strings never supply rules.
fit_texts=[texts[d['id']] for d in old_meta.values() if d['partition']=='train']
for r in rows:
    if r['partition']!='train':continue
    fit_texts += [normalize(r['question']),r['answer']]
    for t in r['history']:fit_texts += [normalize(t['question']),t['answer']]
# Increase counts for observed training-only identifiers/numbers, not a fixed
# vocabulary list. Names should not lose their first letters merely because
# long Japanese phrases dominate byte-pair frequencies. No audit text is read.
fragments=collections.Counter(fragment for r in rows if r['partition']=='train' for text in [normalize(r['question']),r['answer']] for fragment in re.findall(r'[A-Za-z][A-Za-z_-]*|[0-9]+',text) if len(fragment)>1)
for fragment,count in fragments.items():fit_texts.extend([fragment]*(16*count))
tokenizer=fit_fast(fit_texts,merges=1536,numeric_boundaries=True)
@functools.lru_cache(maxsize=30000)
def encoded(text):return encode_stream(text,tokenizer)
def prefix(q,history):
    tokens=[SPECIALS['bos']]
    for t in history:tokens += [SPECIALS['user']]+encoded(normalize(t['question']))+[SPECIALS['assistant']]+encoded(t['answer'])+[SPECIALS['turn']]
    return tokens+[SPECIALS['user']]+encoded(normalize(q))+[SPECIALS['assistant']]
kept=[];skipped=[]
for r in rows:
    p=prefix(r['question'],r['history']);tokens=p+encoded(r['answer'])+[SPECIALS['eos']]
    if len(tokens)>255:skipped.append(dict(id=r['id'],length=len(tokens)));continue
    r.update(tokens=tokens,prefixLength=len(p));kept.append(r)
counts=collections.Counter(tuple(r['semantic'].values()) for r in kept if r['partition']=='train');unknown_count=sum(r['kind']=='unknown' and r['partition']=='train' for r in kept)
for r in kept:
    scale=8 if r['intent']=='addition' else 2 if r['kind']=='context' else 0.5 if r['kind']=='web-qa' else 1
    r['weight']=8/unknown_count if r['kind']=='unknown' else scale/counts.get(tuple(r['semantic'].values()),1)
language={p:[] for p in ['train','validation','test']};document_meta=[]
for d in old_meta.values():
    text=texts[d['id']];assert hashlib.sha256(text.encode()).hexdigest()==d['textSha256']
    frames=windows(text,tokenizer,d['id'],maximum_input=160,lookback=16)
    for frame in frames:
        frame['weight']=1/len(frames)
        if d['id'].startswith('mdn:'):frame.update(license='CC BY-SA 4.0',sourceUrl=d['url'])
    language[d['partition']].extend(frames);document_meta.append(dict(d,frames=len(frames),tokens=sum(len(f['tokens'])-f['prefixLength'] for f in frames)))
result=dict(schemaVersion=5,tokenizer=tokenizer,rows=kept,pretraining=language['train'],pretrainingValidation=language['validation'],pretrainingTest=language['test'],provenance=dict(baseCorpusSha256=base['sourceSha256'],documents=document_meta,mdnDefinitions=base['provenance']['mdnDefinitions'],sourceManifests=base['provenance']['sourceManifests'],arithmeticPairs=arithmetic,excludedSources=['Wikipedia','external pretrained weights','generative AI APIs'],tokenizer='New own training-only BPE, 1536 merges, maximum12 bytes; ASCII digit runs never merge with words or units. Observed training QA identifiers/numbers add16 times their count as fitting fragments; no reserved/predefined word tokens.',diagnostics='All earlier audits, including continuous100, are development diagnostics. Fresh audit must freeze before training.',license=base['provenance']['license']))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
if args.clarify_references:
    result.pop('sourceSha256');result['provenance']['referenceClarification']='Replace first-topic 前の/前に with explicit 初めに出た/一番先に. The original prefix corpus is a pilot with ambiguous references.'
    result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/(stem+'-corpus.json')).write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
manifest=dict(sourceSha256=result['sourceSha256'],partitions=dict(collections.Counter(r['partition'] for r in kept)),vocabulary=len(tokenizer['bytes']),maxSequence=max(len(r['tokens']) for r in kept),rawFrames={p:len(language[p]) for p in language},skipped=skipped)
(HERE/(stem+'-data.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))
