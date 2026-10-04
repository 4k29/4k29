"""Human-authored, source-grounded QA plus exact synthetic arithmetic labels.

The public conversation engine and evaluation files never produce targets.
Question families and arithmetic pairs have fixed separate partitions.
"""
import hashlib
import json
import pathlib
import unicodedata
from tokenizer import fit, encode, prompt, SPECIALS

ROOT = pathlib.Path(__file__).resolve().parents[2]
profile_raw = (ROOT/'docs/profile.json').read_bytes()
spec_raw = (ROOT/'training/product-specifications.json').read_bytes()
profile = json.loads(profile_raw)
facts = {fact['id']: fact for fact in profile['facts']}
specifications = json.loads(spec_raw)
products = {p['id']: p for p in specifications['products']}
def value(id):
    return facts[id]['ja']['value']
def spec(id, key):
    return next(f['ja']['value'] for f in products[id]['fields'] if f['key'] == key)

# The first four question families train; the fifth validates; the last two test.
# Labels are written directly from verified facts, not sampled from an LLM.
seeds = [
 ('name', '名前は'+value('name')+'です。', ['名前は何？','なんて呼べばいい？','どんな名前で活動している？','お名前を教えて。','呼び名を聞かせて。','あなたの名前を知りたい。','どう呼ぶのがいい？'], ['name']),
 ('role', '学生です。', ['職業は何？','学生なの？','今の身分は？','仕事は何をしている？','どんな立場の人？','いまの職業を教えて。','社会人ですか？'], ['student']),
 ('hobbies', '趣味は'+value('photo')+'と'+value('running')+'です。', ['趣味は何？','何を趣味にしている？','休日に楽しむ趣味は？','趣味を教えて。','どんなことが趣味？','好きな趣味の活動を聞かせて。','楽しんでいる趣味は何ですか？'], ['photo','running']),
 ('audio', 'イヤホンは'+value('earphones-beats')+'と'+value('earphones-cmf')+'、ヘッドホンは'+value('headphones')+'を使っています。', ['何のイヤホンを使っている？','使っているヘッドホンは何？','愛用している音響機器は？','イヤホンとヘッドホンを教えて。','普段のイヤホンはどの機種？','音楽を聴くときの機器は何？','何というヘッドホンを使っていますか？'], ['earphones-beats','earphones-cmf','headphones']),
 ('favorites', 'VIVANT、TOKYO MER、kyu、してはる', ['好きなものは何？','好きなものを教えて。','お気に入りは何？','好きなものの名前は？','好きなものを挙げて。','あなたのお気に入りを聞きたい。','好んでいるものを教えてください。'], ['favorite-vivant','favorite-tokyo-mer','favorite-kyu','favorite-person']),
 ('mer', 'TOKYO MERは、鈴木亮平さん主演のTBSの日曜劇場ドラマです。', ['MERは？','TOKYO MERについて教えて。','MERはどんなドラマ？','TOKYO MERとは？','MERを紹介して。','TOKYO MERのことを知りたい。','merについて説明して。'], ['favorite-tokyo-mer']),
 ('vivant', 'VIVANTは、堺雅人さん主演のTBSの日曜劇場ドラマです。', ['VIVANTは？','VIVANTについて教えて。','VIVANTはどんなドラマ？','VIVANTとは？','VIVANTを紹介して。','VIVANTのことを知りたい。','vivantについて説明して。'], ['favorite-vivant']),
 ('kyu', facts['favorite-kyu']['ja']['overview']['brief'], ['kyuは？','kyuについて教えて。','kyuはどんなブランド？','kyuとは？','kyuを紹介して。','kyuのことを知りたい。','kyuについて説明してください。'], ['favorite-kyu']),
 ('headphone-spec', value('headphones')+'はNothingのヘッドホンで、'+spec('headphones','driver')+'ドライバーを搭載し、Bluetooth '+spec('headphones','bluetooth')+'と'+spec('headphones','resistance')+'の防塵・防水性能に対応しています。', ['Headphone (1)のスペックは？','Nothing Headphone1の仕様を教えて。','headphone1の性能は？','Nothingのヘッドホンのスペックは？','Headphone (1)の主な仕様は？','nothing headphone(1)の仕様が知りたい。','Headphone 1の特徴と性能を説明して。'], ['headphones']),
 ('headphone-weight', value('headphones')+'の重さは'+spec('headphones','weight')+'です。', ['Headphone (1)の重さは？','Headphone1は何グラム？','Nothing Headphone (1)の重量は？','headphone1の重さを教えて。','Headphone (1)はどれくらい重い？','nothing headphone1の重量が知りたい。','Headphone 1の重さを説明して。'], ['headphones']),
 ('cmf-battery', 'CMF BudsのANCオフの再生時間は、'+spec('earphones-cmf','battery-off')+'です。', ['CMF BudsのANCオフの電池は？','CMF Budsのノイズキャンセルを切った再生時間は？','CMF BudsはANCオフで何時間再生できる？','CMF BudsのANCをオフにしたバッテリーは？','CMF BudsのANCオフ時の再生時間を教えて。','cmf budsのancオフでの電池持ちは？','CMF Budsのノイキャンを切ると何時間聴ける？'], ['earphones-cmf']),
 ('tecirc', 'Tecircで記事を書いています。', ['Tecircでは何をしている？','Tecircでの活動は？','記事はどこで書いている？','Tecircについて教えて。','Tecircで何をする？','Tecircでのあなたの活動を教えて。','Tecircではどんなことをしていますか？'], ['tecirc']),
 ('topics', 'Tecircの記事では、'+value('tecirc-subjects')+'を扱っています。', ['記事で何を扱う？','Tecircの記事のテーマは？','執筆の題材は何？','どんな話題の記事を書く？','記事の内容を教えて。','何についての記事を執筆している？','書いている記事のテーマを聞かせて。'], ['tecirc-subjects']),
 ('running-app', 'ランニングには'+value('running-app')+'を使っています。', ['ランニングのアプリは何？','走るときのアプリは？','どのランニングアプリを使う？','ランニングアプリを教えて。','運動の記録には何を使う？','ランニングを記録するアプリは何？','ランニング用アプリの名前を知りたい。'], ['running-app']),
 ('running-shoes', 'ランニングでは'+value('running-shoes')+'を履いています。', ['ランニングの靴は何？','走るときに履く靴は？','どのランニングシューズを使う？','ランニングシューズを教えて。','ランニングでは何を履く？','ランニング用のシューズの名前は？','走るときの靴を教えてください。'], ['running-shoes']),
 ('unknown-age', '年齢は公開していません。', ['年齢は何歳？','あなたは何歳？','年齢を教えて。','何年生まれ？','いくつですか？','誕生年を知りたい。','生まれた年を教えて。'], []),
 ('greeting', 'こんにちは。何について知りたい？', ['こんにちは。','こんにちは！','おはよう。','こんばんは。','やあ。','初めまして。','よろしくお願いします。'], []),
 ('thanks', 'どういたしまして。', ['ありがとう。','助かった。','教えてくれてありがとう。','ありがとうございます。','感謝します。','教えてくれて助かりました。','ありがとう、よく分かった。'], [])
]
# Unshared personal information is unknown; do not invent an owner preference
# about disclosure. Its target is the existing, authorized unknown response.
seeds = [(id, profile['unknownReply'] if id=='unknown-age' else a, qs, ids) for id,a,qs,ids in seeds]
rows=[]
prefixes=['','ねえ、','ひとつ聞きたいんだけど、','こんにちは。','ちょっと教えて。','質問です。']
suffixes=['','教えてください。','短く答えて。']
for id,answer,questions,ids in seeds:
    for family,question in enumerate(questions):
        partition='train' if family<4 else 'validation' if family==4 else 'test'
        variants=[(p,s) for p in prefixes for s in suffixes] if partition=='train' else [('', '')]
        for prefix,suffix in variants:
            rows.append(dict(id=id+':'+str(family)+':'+str(len(rows)),group=id+':family:'+str(family),partition=partition,kind='profile' if ids else 'dialogue',question=prefix+question+suffix,answer=answer,history=[],factIds=ids))
# Context-dependent actor questions: history differs for two dramas but the
# current question is identical, so a model must condition on prior turns.
for id,actor in [('mer','鈴木亮平'),('vivant','堺雅人')]:
    seed=next(s for s in seeds if s[0]==id)
    follow=['それの主演は？','主演は誰？','そのドラマの主演は？','主演を教えて。','誰が主演している？','その作品の主演俳優は？','主人公を演じた人ではなく主演を教えて。']
    for family,question in enumerate(follow):
        partition='train' if family<4 else 'validation' if family==4 else 'test'
        for first in seed[2][:4] if partition=='train' else [seed[2][family]]:
            rows.append(dict(id='context-'+id+':'+str(len(rows)),group='context-'+id+':family:'+str(family),partition=partition,kind='context',question=question,answer=actor+'さんです。',history=[dict(question=first,answer=seed[1])],factIds=seed[3]))
for a in range(10):
    for b in range(10):
        split=(a*11+b*7)%10
        partition='test' if split==0 else 'validation' if split==1 else 'train'
        for style in range(3 if partition=='train' else 1):
            question=[f'{a}+{b}はいくつ？',f'{a}と{b}を足すと？',f'{a}に{b}を加えるといくつ？'][style]
            rows.append(dict(id=f'addition:{a}:{b}:{style}',group=f'addition:{a}:{b}',partition=partition,kind='addition',question=question,answer=f'{a+b}です。',history=[],factIds=[]))
        if a!=b:
            rows.append(dict(id=f'comparison:{a}:{b}',group=f'comparison:{a}:{b}',partition=partition,kind='comparison',question=f'{a}と{b}では、どちらが大きい？',answer=f'{max(a,b)}のほうが大きいです。',history=[],factIds=[]))
for row in rows:
    row['question']=unicodedata.normalize('NFKC',row['question']).lower()
    for turn in row['history']:
        turn['question']=unicodedata.normalize('NFKC',turn['question']).lower()
    row['weight']=3 if row['kind'] in ['profile','context'] else 1
train_texts=[]
for row in rows:
    if row['partition']=='train':
        train_texts.extend([row['question'],row['answer']])
        for turn in row['history']:train_texts.extend([turn['question'],turn['answer']])
tokenizer=fit(train_texts)
for row in rows:
    prefix=prompt(row['question'],row['history'],tokenizer)
    row['prefixLength']=len(prefix)
    row['tokens']=prefix+encode(row['answer'],tokenizer)+[SPECIALS['eos']]
result=dict(schemaVersion=1,tokenizer=tokenizer,rows=rows,provenance=dict(profileSha256=hashlib.sha256(profile_raw).hexdigest(),specificationsSha256=hashlib.sha256(spec_raw).hexdigest(),labels='Human-authored from approved profile/source values; exact arithmetic from Python integers. No existing conversation engine, external model, or evaluation files produce labels.',partition='Separate authored question families; entire arithmetic operand pairs held out; tokenizer fitted on train strings only.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
target=pathlib.Path(__file__).with_name('corpus.json')
target.write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
print(json.dumps(dict(rows=len(rows),vocabulary=len(tokenizer['bytes']),maxSequence=max(len(r['tokens']) for r in rows),partitions={p:sum(r['partition']==p for r in rows) for p in ['train','validation','test']},sourceSha256=result['sourceSha256'])))
