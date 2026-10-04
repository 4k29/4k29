"""Freeze authored new questions before binding training, never select weights."""
import hashlib
import json
import pathlib
from tokenizer import prompt
HERE=pathlib.Path(__file__).resolve().parent
corpus=json.loads((HERE/'binding-corpus.json').read_text())
answers={r['intent']:r['answer'] for r in corpus['rows'] if r['partition']=='train'}
cases=[]
def add(q,intent,kind='profile',history=None,answer=None):
    cases.append(dict(id='binding-audit:'+str(len(cases)),question=q,answer=answer or answers[intent],history=history or [],kind=kind,partition='test',group='independent-audit:'+str(len(cases))))
for q,intent in [
 ('どう呼べばいいかな？','name'),('あなたはいま学生、それとも社会人？','role'),
 ('仕事や活動とは別に、趣味を教えてもらえる？','hobbies'),('何で音楽を聴くことが多い？','audio'),
 ('使ってるヘッドホンやイヤホンの名前をまとめて知りたい。','audio'),('気に入ってるもの、名前を並べてみて。','favorites'),
 ('Tecircとはどんな関わりがあるのかな？','tecirc'),('Tecircで書く記事のジャンルを知りたいな。','topics'),
 ('走る記録はどのアプリにつけてるの？','running-app'),('走るとき、足元はどんなシューズ？','running-shoes'),
 ('merってどんなドラマだったっけ？','mer'),('vivantというドラマを紹介して。','vivant'),
 ('VIVANTの主役を演じる人は誰？','vivant-actor'),('TOKYO MERは何局の日曜劇場？','mer-station'),
 ('kyuというブランドについて説明して。','kyu'),('NothingのHeadphone1について、特徴をまとめてもらえる？','headphone-spec'),
 ('Headphone 1は重い？重量の数字を知りたい。','headphones-weight'),
 ('nothing headphone1に入っているドライバーの仕様は？','headphones-driver'),
 ('Headphone1はどんなBluetoothのバージョンで接続する？','headphones-bluetooth'),
 ('Nothing Headphone(1)は水やほこりにどこまで対応してる？','headphones-resistance'),
 ('Headphone1で選べる音声コーデックは何がある？','headphones-codecs'),
 ('AACでノイキャンを切って聴くと、Headphone1は何時間使える？','headphones-battery-aac-off'),
 ('LDACでノイキャンを入れて聴くと、Headphone1は何時間もつ？','headphones-battery-ldac-on'),
 ('CMF Budsのノイズキャンセルはどんな性能なのかな？','earphones-cmf-anc'),
 ('CMF Budsのノイキャンを無効にしたまま、どれくらい聴ける？','earphones-cmf-battery-off'),
 ('ノイキャンを使いながら聴くと、CMF Budsは何時間もつ？','earphones-cmf-battery-on'),
 ('CMF Budsの電池の容量は、イヤホン側とケース側でそれぞれいくつ？','earphones-cmf-battery-capacity'),
 ('CMF Budsは充電台に置いて無線で充電できるの？','earphones-cmf-wireless-charging'),
 ('CMF Budsで2台の機器に同時につなぐにはどうする？','earphones-cmf-multipoint'),
 ('Beats Fit Proは汗や水に対応してる？ケースも含めて知りたい。','earphones-beats-resistance'),
 ('Beats Fit Proにはノイズキャンセルが付いてるかな？','earphones-beats-anc'),
 ('Beats Fit Proを少しだけ充電したときは、どれくらい再生できる？','earphones-beats-fast-charging'),
 ('kyuのカメラは記録用に何GB入っているの？','favorite-kyu-storage'),
 ('kyu cameraは本体だけで何グラムくらい？','favorite-kyu-weight'),
 ('kyu cameraで前側の動画を撮るときの仕様を知りたい。','favorite-kyu-video-front'),
 ('kyuのカメラを充電する端子って何？','favorite-kyu-charging'),
 ]:add(q,intent)
for before,last,q,intent in [
 ('VIVANTです。',answers['mer'],'じゃあ、いま紹介した作品は誰が主演？','mer-actor'),
 (answers['mer'],answers['vivant'],'直前の作品で主演しているのは誰？','vivant-actor'),
 ('CMF Budsです。','Nothing Headphone (1)です。','最後の製品について、重さを教えて。','headphones-weight'),
 ('Nothing Headphone (1)です。','CMF Budsです。','いまの製品のノイキャンの性能はどんな感じ？','earphones-cmf-anc'),
 ]:
    add(q,intent,kind='context',history=[dict(question='最初の紹介は？',answer=before),dict(question='次の紹介は？',answer=last)])
for q in [
 '撮影するときのカメラはどのメーカーの何という機種？','通っている学校の名称まで教えてくれる？',
 '誕生した年月日を知りたいな。','住んでいる番地を教えて。',
 '今この瞬間の東京は晴れている？','あしたの大阪で傘は必要？',
 'Nothing Headphone (4)の重さはどのくらい？','CMF Buds ProのANC性能を説明して。',
 'Beats Fit Proの重量の数値を教えて。','CMF Budsには何GBのストレージがある？',
 '使っているカメラを買った日付は？','友達が使っているイヤホンの製品名を教えて。',
 ]:add(q,'unknown-field',kind='unknown',answer='その情報は分かりません。')
for q,intent in [
 ('雪が白色に見えるのはどういう光の作用なの？','definition-snow-white'),
 ('平均の風速と瞬間の風速は、測る時間がどう違う？','definition-wind'),
 ('夏日、真夏日、猛暑日はそれぞれ何℃で区切るの？','definition-hot-days'),
 ('熱帯夜って、夜の温度がどうなっている場合？','definition-tropical-night'),
 ]:add(q,intent,kind='web-knowledge')
for q,intent in [('おはよう、よろしくね。','greeting'),('なるほど、教えてくれてありがとう！','thanks')]:add(q,intent,kind='dialogue')
add('登録しているイヤホンの機種は合計いくつ？','audio',kind='reasoning',answer='2機種です。')
add('MERとVIVANTは同じ主演俳優なの？','mer',kind='reasoning',answer='主演は異なります。TOKYO MERは鈴木亮平さん、VIVANTは堺雅人さんです。')
prefixes={tuple(r['tokens'][:r['prefixLength']]) for r in corpus['rows']}
for r in cases:
    prefix=prompt(r['question'],r['history'],corpus['tokenizer'])
    if tuple(prefix) in prefixes:raise ValueError('Audit question already in corpus: '+r['question'])
    if len(prefix)>=128:raise ValueError('Audit history overflows context')
result=dict(schemaVersion=1,rows=cases,provenance=dict(frozenBeforeTraining=True,bindingCorpusSha256=corpus['sourceSha256'],labels='Authored new questions using approved profile/spec facts and attributed government definitions. No candidate output supplies labels.',selection='Not read by training, tokenizer fitting or validation checkpoint selection. Finite diagnostic, not a general benchmark.',previousChallenge='The former 38 questions informed development and are no longer independent.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'binding-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(total=len(cases),sourceSha256=result['sourceSha256'])))
