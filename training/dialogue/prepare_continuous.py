"""Real document endings, attributed MDN prose, richer context and reasoning.

All QA targets are approved facts, author-defined prose or exact synthetic
arithmetic. No model/API supplies labels or weights. Prior audits are diagnostic.
"""
import collections
import copy
import functools
import hashlib
import json
import pathlib
import re
import unicodedata
from tokenizer import SPECIALS,encode_stream
from stream_windows import windows
HERE=pathlib.Path(__file__).resolve().parent
base=json.loads((HERE/'binding-corpus.json').read_text());tokenizer=base['tokenizer']
rows=copy.deepcopy(base['rows']);answers={r['intent']:r['answer'] for r in rows if r['partition']=='train'}
unknown='その情報は分かりません。';skipped=[]
@functools.lru_cache(maxsize=20000)
def encoded(text):return encode_stream(text,tokenizer)
def prefix(q,history):
    tokens=[SPECIALS['bos']]
    for turn in history:
        tokens += [SPECIALS['user']]+encoded(unicodedata.normalize('NFKC',turn['question']).lower())
        tokens += [SPECIALS['assistant']]+encoded(turn['answer'])+[SPECIALS['turn']]
    return tokens+[SPECIALS['user']]+encoded(unicodedata.normalize('NFKC',q).lower())+[SPECIALS['assistant']]
inputs={tuple(r['tokens'][:r['prefixLength']]) for r in rows}
def add(intent,q,answer,family,partition='train',history=None,kind='profile',semantic=None):
    history=history or [];q=unicodedata.normalize('NFKC',q).lower();p=prefix(q,history)
    if tuple(p) in inputs:return
    tokens=p+encoded(answer)+[SPECIALS['eos']]
    if len(tokens)>255:skipped.append(dict(question=q,intent=intent,length=len(tokens)));return
    inputs.add(tuple(p));rows.append(dict(id='continuous:'+str(len(rows)),intent=intent,group='continuous:'+family,partition=partition,kind=kind,question=q,history=history,answer=answer,prefixLength=len(p),tokens=tokens,factIds=[],weight=1,semantic=semantic or dict(subject='owner',attribute=intent)))
def family(intent,answer,questions,kind='profile',semantic=None):
    for i,q in enumerate(questions):
        part='train' if i<len(questions)-4 else 'validation' if i<len(questions)-2 else 'test'
        add(intent,q,answer,intent+':'+str(i),part,kind=kind,semantic=semantic)

# Registration counts, not the unverified number of physical units owned.
for kind,name,count in [('audio','音響機器',3),('earphones','イヤホン',2),('headphones','ヘッドホン',1)]:
    family('count-'+kind,f'{count}機種です。',[f'使っている{name}の機種は何種類？',f'{name}は何機種使ってる？',f'使っている{name}の製品は何機種ある？',f'{name}の機種数を教えて',f'普段使っている{name}は何種類なの？',f'{name}の製品名は何種類挙げられる？',f'{name}の機種は全部でいくつ？',f'{name}について、使う機種の数を知りたい',f'{name}は合計何機種使っている？',f'{name}の種類の数を聞かせて',f'使っている{name}の機種数が知りたい',f'{name}の機種が何種類あるか教えて'],kind='reasoning',semantic=dict(subject='owner',attribute='count-'+kind))
family('drama-actor-comparison','主演は異なります。TOKYO MERは鈴木亮平さん、VIVANTは堺雅人さんです。',['MERとVIVANTの主演は同じ？','VIVANTとMERは同じ俳優が主演？','TOKYO MERとVIVANTの主演を比べて','MERとVIVANTはそれぞれ誰が主演？','2つのドラマは主演が違う？MERとVIVANT。','VIVANTとTOKYO MERの主演は異なる？','MERとVIVANTの主演に違いはある？','TOKYO MERとVIVANTを主演で比較して','VIVANTとMERの主演俳優を比較したい','TOKYO MERとVIVANTは主演が共通なの？','MERとVIVANTで主演を務める人は同じなのか教えて','VIVANTとTOKYO MERは主演が同一人物ですか'],kind='reasoning',semantic=dict(subject='comparison',attribute='actors'))
family('drama-station-comparison','どちらもTBSの日曜劇場ドラマです。',['MERとVIVANTの放送枠は同じ？','VIVANTとMERは同じテレビ局？','TOKYO MERとVIVANTの放送局を比べて','MERとVIVANTは両方TBS？','VIVANTとTOKYO MERはどちらも日曜劇場？','2つのドラマの放送枠は共通？MERとVIVANT。','MERとVIVANTの放送局に違いはある？','TOKYO MERとVIVANTは同じ枠で放送された？','MERもVIVANTもTBSの日曜劇場なの？','TOKYO MERとVIVANTは放送局が共通なの？','VIVANTとMERで放送枠は共通するのか教えて','TOKYO MERとVIVANTは同じ局の同じ枠ですか'],kind='reasoning',semantic=dict(subject='comparison',attribute='stations'))
family('weight-comparison','Nothing Headphone (1)のほうが重く、329gと115gで214gの差があります。',['Headphone1とkyu cameraはどちらが重い？','kyu cameraよりHeadphone (1)のほうが重い？','Nothing Headphone (1)とkyu cameraの重量を比較して','Headphone1とkyu cameraの重さは何グラム違う？','kyu cameraとHeadphone1の重さの差は？','Headphone (1)はkyu cameraに比べてどれくらい重い？','Headphone1とkyu cameraを重さで比べて','Nothing Headphone (1)とkyu cameraで重いのは？','kyu cameraとHeadphone (1)の重量差を知りたい','Headphone1とkyu cameraはどちらの重さが上？','Nothing Headphone1とkyu cameraの重さを比べてほしい','kyu cameraとNothing Headphone1の重いほうと差を教えて'],kind='reasoning',semantic=dict(subject='comparison',attribute='weight'))
family('bluetooth-comparison','どちらもBluetooth 5.3です。',['Headphone1とCMF BudsのBluetoothは同じ？','CMF BudsとHeadphone (1)のBluetoothを比べて','Nothing Headphone (1)とCMF Budsは同じBluetoothバージョン？','Headphone1もCMF BudsもBluetooth 5.3？','CMF BudsとHeadphone1のBluetoothに違いはある？','Headphone (1)とCMF BudsのBluetoothの版は？','Headphone1とCMF BudsのBluetoothは共通？','CMF BudsとNothing Headphone (1)のBluetoothを比較して','Headphone1とCMF BudsのBluetoothは同じバージョンなの？','CMF BudsとHeadphone (1)はBluetoothの版が共通なの？','Nothing Headphone1とCMF BudsをBluetoothの版で比べてほしい','CMF BudsとHeadphone1のBluetoothバージョンは一致しますか'],kind='reasoning',semantic=dict(subject='comparison',attribute='bluetooth'))
family('favorite-dramas','VIVANT、TOKYO MER',['好きなドラマの名前を教えて','お気に入りのドラマは？','どのドラマが好き？','好きなテレビドラマを挙げて','気に入っているドラマの名前は？','ドラマの中で好きなものを教えて','お気に入りのドラマ名を聞かせて','どんなドラマが好きなの？','好きなドラマを列挙してください','お気に入りのドラマはどれですか','ドラマで好きな作品名を教えてください','好きなテレビドラマの名称を聞かせて'])

# Unknown preference/device categories do not inherit the known favorites/gear.
for noun in ['食べ物','映画','小説','アーティスト','曲','レストラン','スマートフォン','パソコン','撮影用カメラ','学校名']:
    requests=['好きな{}は何？','お気に入りの{}を教えて','{}の好みを聞かせて','好きな{}の名前は？'] if noun in ['食べ物','映画','小説','アーティスト','曲','レストラン'] else ['使っている{}の名前は？','普段の{}を教えて','あなたの{}はどれ？','{}の名前を聞かせて']
    for i,form in enumerate(requests):add('unknown-extra',form.format(noun),unknown,'unknown-category:'+noun+':'+str(i),'train' if i<2 else 'validation' if i==2 else 'test',kind='unknown',semantic=dict(subject='unverified',attribute='unknown'))
for i,q in enumerate(['今この瞬間の東京の天気は？','いま東京は晴れていますか','現在の気温は何度ですか','今日の大阪は雨が降っていますか','明日の東京の降水確率は？','明日は大阪で傘が必要ですか','今の東京の空の様子を教えて','現在、名古屋で降っている雨は？']):add('unknown-live',q,unknown,'unknown-live:'+str(i),'train' if i<4 else 'validation' if i<6 else 'test',kind='unknown',semantic=dict(subject='unverified',attribute='unknown'))

# 2-4 turn histories with distractors and gratitude, including long descriptions.
topics=[('mer',answers['mer']),('vivant',answers['vivant']),('headphones',answers['headphone-spec']),('earphones-cmf','イヤホンはCMF Budsを使っています。'),('favorite-kyu',answers['kyu']),('hobbies',answers['hobbies'])]
followups={'mer':[('主演は誰？','mer-actor'),('そのドラマの主演は誰ですか？','mer-actor'),('今紹介したドラマの主演を教えて','mer-actor'),('最後に話したドラマで主演しているのは誰？','mer-actor')], 'vivant':[('主演は誰？','vivant-actor'),('そのドラマの主演は誰ですか？','vivant-actor'),('今紹介したドラマの主演を教えて','vivant-actor'),('最後に話したドラマで主演しているのは誰？','vivant-actor')], 'headphones':[('その製品の重さは？','headphones-weight'),('今紹介した製品の重量を教えて','headphones-weight'),('最後の製品は何グラム？','headphones-weight'),('直前に出てきた製品の重さを聞かせて','headphones-weight')], 'earphones-cmf':[('その製品のノイキャンは？','earphones-cmf-anc'),('今紹介した製品のANCの性能を教えて','earphones-cmf-anc'),('最後の製品のノイズキャンセリングは？','earphones-cmf-anc'),('直前に出てきた製品のANCはどんなもの？','earphones-cmf-anc')]}
source_semantics={r['intent']:r['semantic'] for r in base['rows'] if r['partition']=='train'}
for subject,answer in topics:
    if subject not in followups:continue
    for other,other_answer in topics:
        if other==subject:continue
        for length in [2,3,4,5]:
            history=[dict(question='先に紹介して。',answer=other_answer),dict(question='別の話題も紹介して。',answer=answer)]
            if length>=3:history.insert(0,dict(question='何をしている人？',answer=answers['role']))
            if length==4:history.append(dict(question='ありがとう。',answer=answers['thanks']))
            if length==5:
                history.insert(0,dict(question='使う機器もまとめて紹介して。',answer=answers['headphone-spec']))
                history.insert(0,dict(question='趣味についても聞かせて。',answer=answers['hobbies']))
            for i,(q,intent) in enumerate(followups[subject]):add('context-'+intent,q,answers[intent],f'context:{subject}:{other}:{length}:{i}','train' if i<2 else 'validation' if i==2 else 'test',history=history,kind='context',semantic=source_semantics[intent])

# Short complete MDN definitions, only from raw training pages. Validation/test
# pages remain raw holdouts; no labels are extracted from those pages.
mdn_docs=[json.loads(l) for l in (HERE/'mdn-language-documents.jsonl').read_text().splitlines()]
mdn_definitions=[
 ('const','/Grammar_and_types','再代入','constは、再代入できない変数を宣言します。オブジェクトのプロパティは変更できます。'),
 ('let','/let','ブロックスコープ','letは、再代入できるブロックスコープの変数を宣言します。'),
 ('Array','/Array','複数のアイテム','Arrayは、複数の値を順番に並べて扱うJavaScriptの配列です。'),
 ('Object','/Object','キー付き','Objectは、キーと値の組み合わせを持つJavaScriptのオブジェクトを表します。'),
 ('String','/String','文字の並び','Stringは、文字の並びを表したり操作したりするJavaScriptのオブジェクトです。'),
 ('Map','/Map','キーと値','Mapは、キーと値の組を保存するJavaScriptのコレクションです。'),
 ('Set','/Set','一意','Setは、重複しない値を保存するJavaScriptのコレクションです。'),
 ('typeof','/typeof','文字列','typeofは、値の型を示す文字列を返すJavaScriptの演算子です。'),
 ('関数','/Functions','関数','関数は、引数を受け取って処理を行い、値を返すことができるコードのまとまりです。'),
 ('Promise','/Using_promises','非同期処理','Promiseは、非同期処理の完了または失敗を表すJavaScriptのオブジェクトです。'),
 ('モジュール','/Modules','分割','モジュールは、コードを別のファイルへ分割し、importやexportで機能を共有する仕組みです。'),
 ('input','/input','フォーム','inputは、入力用のフォーム部品を作るHTML要素です。type属性で入力の種類を選べます。'),
 ('textarea','/textarea','複数行','textareaは、複数行のテキストを入力するHTML要素です。'),
 ('color','/color','前景色','CSSのcolorは、文字などの前景色を指定するプロパティです。'),
 ('font-family','/font-family','優先順位','font-familyは、使用するフォントを優先順に指定するCSSプロパティです。'),
 ('overflow-wrap','/overflow-wrap','文字列の途中','overflow-wrapは、長い単語などが枠からはみ出すときの折り返しを制御するCSSプロパティです。'),
]
mdn_evidence=[]
for name,suffix,needle,answer in mdn_definitions:
    hits=[d for d in mdn_docs if d['url'].endswith(suffix) and d['partition']=='train']
    if len(hits)!=1:raise ValueError('Missing train-only MDN page '+suffix)
    d=hits[0];paragraphs=[b['text'] for b in d['blocks'] if needle in b['text']]
    if not paragraphs:raise ValueError('No cited evidence for '+name)
    intent='mdn-'+name.lower()
    qs=[f'{name}とは何？',f'{name}の意味を教えて',f'{name}は何をするもの？',f'{name}を簡単に説明して',f'{name}について教えてほしい',f'{name}の基本を説明して',f'{name}はどういう仕組み？',f'{name}が何か知りたい',f'{name}とはどんなものか説明してください',f'{name}は何のために使うの？',f'{name}が表すものを教えてください',f'{name}の役割を説明してほしい']
    family(intent,answer,qs,kind='web-knowledge',semantic=dict(subject='web-technology',attribute=intent))
    for r in rows:
        if r['intent']==intent:r.update(sourceUrl=d['url'],sourceDocument=d['id'],license='CC BY-SA 4.0')
    mdn_evidence.append(dict(intent=intent,sourceDocument=d['id'],url=d['url'],evidence=paragraphs,answer=answer,license='CC BY-SA 4.0'))

# Pair-disjoint small arithmetic, not a calculator invoked at inference.
arithmetic=[]
for a in range(21):
    for b in range(21):
        bucket=int(hashlib.sha256(f'own-addition:{a}:{b}'.encode()).hexdigest()[:8],16)%10
        partition='validation' if bucket==8 else 'test' if bucket==9 else 'train'
        answer=f'{a}+{b}={a+b}なので、合わせて{a+b}個です。'
        questions=[f'りんごが{a}個、みかんが{b}個あります。全部で何個？',f'{a}個と{b}個を合わせると何個になる？',f'{a}個に{b}個を足すと何個ですか？',f'最初に{a}個あり、さらに{b}個増えました。今は全部で何個？']
        for q in questions:add('addition',q,answer,f'addition:{a}:{b}',partition,kind='reasoning',semantic=dict(subject='provided-facts',attribute='addition'))
        arithmetic.append(dict(a=a,b=b,partition=partition))

counts=collections.Counter(tuple(r['semantic'].values()) for r in rows if r['partition']=='train');unknown_count=sum(r['partition']=='train' and r['kind']=='unknown' for r in rows)
for row in rows:
    scale=4 if row['intent']=='addition' else 1.5 if row['kind']=='context' else 0.5 if row['kind']=='web-qa' else 1
    row['weight']=8/unknown_count if row['kind']=='unknown' else scale/counts.get(tuple(row['semantic'].values()),1)
documents=[];source_manifests=[]
for name in ['web','mdn']:
    documents.extend(json.loads(l) for l in (HERE/(name+'-language-documents.jsonl')).read_text().splitlines())
    source_manifests.append(dict(name=name,sha256=hashlib.sha256((HERE/(name+'-language-sources.json')).read_bytes()).hexdigest()))
authored='\n'.join(r['text'] for r in base['pretraining'] if r['document']=='authored-train')
documents.append(dict(id='authored-train',partition='train',text=authored,url=None,textSha256=hashlib.sha256(authored.encode()).hexdigest()))
documents.sort(key=lambda d: {'train':0,'validation':1,'test':2}[d['partition']]);seen=set();language={p:[] for p in ['train','validation','test']};document_meta=[]
for d in documents:
    if hashlib.sha256(d['text'].encode()).hexdigest()!=d['textSha256']:raise ValueError('Changed source '+d['id'])
    text=d['text']
    if d.get('site')=='mdn':
        text='\n'.join(b['text'] for b in d['blocks'] if not re.search(r'このページはコミュニティー|View in English|Always switch to English|この機能は広く実装|この機能の一部は|すべてのブラウザーで利用可能',b['text']))
    digest=hashlib.sha256(text.encode()).hexdigest()
    if digest in seen:continue
    seen.add(digest);frames=windows(text,tokenizer,d['id'],maximum_input=192,lookback=16)
    for frame in frames:
        frame['weight']=1/len(frames)
        if d.get('site')=='mdn':frame.update(license='CC BY-SA 4.0',sourceUrl=d['url'])
    language[d['partition']].extend(frames)
    document_meta.append(dict(id=d['id'],partition=d['partition'],originalTextSha256=d['textSha256'],textSha256=digest,frames=len(frames),url=d.get('url'),tokens=sum(len(r['tokens'])-r['prefixLength'] for r in frames)))
result=dict(schemaVersion=4,tokenizer=tokenizer,rows=rows,pretraining=language['train'],pretrainingValidation=language['validation'],pretrainingTest=language['test'],provenance=dict(baseCorpusSha256=base['sourceSha256'],sourceManifests=source_manifests,excludedSources=['Wikipedia','external pretrained weights','generative AI APIs'],rawLanguage='Full documents; BOS/EOS only at genuine boundaries. Overlapping lookback is masked from targets. Page-balanced raw sampling. Fixed own vocabulary, no audit fitting. MDN translation/baseline/browser-support boilerplate removed with original and processed hashes retained.',documents=document_meta,mdnDefinitions=mdn_evidence,arithmeticPairs=arithmetic,labels='Approved profile/spec facts, attributed government/MDN definitions and exact synthetic addition. No external model output supplies targets.',diagnostics='All prior 178/38/60 probes are reused development diagnostics. New audit must freeze before this training starts.',license='MDN-derived raw token records and adapted QA labels retain CC BY-SA 4.0 and per-source attribution; see MDN-DATA-LICENSE.md. Other existing portions keep their original conditions.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'continuous-corpus.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
manifest=dict(sourceSha256=result['sourceSha256'],partitions=dict(collections.Counter(r['partition'] for r in rows)),rawFrames={p:len(language[p]) for p in language},rawDocuments=len(document_meta),context=256,vocabulary=len(tokenizer['bytes']),maxSequence=max(len(r['tokens']) for r in rows),skipped=skipped)
(HERE/'continuous-data.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))
