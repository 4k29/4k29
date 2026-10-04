"""Freeze new real-language questions and held-out operand pairs before fitting."""
import hashlib
import json
import pathlib
from tokenizer import prompt,encode_stream
HERE=pathlib.Path(__file__).resolve().parent
c=json.loads((HERE/'continuous-corpus.json').read_text())
answers={r['intent']:r['answer'] for r in c['rows'] if r['partition']=='train'}
rows=[]
def add(q,intent,kind='profile',history=None,answer=None):
    rows.append(dict(id='continuous-audit:'+str(len(rows)),group='fresh:'+str(len(rows)),partition='test',question=q,history=history or [],answer=answer or answers[intent],kind=kind))
for q,intent in [
 ('名前の読み方も含めて、どう呼ぶといい？','name'),('学生かどうかを知りたいです。','role'),
 ('楽しみで続けていることは何がある？','hobbies'),('音を聴くとき、いつも使う製品はどれ？','audio'),
 ('お気に入りのものの名前を一覧で見せて。','favorites'),('記事を書く場所はどこなのかな？','tecirc'),
 ('Tecircの記事は何を題材にしている？','topics'),('走った距離の記録にどのアプリを使う？','running-app'),
 ('ランニングでは何という靴を履くの？','running-shoes'),('MERという作品を短く紹介してもらえる？','mer'),
 ('VIVANTのことを簡単に説明してくれる？','vivant'),('kyuのブランドがどんなものか聞かせて。','kyu'),
 ('headphone 1の全体的な仕様をまとめて説明して。','headphone-spec'),
 ('Nothing Headphone1は何グラムの本体なの？','headphones-weight'),
 ('headphone(1)で採用するドライバーはどんなもの？','headphones-driver'),
 ('Headphone1はBluetoothのどの版に対応している？','headphones-bluetooth'),
 ('Headphone(1)の音声コーデックの種類を挙げて。','headphones-codecs'),
 ('Headphone1はほこりと水に対して何等級なの？','headphones-resistance'),
 ('AACでANCをオンにしたまま聴く場合、Headphone1はどれくらい再生できる？','headphones-battery-aac-on'),
 ('LDACでANCを無効にした場合のHeadphone1の再生時間は？','headphones-battery-ldac-off'),
 ('CMF BudsのANCがどんな方式なのか知りたいな。','earphones-cmf-anc'),
 ('CMF Budsはノイキャンを切っておくと何時間再生できるの？','earphones-cmf-battery-off'),
 ('CMF BudsでANCを入れている場合の再生時間を聞きたい。','earphones-cmf-battery-on'),
 ('CMF Budsの電池そのものは本体とケースでどんな容量？','earphones-cmf-battery-capacity'),
 ('Beats Fit Proの水と汗への対応は？ケースも知りたい。','earphones-beats-resistance'),
 ('Beats Fit Proは短時間の充電でどれくらい聴けるのかな？','earphones-beats-fast-charging'),
 ('kyu cameraは何グラムの重量がある？','favorite-kyu-weight'),
 ('kyu cameraの前面動画はどんな解像度とフレームレート？','favorite-kyu-video-front'),
 ('kyu cameraの記憶容量はどれくらい用意されてる？','favorite-kyu-storage'),
 ('kyu cameraはどのような端子で充電する？','favorite-kyu-charging'),
 ]:add(q,intent)
intro=lambda name,answer:dict(question=name+'を紹介して。',answer=answer)
for h,q,intent in [
 ([intro('VIVANT',answers['vivant']),intro('MER',answers['mer'])],'あとで紹介した作品は誰が主演だった？','mer-actor'),
 ([intro('MER',answers['mer']),intro('VIVANT',answers['vivant'])],'二番目のドラマを主演している人は誰？','vivant-actor'),
 ([intro('趣味',answers['hobbies']),intro('MER',answers['mer']),dict(question='なるほど、ありがとう。',answer=answers['thanks'])],'さっきのドラマの主演をもう一度聞かせて。','mer-actor'),
 ([intro('音響機器',answers['audio']),intro('VIVANT',answers['vivant']),dict(question='教えてくれて助かった。',answer=answers['thanks'])],'そのドラマで主演を務める人は？','vivant-actor'),
 ([intro('VIVANT',answers['vivant']),intro('MER',answers['mer'])],'最後に紹介したドラマはどの局の何という枠？','mer-station'),
 ([intro('MER',answers['mer']),intro('VIVANT',answers['vivant'])],'今のドラマの放送局と枠を確認したい。','vivant-station'),
 ([intro('CMF Buds','CMF Budsです。'),intro('Headphone1',answers['headphone-spec'])],'最後に紹介したほうの重量はどのくらい？','headphones-weight'),
 ([intro('Headphone1',answers['headphone-spec']),intro('CMF Buds','イヤホンはCMF Budsを使っています。')],'二番目の製品のANCは何方式？','earphones-cmf-anc'),
 ([intro('学生',answers['role']),intro('VIVANT',answers['vivant']),intro('MER',answers['mer'])],'最後に話した作品の主演の名前を教えて。','mer-actor'),
 ([intro('学生',answers['role']),intro('MER',answers['mer']),intro('VIVANT',answers['vivant'])],'最後のドラマは誰が主演している？','vivant-actor'),
 ([intro('趣味',answers['hobbies']),intro('CMF Buds','CMF Budsです。'),intro('Headphone1',answers['headphone-spec']),dict(question='ありがとうね。',answer=answers['thanks'])],'最後に出てきた製品は何グラムだった？','headphones-weight'),
 ([intro('学生',answers['role']),intro('Headphone1','Nothing Headphone (1)です。'),intro('CMF Buds','CMF Budsです。'),dict(question='ありがとう。',answer=answers['thanks'])],'さっきのイヤホンのノイズキャンセルを教えて。','earphones-cmf-anc'),
 ]:add(q,intent,kind='context',history=h)
for q in [
 '好きなアニメの作品名は何なの？','いちばん好きな食べ物を聞かせてもらえる？','お気に入りの映画のタイトルは？',
 'よく聴くアーティストの名前を教えてほしい。','好きな小説のタイトルを知りたいな。','使っているスマホの型番を教えて。',
 '普段どのパソコンの機種を使ってるのかな？','撮影用に持っているカメラの型番はどれ？','現在通学している学校の名前を教えて。',
 'あなたの誕生日を年月日で教えてください。','住まいの住所はどこなの？','今この瞬間、東京で降水はある？',
 'あした大阪で傘が必要になるか教えて。','CMF Buds Pro 3のノイキャンはどうなっている？','Nothing Headphone (5)は何グラムある？',
 'Beats Fit Proのドライバー径はいくつ？','CMF Budsに内蔵されたストレージは何GB？','Headphone1を何円で買ったのか教えて。',
 ]:add(q,'unknown-extra',kind='unknown',answer='その情報は分かりません。')
for q,intent in [
 ('雪の白さはどんな理由で生まれるの？','definition-snow-white'),
 ('平均風速という値と瞬間風速という値はどう違うのですか？','definition-wind'),
 ('夏日と真夏日と猛暑日の境目はそれぞれ何度？','definition-hot-days'),
 ('どんな最低気温の夜が熱帯夜に当たるの？','definition-tropical-night'),
 ('constで宣言した変数ってどういうもの？','mdn-const'),('letが宣言するものはどんな変数？','mdn-let'),
 ('JavaScriptのArrayが表しているものを説明して。','mdn-array'),('StringはJavaScriptで何を扱う？','mdn-string'),
 ('キーと値を保存するMapの役割は？','mdn-map'),('JavaScriptのSetは何を保存できるもの？','mdn-set'),
 ('typeofという演算子は何を返すのかな？','mdn-typeof'),('関数という仕組みは何をするもの？','mdn-関数'),
 ('Promiseの役目を短く説明してくれる？','mdn-promise'),('HTMLのtextareaはどんな入力欄？','mdn-textarea'),
 ('CSSのcolorというプロパティは何を指定する？','mdn-color'),('font-familyはCSSで何の順番を指定するの？','mdn-font-family'),
 ]:add(q,intent,kind='web-knowledge')
for q,intent in [
 ('使っているイヤホンを機種の数で数えると、何種類になる？','count-earphones'),
 ('使っている音響機器の製品名は、全部で何種類挙げられる？','count-audio'),
 ('普段使うヘッドホンの機種は何種類になるの？','count-headphones'),
 ('MERとVIVANTは主演の俳優が同一なのか知りたい。','drama-actor-comparison'),
 ('VIVANTとTOKYO MERって放送局も枠も同じなの？','drama-station-comparison'),
 ('kyu cameraとNothing Headphone1の重量差と重いほうを教えて。','weight-comparison'),
 ('CMF BudsとNothing Headphone1をBluetoothの版で比べると？','bluetooth-comparison'),
 ]:add(q,intent,kind='reasoning')
held=[r for r in c['provenance']['arithmeticPairs'] if r['partition']=='test']
held.sort(key=lambda r:hashlib.sha256(f'fresh-probe:{r["a"]}:{r["b"]}'.encode()).hexdigest())
for case in held[:13]:
    a,b=case['a'],case['b'];q=f'{a}個を持っていて、{b}個を受け取りました。合計で何個持つことになる？'
    add(q,'addition',kind='reasoning',answer=f'{a}+{b}={a+b}なので、合わせて{a+b}個です。')
for q,intent in [('こんにちは、少し聞いてもいいかな。','greeting'),('そういうことか、どうもありがとう。','thanks'),('こんばんは、よろしくお願いします。','greeting'),('説明してくれて助かりました、ありがとう。','thanks')]:add(q,intent,kind='dialogue')
known={tuple(r['tokens'][:r['prefixLength']]) for r in c['rows']}
for old in ['new-challenge.json','binding-audit.json']:
    for r in json.loads((HERE/old).read_text())['rows']:known.add(tuple(prompt(r['question'],r['history'],c['tokenizer'])))
for r in rows:
    p=prompt(r['question'],r['history'],c['tokenizer'])
    if tuple(p) in known:raise ValueError('Audit input was used previously: '+r['question'])
    if len(p)+len(encode_stream(r['answer'],c['tokenizer']))+1>256:raise ValueError('Audit full gold exceeds context')
result=dict(schemaVersion=1,rows=rows,provenance=dict(frozenBeforeTraining=True,corpusSha256=c['sourceSha256'],selection='Never used for vocabulary, weights or checkpoint selection. Prior 38/60 probes informed development and remain diagnostics.',coverage='Finite authored profile/spec/context/scope/MDN/grounded-reasoning diagnostic. Synthetic arithmetic operands are held out from QA training; no general reasoning benchmark is claimed.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'continuous-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(total=len(rows),sourceSha256=result['sourceSha256'])))
