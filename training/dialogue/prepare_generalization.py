"""Source-grounded finite-domain curriculum, with explicit scope boundaries.

No generated model output supplies labels. All prose is defined by the dataset
author; existing profile and verified specification values supply known facts.
Question families, not repeated wrapper strings, define the three partitions.
"""
import hashlib
import json
import pathlib
import unicodedata
from tokenizer import fit, encode, prompt, SPECIALS

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[1]
profile=json.loads((ROOT/'docs/profile.json').read_text())
specifications=json.loads((ROOT/'training/product-specifications.json').read_text())
old=json.loads((HERE/'corpus.json').read_text())
facts={r['id']:r for r in profile['facts']}
products={r['id']:r for r in specifications['products']}
UNKNOWN='その情報は分かりません。'
rows=[]
def add(intent,question,answer,family,partition,history=None,fact_ids=None,kind='profile'):
    rows.append(dict(id=f'{intent}:{len(rows)}',intent=intent,group=f'{intent}:family:{family}',partition=partition,kind=kind,question=unicodedata.normalize('NFKC',question).lower(),answer=answer,history=history or [],factIds=fact_ids or [],weight=1))
def examples(intent,answer,questions,fact_ids=None,kind='profile',history=None):
    for i,q in enumerate(questions):
        partition='train' if i<len(questions)-4 else 'validation' if i<len(questions)-2 else 'test'
        wrappers=['','ちょっと聞きたい。','ねえ、','教えてほしいんだけど、'] if partition=='train' else ['']
        for w in wrappers:add(intent,w+q,answer,i,partition,history,fact_ids,kind)

# Keep prior QA families, without the 18 near-identical prefix/suffix copies.
seen=set()
for row in old['rows']:
    if row['kind'] in ['addition','comparison','context']:continue
    key=(row['group'],row['answer'])
    if key in seen:continue
    seen.add(key)
    # Original variant ordering starts with the unwrapped seed question.
    intent=row['id'].split(':')[0]
    answer=UNKNOWN if intent=='unknown-age' else row['answer']
    add(intent,row['question'],answer,'legacy-'+row['group'],row['partition'],fact_ids=row['factIds'],kind='unknown' if intent=='unknown-age' else row['kind'])

new={
 'name':['何という名前？','呼び名は？','名前を聞いてもいい？','名前を教えてほしい','あなたの呼び方を教えて','名乗ってください','どういう名前なの','名前について聞かせて','あなたを何と呼ぼうか','呼び名が知りたい'],
 'role':['どんな仕事？','職業を教えてほしい','学生ですか','働いているの？','立場を教えて','今は何をしている人？','あなたの職業が知りたい','どんな身分なの','今の仕事について聞かせて','何をしている人なの'],
 'hobbies':['趣味を聞かせて','趣味について教えてほしい','趣味はどんなこと？','普段の趣味は？','楽しみでやっていることは？','あなたの趣味を知りたい','趣味には何がある？','趣味は何をするの','何が趣味か聞かせて','どんな趣味があるの'],
 'audio':['イヤホンは何を使うの？','使うヘッドホンを聞かせて','普段何のイヤホンで聴く？','何というイヤホン？','どんなヘッドホンを使ってる？','イヤホンの機種を教えて','いつもの音響機器を教えて','使ってるイヤホンは？','今使っているヘッドホンを知りたい','音楽を聴く道具を聞かせて'],
 'favorites':['好きなものを聞かせて','お気に入りを教えてほしい','何が好きなの？','好きなものは？','好みのものを教えて','好きなものの名前だけ教えて','何がお気に入りなの','好きなものには何がある？','気に入っているものを挙げて','好きなものを列挙してください'],
 'tecirc':['Tecircで何を書いてる？','Tecircでの活動を聞かせて','Tecircでは記事を書くの？','記事を書いている場所は？','執筆活動はどこ？','Tecircでやっていることは？','Tecircとの関わりは？','Tecircでの活動を知りたい','あなたはTecircで何をしてるの','Tecircで何をしているのか教えて'],
 'topics':['どんなテーマで記事を書く？','記事の題材を聞かせて','何の記事を執筆する？','執筆テーマは？','記事は何について？','Tecircで扱う話題は？','どんな内容を記事にする？','記事の話題を教えて','あなたの記事はどんなテーマなの','Tecircに書く話題を知りたい'],
 'running-app':['ランニングで使うアプリは？','走った記録に使うアプリは？','走るとき何のアプリを開く？','ランニングの記録用アプリは？','ランの記録をするアプリは？','何のアプリで走った記録をつける？','ランニングアプリの名前は？','使っている運動記録アプリは？','走った距離を記録するアプリを聞かせて','ランニングのアプリ名が知りたい'],
 'running-shoes':['走るときのシューズは？','ランニングで履いている靴は？','走るための靴を教えて','普段履くランニングシューズは？','走るときの靴を聞かせて','ランニング用の靴は？','ランニングで使う靴の名前は？','シューズは何で走ってる？','愛用するランニングシューズを知りたい','走るときのシューズ名を聞かせて'],
 'greeting':['こんにちは','やあ！','おはようございます','こんばんは！','はじめまして','どうもこんにちは','よろしく','初めまして！','こんにちは、よろしく','やあ、はじめまして'],
 'thanks':['ありがとう','助かりました','どうもありがとう','ありがとう！','教えてくれて助かった','感謝してます','説明ありがとう','助かったよ','ありがとう、理解できた','返事をくれてありがとう'],
}
canonical={r['id'].split(':')[0]:r for r in old['rows'] if not r['history'] and r['kind'] not in ['addition','comparison']}
for intent,questions in new.items():
    base=canonical[intent]
    examples(intent,base['answer'],questions,base['factIds'],base['kind'])

for intent,name,actor in [('mer','TOKYO MER','鈴木亮平'),('vivant','VIVANT','堺雅人')]:
    alias='MER' if intent=='mer' else name
    answer=f'{name}は、{actor}さん主演のTBSの日曜劇場ドラマです。'
    examples(intent,answer,[f'{alias}って何？',f'{alias}について知りたい',f'{alias}の説明をして',f'{alias}について教えてほしい',f'{name}の説明を聞かせて',f'{alias}について聞かせて',f'{alias}について簡単に説明して',f'{name}はどういうドラマ？',f'{alias}のことを教えてほしい',f'{name}がどんな作品か教えて'],['favorite-'+('tokyo-mer' if intent=='mer' else 'vivant')])
    examples(intent+'-actor',f'{actor}さんです。',[f'{alias}の主演は？',f'{name}は誰が主演？',f'{alias}の主演俳優は誰？',f'{alias}の主演を教えて',f'{name}に主演しているのは誰？',f'{alias}の主演の名前は？',f'{alias}は誰が主演してるの',f'{alias}の主演俳優を教えてほしい',f'{name}で主演を務めている人は？',f'{alias}の主演の人を知りたい'])
    examples(intent+'-station','TBSの日曜劇場です。',[f'{alias}の放送局は？',f'{alias}はどのテレビ局？',f'{name}の放送枠は？',f'{alias}を放送した局は？',f'{alias}はどこの局のドラマ？',f'{name}の放送局を教えて',f'{alias}は何の枠で放送された？',f'{alias}の放送枠を教えて',f'{name}はどの局で放送していた？',f'{alias}のテレビ局が知りたい'])
    for other in ['mer','vivant']:
        first=canonical[other]
        history=[dict(question='そのドラマを説明して。',answer=first['answer']),dict(question=f'{alias}は？',answer=answer)]
        examples('context-'+intent+'-actor',f'{actor}さんです。',['それの主演は？','主演は誰？','そのドラマの主演は？','それは誰が主演？','主演を教えて','主演俳優は？','その作品の主演を教えて','誰が主演しているの？','今のドラマの主演を聞かせて','直前に話したドラマの主演は誰？'],kind='context',history=history)

names={'headphones':['Nothing Headphone (1)','Headphone1','headphone(1)','Nothing Headphone1'], 'earphones-cmf':['CMF Buds','cmf buds'],'earphones-beats':['Beats Fit Pro','beats fit pro'],'favorite-kyu':['kyu camera','kyuのカメラ']}
synonyms={
 'driver':['ドライバー','ドライバー径','ドライバーの種類'], 'weight':['重さ','重量','何グラム'],
 'bluetooth':['Bluetooth','Bluetoothのバージョン','ブルートゥースのバージョン'],
 'codecs':['コーデック','対応コーデック','音声コーデック'], 'resistance':['防水性能','防塵・防水性能','防水等級'],
 'anc':['ノイズキャンセリング','ANC','ノイキャン'], 'charging':['充電端子','接続端子','充電用の端子'],
 'impedance':['インピーダンス','抵抗値'], 'battery-capacity':['バッテリー容量','電池容量'],
 'connection':['接続方法','接続端子の種類'], 'multipoint':['2台同時接続','マルチポイント'],
 'wireless-charging':['ワイヤレス充電','無線充電'], 'fast-charging':['急速充電','短時間の充電'],
 'storage':['ストレージ','記憶容量'], 'video-front':['フロント動画','前面カメラの動画'], 'video-back':['バック動画','背面カメラの動画'], 'dimensions':['サイズ','寸法'],
 'battery-off':['ANCオフの再生時間','ノイキャンを切ったときの電池持ち','ANCをオフにしたときの再生時間'],
 'battery-on':['ANCオンの再生時間','ノイキャンを入れたときの電池持ち','ANCをオンにしたときの再生時間'],
 'battery-aac-on':['AAC・ANCオンの再生時間','AACでノイキャンを入れた再生時間'],
 'battery-aac-off':['AAC・ANCオフの再生時間','AACでノイキャンを切った再生時間'],
 'battery-ldac-on':['LDAC・ANCオンの再生時間','LDACでノイキャンを入れた再生時間'],
 'battery-ldac-off':['LDAC・ANCオフの再生時間','LDACでノイキャンを切った再生時間'],
}
formats=['{n}の{s}は？','{n}の{s}を教えて。','{n}について、{s}が知りたい。','{n}の{s}を聞かせて。','{n}は{s}がどうなっている？','{n}の{s}について教えてほしい。','{n}の{s}を説明して。','{n}は{s}がどれくらい？','{n}について{s}を教えてくれる？','{n}の{s}について知りたいんだけど。']
for pid,product in products.items():
    label=names[pid][0]
    for field in product['fields']:
        key=field['key']; f=field['ja']; intent=pid+'-'+key
        answer=f"{label}の{f['label']}は、{f['value']}です。"
        # More idiomatic statements for yes/no capabilities and device weight.
        if key=='weight':answer=f"{label}の重さは{f['value']}です。"
        if key=='anc' and pid=='earphones-beats':answer=f'{label}はANCに対応しています。'
        if key=='resistance':
            answer={'headphones':f'{label}はIP52の防塵・防水性能に対応しています。','earphones-cmf':f'{label}のイヤホン本体はIP54の防塵・防水性能に対応しています。','earphones-beats':f'{label}のイヤホン本体はIPX4の耐汗・耐水性能に対応しています。ケースは非対応です。'}[pid]
        if key=='multipoint':answer=(f'{label}は2台同時接続に対応しています。' if pid=='headphones' else f'{label}はNothing Xアプリで設定すると2台同時接続が使えます。')
        if key=='wireless-charging':answer=f'{label}はワイヤレス充電に対応していません。'
        qs=[]
        for i,form in enumerate(formats):
            for n in names[pid] if i<6 else [names[pid][0]]:
                for s in synonyms[key] if i<6 else [synonyms[key][i%len(synonyms[key])]]:
                    qs.append((i,form.format(n=n,s=s)))
        for family,q in qs:
            part='train' if family<6 else 'validation' if family<8 else 'test'
            for prefix in ['', 'ねえ、'] if part=='train' else ['']:
                add(intent,prefix+q,answer,'spec-'+str(family),part,fact_ids=[pid])
        # Same follow-up text, different preceding product. Conditions stay in
        # the question for battery life; no unqualified battery-time answers.
        follow=[f'{s}は？' for s in synonyms[key]]
        history=[dict(question=f'{label}について教えて。',answer=(canonical['headphone-spec']['answer'] if pid=='headphones' else f'{label}について説明します。'))]
        for i,q in enumerate(follow):add('context-'+intent,q,answer,i,'train',history,[pid],kind='context')

# Full product description retains the introduction + multiple specs together.
head=canonical['headphone-spec']['answer']
examples('headphone-spec',head,['Headphone1の特徴は？','Headphone (1)について教えてほしい','Nothingのヘッドホンの性能を教えて','Nothing Headphone (1)のスペックを聞かせて','headphone1の製品仕様は？','Headphone (1)の特徴と性能を説明して','Headphone1の性能を詳しく教えて','Nothing Headphone (1)の特徴を聞かせて','Headphone (1)の仕様をまとめて教えて','Nothing Headphone1について知りたい'])
examples('kyu',canonical['kyu']['answer'],['kyuって何？','kyuのブランドを教えて','kyuはどんなブランドなの？','kyuについて知りたい','kyuの説明をして','kyuについて聞かせて','kyuってどんなブランド？','kyuのことを教えてほしい','kyuを説明してくれる？','kyuについてもう少し知りたい'],['favorite-kyu'])
examples('tecirc-not-hobby','Tecircでの記事執筆は活動です。趣味は写真・映像制作とランニングです。',['Tecircは趣味？','記事執筆は趣味なの？','Tecircで書くのは趣味？','執筆が趣味ですか？','記事を書くことは趣味なの？','Tecircの記事執筆は趣味なの？','Tecircは趣味に入る？','記事を書くのが趣味なの？','Tecircでの執筆は趣味に含まれる？','Tecircで記事を書くのも趣味ですか？'])

# Explicit boundary pairs: valid known device vs a different model/person.
for n in ['Headphone (2)','Nothing Headphone2','CMF Buds Pro 2','CMF Buds 2','AirPods Pro','Sony WH-1000XM5','友達のヘッドホン','友人のイヤホン','別の人のヘッドホン']:
    examples('unknown-product',UNKNOWN,[f'{n}の重さは？',f'{n}のBluetoothは？',f'{n}のバッテリー容量は？',f'{n}の防水性能は？',f'{n}のコーデックは？',f'{n}の仕様を教えて',f'{n}の再生時間は？',f'{n}の接続方法は？',f'{n}の性能について知りたい',f'{n}の重量を聞かせて'],kind='unknown')
unknown_questions=[
 ['年齢は？','何歳なの？','誕生日はいつ？','生年月日は？','誕生年は？','生まれた日は？','いくつなの？','いつ生まれた？','あなたの年齢を知りたい','何年に生まれたの？'],
 ['今日の天気は？','明日の天気は？','東京の今の天気は？','今日の気温は？','明日は雨？','今は晴れてる？','今日の東京の気温は？','現在の天候を教えて','東京は今、雨が降ってる？','明日の予報を聞かせて'],
 ['住所は？','電話番号は？','本名は？','どこに住んでいる？','学校名は？','身長は？','体重は？','家族の名前は？','通っている学校を知りたい','住んでいる場所を聞かせて'],
 ['ヘッドホンを選んだ理由は？','イヤホンを買った理由は？','何円で買った？','購入日は？','どこで買った？','何色を買った？','購入の決め手は？','誰に勧められた？','Headphone (1)を買った理由を知りたい','CMF Budsはいつ買ったの？'],
 ['今の株価は？','今年のニュースは？','今日のニュースは？','日本の首相は今誰？','次の試合の結果は？','今日の為替は？','現在の時刻は？','今の電車の遅延は？','最新のニュースを聞かせて','今の為替レートを知りたい'],
]
for i,qs in enumerate(unknown_questions):examples('unknown-scope-'+str(i),UNKNOWN,qs,kind='unknown')

# A repeated input must never cross splits or teach incompatible labels. Use
# the latest source-grounded wording and put its entire family in the most
# conservative partition that contains the repeated input.
priority={'train':0,'validation':1,'test':2}
for _ in range(4):
    inputs={}
    for r in rows:
        key=(r['question'],json.dumps(r['history'],ensure_ascii=False,sort_keys=True))
        inputs.setdefault(key,[]).append(r)
    for same in inputs.values():
        if len(same)<2:continue
        partition=max((r['partition'] for r in same),key=priority.get)
        groups={r['group'] for r in same}
        for r in rows:
            if r['group'] in groups:r['partition']=max(r['partition'],partition,key=priority.get)
        answer=same[-1]['answer']
        for r in same:r['answer']=answer
seen=set();unique=[]
for r in rows:
    key=(r['question'],json.dumps(r['history'],ensure_ascii=False,sort_keys=True))
    if key in seen:continue
    seen.add(key);unique.append(r)
rows=unique

# A small raw Japanese next-token corpus demonstrates own pretraining without
# claiming general language acquisition. Entirely train-only answers + authored
# short narratives; validation/test answers are never selected as raw samples.
raw=sorted({r['answer'] for r in rows if r['partition']=='train'})
for subject in ['太郎','花子','健太','美咲','遥','直樹','咲','翔太']:
    for thing,action in [('本','読む'),('写真','撮る'),('記事','書く'),('動画','見る'),('音楽','聴く')]:
        raw.extend([f'{subject}は{thing}が好きです。休日には{thing}を楽しみます。',f'{subject}は今日、{thing}を{action}ことにしました。',f'{thing}を{action}前に、{subject}は予定を確認しました。'])
for place in ['図書館','公園','学校','駅']:
    raw.extend([f'今日は{place}へ行きました。帰り道に友達と話しました。',f'明日は{place}へ行く予定です。雨が降ったら、予定を変えます。'])
train_strings=raw[:]
for row in rows:
    if row['partition']!='train':continue
    train_strings.extend([row['question'],row['answer']])
    for turn in row['history']:train_strings.extend([turn['question'],turn['answer']])
tokenizer=fit(train_strings,merges=768)
for row in rows:
    prefix=prompt(row['question'],row['history'],tokenizer)
    row['prefixLength']=len(prefix);row['tokens']=prefix+encode(row['answer'],tokenizer)+[SPECIALS['eos']]
    # Balance intents rather than letting template-rich specs overwhelm the
    # direct profile, dialogue and unknown examples.
counts={}
for row in rows:
    if row['partition']=='train':counts[row['intent']]=counts.get(row['intent'],0)+1
for row in rows:row['weight']=1/counts.get(row['intent'],1)
result=dict(schemaVersion=2,tokenizer=tokenizer,rows=rows,pretraining=[dict(text=t,tokens=[SPECIALS['bos']]+encode(t,tokenizer)+[SPECIALS['eos']]) for t in raw],provenance=dict(labels='Dataset-author-defined prose and templates from approved facts/verified specifications; no external model output, pretrained tokenizer or weights.',partitions='Disjoint question families. Legacy tests retained as development diagnostics, not a fresh independent comparison. New test families are frozen before any new training.',profileSha256=hashlib.sha256((ROOT/'docs/profile.json').read_bytes()).hexdigest(),specificationsSha256=hashlib.sha256((ROOT/'training/product-specifications.json').read_bytes()).hexdigest(),rawLanguage='Finite authored train-only sentences; no broad Japanese pretraining corpus is claimed.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'generalization-corpus.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
manifest=dict(sourceSha256=result['sourceSha256'],partitions={p:sum(r['partition']==p for r in rows) for p in ['train','validation','test']},intents=len(counts),vocabulary=len(tokenizer['bytes']),rawLanguageSamples=len(raw),maxSequence=max(len(r['tokens']) for r in rows),testSha256=hashlib.sha256(json.dumps([r for r in rows if r['partition']=='test'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest())
(HERE/'generalization-data.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(manifest))
