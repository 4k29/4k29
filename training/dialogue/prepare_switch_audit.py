"""Freeze120 author-defined questions before the new model is trained."""
import hashlib,json,pathlib,random,unicodedata
from tokenizer import prompt,encode_stream
HERE=pathlib.Path(__file__).resolve().parent
c=json.loads((HERE/'switch-corpus.json').read_text());t=c['tokenizer']
answers={r['intent']:r['answer'] for r in c['rows'] if r['partition']=='train'}
rows=[]
def add(q,intent=None,kind='profile',history=None,answer=None):
    rows.append(dict(id='switch-audit:'+str(len(rows)),group='switch-fresh:'+str(len(rows)),partition='test',kind=kind,question=q,history=history or [],answer=answer if answer is not None else answers[intent]))
profile=[
 ('名乗るときの表記とふりがなを教えてくれるかな。','name'),('今は学生なのか、仕事をしているのか聞きたいな。','role'),
 ('空いた時間は、趣味としてどんなことに取り組むの？','hobbies'),('音楽を楽しむときに愛用している機器を挙げてくれる？','audio'),
 ('気に入っているものを、名前のみで教えてくれるかな。','favorites'),('Tecircで取り組んでいることを一言で聞かせて。','tecirc'),
 ('執筆している記事では、どんな題材を取り上げるのかな。','topics'),('走った記録を残すときは、どのアプリを開くの？','running-app'),
 ('ランニングのときに履いている靴を製品名で聞かせて。','running-shoes'),('TOKYO MERって、誰が主演でどの放送枠なのかな。','mer'),
 ('VIVANTという作品の主演と放送枠をまとめて聞きたいな。','vivant'),('kyuがどんなブランドなのか、一言で説明できる？','kyu'),
 ('Headphone1という製品を、主な仕様も含めて紹介できる？','headphone-spec'),('Nothing Headphone1は何グラムの重さがあるのかな。','headphones-weight'),
 ('Headphone (1)にはどんな口径のどんなドライバーが入ってる？','headphones-driver'),('Headphone1のBluetoothの版を数字で聞かせて。','headphones-bluetooth'),
 ('Headphone1で利用できるコーデックを全部聞かせて。','headphones-codecs'),('Headphone1の防水防塵は、どの等級までなのかな。','headphones-resistance'),
 ('AACを使ってノイキャンも作動させたHeadphone1は、何時間聴けるのかな。','headphones-battery-aac-on'),
 ('AAC接続でノイキャンを止めたHeadphone1は、最大どれくらい聴けるのかな。','headphones-battery-aac-off'),
 ('LDACを使いノイキャンを作動させたHeadphone1の再生時間を聞きたいな。','headphones-battery-ldac-on'),
 ('LDAC接続でノイキャンを止めたHeadphone1は、最長どれくらい聴けるのかな。','headphones-battery-ldac-off'),
 ('CMF Budsのノイキャンは、方式と強さがどうなってるのかな。','earphones-cmf-anc'),
 ('CMF Budsをノイキャンなしで使うと、単体とケースで何時間ずつ聴けるのかな。','earphones-cmf-battery-off'),
 ('CMF Budsでノイキャンを使うと、単体とケースで何時間ずつ聴けるのかな。','earphones-cmf-battery-on'),
 ('CMF Budsのイヤホンとケースには、何mAhずつの電池があるのかな。','earphones-cmf-battery-capacity'),
 ('Beats Fit Proは、ケースもイヤホンも水に対応しているのかな。','earphones-beats-resistance'),
 ('Beats Fit Proで短時間の充電をすると、どれくらい聴けるのかな。','earphones-beats-fast-charging'),
 ('kyu cameraというカメラの重量をグラムで聞かせて。','favorite-kyu-weight'),
 ('kyu cameraのフロント動画は、解像度などがどうなってるのかな。','favorite-kyu-video-front'),
 ('kyu cameraは、何GBの内部保存領域を持っているのかな。','favorite-kyu-storage'),
 ('kyu cameraを充電するときの端子の種類を聞きたいな。','favorite-kyu-charging')]
for q,intent in profile:add(q,intent)
# The first28 questions reappear after unrelated history; correct answers must
# remain tied to the new explicit question, not to the last response.
old=[('MERのことを先に聞こう。',answers['mer']),('VIVANTの紹介を先に聞こう。',answers['vivant']),('趣味を先に聞こう。',answers['hobbies']),('名前を先に聞こう。',answers['name']),('先にkyuを紹介して。',answers['kyu']),('まずHeadphone1を紹介して。',answers['headphone-spec']),('こんばんは。', 'こんばんは。何について知りたい？')]
for i,(q,intent) in enumerate(profile[:28]):
    previous=old[(i+1)%len(old)];history=[dict(question=previous[0],answer=previous[1])]
    if i%3==0:history.insert(0,dict(question='初めに立場を聞いてもいい？',answer=answers['role']))
    if i%4==0:history.append(dict(question='説明してくれてありがとう。',answer=answers['thanks']))
    add(q,intent,'context',history)
for order in [['mer','vivant'],['vivant','mer']]:
    history=[dict(question=s.upper()+'を先に紹介して。',answer=answers[s]) for s in order]
    for first in [True,False]:
        subject=order[0 if first else 1];ref='一番初めに聞いた' if first else '後から聞いた'
        add(f'2つの作品で、{ref}ほうの主演だけ聞かせてくれる？',subject+'-actor','context',history)
        add(f'2つの作品で、{ref}ほうは何局の何という放送枠なのかな。',subject+'-station','context',history)
for order in [['headphones','favorite-kyu'],['favorite-kyu','headphones']]:
    history=[dict(question=('Headphone1' if s=='headphones' else 'kyu camera')+'を紹介して。',answer=answers['headphone-spec'] if s=='headphones' else answers['favorite-kyu-weight']) for s in order]
    for first in [True,False]:
        subject=order[0 if first else 1];ref='最初' if first else '最後'
        add(f'2つの製品のうち、{ref}に紹介したほうは何gなのかな。',subject+'-weight','context',history)
for q in [
 '好きな映画を正式な作品名で聞かせてくれる？','愛読する小説のタイトルを聞かせてくれる？',
 '音楽で気に入っている歌手を、名前で教えてくれるかな。','お気に入りの楽曲名を具体的に聞きたいな。',
 '普段のパソコンの機種を型番で聞かせてくれる？','携帯電話の機種を型番で聞かせてくれる？',
 '写真撮影にいつも使うカメラは、どの機種なのかな。','通っている学校の正式名称を聞かせてくれる？',
 'Nothing Headphone (7)の重量をグラムで聞かせて。','Nothing Headphone (3)のBluetoothを聞かせて。',
 'CMF Buds Pro 5のノイキャン性能を聞かせて。','CMF Buds Pro 4の電池の容量を聞かせて。',
 'Beats Fit Proの本体が何gか、確認した数値で聞かせて。','CMF Budsの内蔵SSDは何GBか聞かせて。',
 '今この瞬間の仙台の気温を聞かせてくれる？','今この瞬間に福岡では雨が降っているのかな。']:add(q,kind='unknown',answer='その情報は分かりません。')
definitions=[
 ('constで宣言すると、再代入はどうなるのかな。','mdn-const'),('letが作る変数について、性質を聞かせて。','mdn-let'),
 ('JavaScriptのArrayは、どんなデータを扱うのかな。','mdn-array'),('Stringは、JavaScriptで何を扱うためのものなのかな。','mdn-string'),
 ('Mapは、JavaScriptでどんな組を保管するのかな。','mdn-map'),('Setは、JavaScriptでどんな値を保管するのかな。','mdn-set'),
 ('typeofで調べると、どんな値が返ってくるのかな。','mdn-typeof'),('Promiseが表す状態を、短く聞かせて。','mdn-promise'),
 ('HTMLのinputは、どんな入力部品を作るのかな。','mdn-input'),('HTMLのtextareaは、どんな入力に使うのかな。','mdn-textarea'),
 ('CSSのcolorでは、どこの色を指定するのかな。','mdn-color'),('CSSのfont-familyは、どんな順で何を指定するのかな。','mdn-font-family'),
 ('JavaScriptのObjectは、どんな組み合わせを表すのかな。','mdn-object'),('JavaScriptの関数は、どんなまとまりのコードなのかな。','mdn-関数'),
 ('JavaScriptのモジュールは、どのようにコードを分けるのかな。','mdn-モジュール'),('CSSのoverflow-wrapは、長い単語にどう作用するのかな。','mdn-overflow-wrap')]
for q,intent in definitions:add(q,intent,'web-knowledge')
for q,intent in [
 ('普段使うイヤホンは、製品名で数えると何種類になるのかな。','count-earphones'),
 ('普段使うヘッドホンは、製品名で数えると何種類になるのかな。','count-headphones'),
 ('イヤホンもヘッドホンもまとめて数えると、何機種になるのかな。','count-audio'),
 ('TOKYO MERとVIVANTでは、主演は同じ人物なのかな。名前も聞かせて。','drama-actor-comparison'),
 ('TOKYO MERとVIVANTでは、放送局と放送枠が同じなのかな。','drama-station-comparison'),
 ('Headphone1とkyu cameraは、重いほうと重さの差がどうなるのかな。','weight-comparison'),
 ('CMF BudsとHeadphone1では、Bluetoothの版がそろっているのかな。','bluetooth-comparison'),
 ('好きなドラマのタイトルを、ドラマだけに絞って聞かせてくれる？','favorite-dramas')]:add(q,intent,'reasoning')
held=[r for r in c['provenance']['arithmeticPairs'] if r['partition']=='test' and r['a']<=r['b']];random.Random(20261005).shuffle(held)
math=[]
for pair in held[:4]:
    a,b=pair['a'],pair['b'];add(f'箱に{a}個を入れました。さらに{b}個を入れたら、合計何個になるのかな。',kind='reasoning',answer=f'{a}+{b}={a+b}なので、合わせて{a+b}個です。');math.append(dict(id=rows[-1]['id'],a=a,b=b,bothOrdersTest=True))
for q,answer in [('こんにちは。これから少し聞かせてもらいたいな。','こんにちは。何について知りたい？'),('こんばんは。今から話を聞かせてくれるかな。','こんばんは。何について知りたい？'),('おはようございます。これから質問してもいいかな。','おはよう。何について知りたい？'),('分かりやすく答えてくれて、ありがとう。',answers['thanks'])]:add(q,kind='dialogue',answer=answer)
assert len(rows)==120,len(rows)
seen={tuple(r['tokens'][:r['prefixLength']]) for r in c['rows']}
for name in ['fresh-probe.json','binding-audit.json','continuous-audit.json','prefix-audit.json']:
    d=json.loads((HERE/name).read_text());seen.update(tuple(prompt(r['question'],r['history'],t)) for r in d['rows'])
for r in rows:
    prefix=prompt(r['question'],r['history'],t);assert tuple(prefix) not in seen,r['question'];seen.add(tuple(prefix))
    assert len(prefix)+len(encode_stream(r['answer'],t))+1<256
result=dict(schemaVersion=1,rows=rows,provenance=dict(frozenBeforeTraining=True,corpusSha256=c['sourceSha256'],selection='Author-defined120 questions, never used for fitting, weights or checkpoint selection. All earlier audits are development controls.',history='Gold-history diagnostic here; separate live probes append actual generated answers.',arithmetic=math,scope='Finite profile/spec/definitions/context/boundaries/arithmetic diagnostic, not representative general dialogue or independent human evaluation.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'switch-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(sourceSha256=result['sourceSha256'],total=len(rows),byKind=dict(__import__('collections').Counter(r['kind'] for r in rows))),ensure_ascii=False))
