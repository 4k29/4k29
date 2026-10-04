"""Author-defined contrasts; fixed own vocabulary and unchanged legacy probes.

No model output supplies targets. New question-form families are split before
training. Old challenge questions become development diagnostics, not holdouts.
"""
import collections
import copy
import hashlib
import json
import pathlib
import unicodedata
from tokenizer import encode,prompt,SPECIALS

HERE=pathlib.Path(__file__).resolve().parent
UNKNOWN='その情報は分かりません。'
base=json.loads((HERE/'web-curriculum-corpus.json').read_text())
products=json.loads((HERE.parent/'product-specifications.json').read_text())['products']
rows=copy.deepcopy(base['rows']);tokenizer=base['tokenizer'];skipped=[]
labels={r['intent']:r['answer'] for r in base['rows'] if r['partition']=='train'}
inputs={json.dumps([r['question'],r['history']],ensure_ascii=False,sort_keys=True) for r in rows}
def add(intent,q,answer,family,partition='train',history=None,kind='profile',source=None):
    q=unicodedata.normalize('NFKC',q).lower();history=history or []
    key=json.dumps([q,history],ensure_ascii=False,sort_keys=True)
    if key in inputs:return
    prefix=prompt(q,history,tokenizer);tokens=prefix+encode(answer,tokenizer)+[SPECIALS['eos']]
    if len(tokens)>127:skipped.append(dict(intent=intent,question=q,reason='sequence-overflow',length=len(tokens)));return
    inputs.add(key)
    row=dict(id=f'binding:{len(rows)}',intent=intent,group='binding:'+family,partition=partition,kind=kind,question=q,answer=answer,history=history,factIds=[],weight=1,prefixLength=len(prefix),tokens=tokens)
    if source:row['sourceUrl']=source
    rows.append(row)
def families(intent,answer,questions,kind='profile'):
    for i,q in enumerate(questions):
        partition='train' if i<len(questions)-4 else 'validation' if i<len(questions)-2 else 'test'
        add(intent,q,answer,intent+':'+str(i),partition,kind=kind)

profile_questions={
 'role':['今は学生として過ごしている？','仕事をしているか教えて','あなたは学生なのかな','日頃どんな立場で活動してる？','社会人か学生かを聞きたい','普段の身分を教えてくれる？','今の肩書きを知りたいです','いまの職業は何になる？','あなたの立場ってどんなもの？','現在の身分について教えてください','今どんな立場の人なのか聞かせて','あなたは何をする人ですか'],
 'audio':['音楽を聴くときに使う機器を教えて','いつも何で音楽を聴くの？','音楽用に使っている道具を挙げて','手持ちのイヤホンとヘッドホンは何？','普段聴くために使ってる製品の名前は？','音を聴く機器のラインナップを知りたい','愛用している音響機器は何？','イヤホンもヘッドホンも教えて','日常で使っているオーディオ機器は？','使っているイヤホンの製品名を聞かせて','持っているリスニング機器は何ですか','どのヘッドホンやイヤホンで聴いてる？'],
 'topics':['Tecircの記事で扱うテーマを教えて','Tecircでは何について記事にするの？','記事の主な題材は何ですか','Tecircに書いている内容の分野は？','どんな内容をテーマにして書く？','執筆している記事のジャンルは何？','あなたが書く記事の中心的な話題は？','Tecircの記事はどんな分野に関するもの？','記事では何を取り上げている？','記事にする話題の種類を知りたい','Tecircで取り上げる題材はどんなもの？','あなたの執筆テーマの分野を聞かせて'],
 'favorites':['気に入っているものの名前を挙げて','好きなものを名前だけ並べて','お気に入りの名前を聞かせて','何を好きなのか一覧で教えて','好きなものの一覧は？','好みのものを列挙して','お気に入りはどんなものがある？','好きなものを教えてください','お気に入りのものは何ですか','好きなものの名称が知りたい','好きなものをいくつか挙げてもらえる？','何がお気に入りか教えてください'],
}
for intent,qs in profile_questions.items():families(intent,labels[intent],qs)

aliases={
 'headphones':['Nothing Headphone (1)','Headphone 1','nothing headphone1','Headphone(1)'],
 'earphones-cmf':['CMF Buds','cmf buds'],
 'earphones-beats':['Beats Fit Pro','beats fit pro'],
 'favorite-kyu':['kyu camera','kyuのカメラ'],
}
fields={
 'driver':['ドライバー','音を鳴らすドライバー'], 'bluetooth':['Bluetoothのバージョン','Bluetooth'],
 'codecs':['音声コーデック','対応するコーデック'], 'anc':['ノイズキャンセリングの方式','ノイキャンの性能','ANCの性能'],
 'resistance':['耐水性能','防水の等級','水や汗への対応'], 'weight':['重量','重さ'],
 'impedance':['インピーダンス','抵抗値'], 'battery-capacity':['バッテリーの容量','電池そのものの容量'],
 'battery-off':['ノイキャンを切った場合の再生時間','ANCを無効にしたときの電池持ち'],
 'battery-on':['ノイキャンを入れた場合の再生時間','ANCを有効にしたときの電池持ち'],
 'battery-aac-off':['AACでANCを切った場合の電池持ち','AAC・ANCオフの再生時間'],
 'battery-aac-on':['AACでANCを入れた場合の電池持ち','AAC・ANCオンの再生時間'],
 'battery-ldac-off':['LDACでANCを切った場合の電池持ち','LDAC・ANCオフの再生時間'],
 'battery-ldac-on':['LDACでANCを入れた場合の電池持ち','LDAC・ANCオンの再生時間'],
 'connection':['接続の方法','有線接続の端子'], 'multipoint':['2台同時接続への対応','マルチポイント機能'],
 'wireless-charging':['無線充電への対応','ワイヤレス充電への対応'], 'charging':['充電の端子','充電に使う端子'],
 'fast-charging':['短時間での充電性能','急速充電の性能'], 'storage':['保存用ストレージの容量','記憶容量'],
 'video-front':['前面カメラの動画仕様','フロント動画の解像度'], 'video-back':['背面カメラの動画仕様','バック動画の解像度'],
 'dimensions':['本体の寸法','本体の大きさ'],
}
forms=['{n}で、{s}はどうなっているの？','{n}について聞きたい。{s}を教えて','{s}はどうなの、{n}の場合。','{n}を知りたいんだけど、{s}を説明して','{n}に関して{s}が気になっている','{n}だと{s}はどんな仕様になる？','{n}は{s}がどのくらいか知りたい','{n}のことなんだけど、{s}を聞かせて','{s}について、{n}の仕様を知りたい','{n}なら{s}はどうですか','{n}における{s}の仕様を教えてください','{n}を使う際の{s}を確認したい']
for product in products:
    pid=product['id']
    for field in product['fields']:
        name=pid+'-'+field['key'];answer=labels[name]
        for family,form in enumerate(forms):
            part='train' if family<8 else 'validation' if family<10 else 'test'
            for alias in aliases[pid]:
                for phrase in fields[field['key']]:
                    add(name,form.format(n=alias,s=phrase),answer,f'spec-form:{family}',part,source=field['source']['url'])
        # Reference resolution must follow the last product, not the first.
        for previous in [p for p in products if p['id']!=pid]:
            history=[dict(question='何を使っている？',answer=previous['name']+'です。'),dict(question='次の製品は何？',answer=product['name']+'です。')]
            for phrase in fields[field['key']]:add('context-'+name,'今の製品の'+phrase+'は？',answer,'context-last:'+name,history=history,kind='context')

# Unsupported *fields* on known products are distinct from unsupported models.
for product in products:
    known={f['key'] for f in product['fields']}
    for missing in ['weight','driver','bluetooth','storage','battery-capacity','video-front','video-back']:
        if missing in known:continue
        for i,form in enumerate(forms):
            part='train' if i<8 else 'validation' if i<10 else 'test'
            add('unknown-field',form.format(n=product['name'],s=fields[missing][0]),UNKNOWN,'missing-field:'+str(i),part,kind='unknown')
for i,question in enumerate(['使っているカメラの型番は？','撮影に使うカメラの製品名を教えて','普段どのカメラで写真を撮る？','学校の名前を教えてください','通学先の名前は何ですか','今住んでいる住所を教えて','今日の東京の空模様は？','現在の大阪の気温を教えて','明日雨が降るか知りたい','きょう日本の株価はいくら？','今日の東京の天候はどうなってる？','現在地の天気を教えてください','所属する学校名を聞いてもいい？','写真撮影用のカメラの型式は何？']):
    part='train' if i<10 else 'validation' if i<12 else 'test'
    add('unknown-person-or-current',question,UNKNOWN,'unknown-scope:'+str(i),part,kind='unknown')

# Explicit verified weather definitions; these facts were raw prose before.
# Concise complete prose is authored here, with source paragraphs retained.
documents=[json.loads(l) for l in (HERE/'web-language-documents.jsonl').read_text().splitlines()]
definitions=[
 ('snow-white','雪の結晶自体は透明ですが、細かい結晶が重なって光が乱反射するため、白く見えます。',['雪はなぜ白いの？','雪が白いわけを説明して','雪の色が白く見える仕組みは？','雪の結晶は透明なのに白く見えるのはなぜ？','白い雪の色は何によるもの？','なぜ雪には白い色が付いて見えるの？','雪が白くなる光の仕組みを知りたい','雪はどうして白色に見えるのですか'], '光の乱反射'),
 ('wind','平均風速は10分間の平均で、瞬間風速はある瞬間の風速です。瞬間風速は平均風速の1.5〜3倍程度になることがあります。',['平均風速と瞬間風速の違いは？','風速と瞬間風速を区別して説明して','瞬間風速は平均風速と何が違う？','普通の風速と瞬間の風速は同じ？','平均と瞬間の風速はどう違いますか','瞬間風速と風速の意味を知りたい','風速と瞬間風速は何を測るの？','平均風速と瞬間風速の定義を説明してください'], '１０分間の平均風速'),
 ('hot-days','最高気温が35℃以上の日が猛暑日、30℃以上が真夏日、25℃以上が夏日です。',['猛暑日は何度以上？','夏日と真夏日と猛暑日の基準は？','気温が何度になると猛暑日なの？','暑い日を分類する温度の条件は？','真夏日と猛暑日の温度を教えて','夏日の気温の基準は何度？','夏日や猛暑日の分類を温度で説明して','猛暑日と真夏日と夏日の定義は何ですか'], '最高気温が３５℃以上'),
 ('tropical-night','熱帯夜は、夕方から翌朝までの最低気温が25℃以上になる夜です。',['熱帯夜は何度以上？','熱帯夜の定義は？','何度の夜を熱帯夜と呼ぶ？','夜の最低気温が何度だと熱帯夜？','熱帯夜の気温の基準を教えて','熱帯夜はどの時間帯の気温で決める？','熱帯夜と呼ぶ条件を説明して','熱帯夜の最低気温の条件は何ですか'], '夕方から翌日の朝'),
]
evidence=[]
for key,answer,questions,needle in definitions:
    hits=[(d,b) for d in documents if d['partition']=='train' for b in d['blocks'] if needle in b['text']]
    if not hits:raise ValueError('No train-only official evidence for '+key)
    d,b=hits[0];evidence.append(dict(intent='definition-'+key,url=d['url'],evidence=b['text'],answer=answer))
    families('definition-'+key,answer,questions,kind='web-knowledge')
    for r in rows:
        if r['intent']=='definition-'+key:r['sourceUrl']=d['url']

def semantics(row):
    intent=row['intent'].removeprefix('context-')
    if row['kind']=='unknown' or intent.startswith('unknown'):return dict(subject='unverified',attribute='unknown')
    for product in products:
        if intent.startswith(product['id']+'-'):return dict(subject=product['id'],attribute=intent[len(product['id'])+1:])
    if intent=='headphone-weight':return dict(subject='headphones',attribute='weight')
    if intent=='headphone-spec':return dict(subject='headphones',attribute='description')
    if intent=='cmf-battery':return dict(subject='earphones-cmf',attribute='battery-off')
    for drama in ['mer','vivant']:
        if intent==drama or intent.startswith(drama+'-'):return dict(subject=drama,attribute=intent[len(drama)+1:] or 'description')
    if intent.startswith('definition-'):return dict(subject='weather',attribute=intent)
    if intent.startswith('web-qa-'):return dict(subject='web-explanation',attribute=intent)
    return dict(subject='owner' if intent not in ['greeting','thanks'] else 'conversation',attribute=intent)
counts=collections.Counter()
unknown_count=sum(r['partition']=='train' and r['kind']=='unknown' for r in rows)
for row in rows:
    row['semantic']=semantics(row)
    if row['partition']=='train':counts[tuple(row['semantic'].values())]+=1
for row in rows:
    scale=0.5 if row['kind']=='web-qa' else 1.5 if row['kind']=='context' else 1
    row['weight']=8/unknown_count if row['kind']=='unknown' else scale/counts.get(tuple(row['semantic'].values()),1)
result=copy.deepcopy(base);result.pop('sourceSha256');result['rows']=rows
result['provenance'].update(baseCorpusSha256=base['sourceSha256'],labels='Dataset-author-defined profile, official specs and standalone government definitions. Expanded subject/field/condition contrasts. No external model labels.',bindingEvidence=evidence,diagnostics='Previously evaluated 178/38 questions remain development diagnostics. New form families are split before training. Independent audit questions must be frozen before this experiment starts.')
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'binding-corpus.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
manifest=dict(sourceSha256=result['sourceSha256'],baseCorpusSha256=base['sourceSha256'],partitions=dict(collections.Counter(r['partition'] for r in rows)),vocabulary=len(tokenizer['bytes']),semanticSubjects=sorted({r['semantic']['subject'] for r in rows if r['partition']=='train'}),semanticAttributes=sorted({r['semantic']['attribute'] for r in rows if r['partition']=='train'}),skipped=skipped,maxSequence=max(len(r['tokens']) for r in rows))
(HERE/'binding-data.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))
