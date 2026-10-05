"""Freeze 100 new prompts and truly unordered-held-out sums before training."""
import hashlib
import json
import pathlib
import random
from tokenizer import prompt,encode_stream
HERE=pathlib.Path(__file__).resolve().parent
c=json.loads((HERE/'prefix-corpus.json').read_text());t=c['tokenizer']
answers={r['intent']:r['answer'] for r in c['rows'] if r['partition']=='train'}
rows=[]
def add(q,intent=None,kind='profile',history=None,answer=None):
    rows.append(dict(id='prefix-audit:'+str(len(rows)),group='prefix-fresh:'+str(len(rows)),partition='test',kind=kind,question=q,history=history or [],answer=answer if answer is not None else answers[intent]))
for q,i in [
 ('自己紹介の名前を読み仮名込みで聞きたい。','name'),('いまの身分について短く答えてください。','role'),
 ('余暇に楽しむことを挙げるなら何？','hobbies'),('音楽を聴く際の愛用機器をまとめて挙げて。','audio'),
 ('好きなものは何か、名称だけで答えてください。','favorites'),('Tecircではどのような活動をしていますか。','tecirc'),
 ('あなたが記事にするテーマを聞きたい。','topics'),('走った記録は何のアプリにつけていますか。','running-app'),
 ('走るときに選ぶシューズの製品名は？','running-shoes'),('MERについて、基本情報を一言で聞きたい。','mer'),
 ('VIVANTの基本的な紹介を聞きたいです。','vivant'),('kyuが手がけるものを短く説明して。','kyu'),
 ('Nothing Headphone1を紹介する形で主要な仕様をまとめて。','headphone-spec'),
 ('Headphone 1本体の重量はgでいくつ？','headphones-weight'),('Headphone (1)のドライバーの方式と口径を教えて。','headphones-driver'),
 ('Nothing Headphone1の無線接続はBluetooth何番？','headphones-bluetooth'),('Headphone1が対応する音声コーデックを列挙して。','headphones-codecs'),
 ('Headphone1の防塵防水の等級を聞きたいです。','headphones-resistance'),
 ('Headphone1でAACを選択し、ANCを使用して再生すると、最長で何時間？','headphones-battery-aac-on'),
 ('Headphone1でAACを選択し、ANCを停止して再生すると、最長で何時間？','headphones-battery-aac-off'),
 ('Headphone1でLDACを選択し、ANCを使用して再生すると、最長で何時間？','headphones-battery-ldac-on'),
 ('Headphone1でLDACを選択し、ANCを停止して再生すると、最長で何時間？','headphones-battery-ldac-off'),
 ('CMF BudsにあるANCは何dBの何方式？','earphones-cmf-anc'),
 ('CMF BudsはANCを止めると単体とケース込みで何時間聴ける？','earphones-cmf-battery-off'),
 ('CMF BudsはANCを使用すると単体とケース込みで何時間聴ける？','earphones-cmf-battery-on'),
 ('CMF Budsの本体とケースそれぞれの電池容量を聞きたい。','earphones-cmf-battery-capacity'),
 ('Beats Fit Proのイヤホンとケースはそれぞれ防水なの？','earphones-beats-resistance'),
 ('Beats Fit Proを急速充電する場合の時間と再生量は？','earphones-beats-fast-charging'),
 ('kyu camera本体がどれほどの重量か聞きたい。','favorite-kyu-weight'),
 ('kyu cameraでフロント側を撮る動画の仕様を教えて。','favorite-kyu-video-front'),
 ('kyu cameraの内部ストレージは何GBある？','favorite-kyu-storage'),
 ('kyu cameraの給電に使う接続端子は何ですか。','favorite-kyu-charging')]:add(q,i)

intro=lambda name,answer:dict(question=name+'を簡単に紹介してください。',answer=answer)
for order in [['mer','vivant'],['vivant','mer']]:
    for layout in range(2):
        h=[intro(s.upper(),answers[s]) for s in order]
        if layout:h.insert(0,intro('立場',answers['role']));h.append(dict(question='説明、助かりました。',answer=answers['thanks']))
        for first in [True,False]:
            subject=order[0 if first else 1];reference='先に出てきたほう' if first else 'あとから出てきたほう'
            add(f'いま挙げた2作品のうち、{reference}の主演は誰でしたか。',subject+'-actor','context',h)
            add(f'いま挙げた2作品のうち、{reference}はどの局のどの放送枠でしたか。',subject+'-station','context',h)
for order in [['headphones','favorite-kyu'],['favorite-kyu','headphones']]:
    names={'headphones':'Headphone1','favorite-kyu':'kyu camera'}
    h=[intro(names[s],answers['headphone-spec'] if s=='headphones' else answers['favorite-kyu-weight']) for s in order]
    for first in [True,False]:
        subject=order[0 if first else 1];ref='先に聞いた製品' if first else '後で聞いた製品'
        add(f'さっきの{ref}の重量を、もう一度gで答えて。',subject+'-weight','context',h)

for q in [
 '好きな映画を作品名で教えてもらえますか。','好きな小説の作品名を聞きたい。','愛聴する歌手の名前を挙げて。','気に入っている曲の曲名を聞きたい。',
 'いつも使うパソコンを型番で教えて。','愛用するスマホを型番で教えて。','あなたが写真を撮るカメラ本体の機種名は？','あなたの学校が何という名前なのか知りたい。',
 'Headphone (9)という機種のドライバーを教えて。','Nothing Headphone (0)の電池持ちは？','CMF Buds Pro 4のANC方式を教えて。','CMF Buds Pro 3の電池容量を聞きたい。',
 'Beats Fit Proの未確認の重量を数値で知りたい。','CMF BudsにあるとされるSSDの容量は？','今この時点で札幌に雨は降っていますか。','いま大阪は何度の気温ですか。'
 ]:add(q,kind='unknown',answer='その情報は分かりません。')
for q,i in [
 ('JavaScriptでconstを使うと何が固定されるの？','mdn-const'),('JavaScriptでletが宣言する変数の特徴は？','mdn-let'),
 ('JavaScriptにおけるArrayの用途を知りたい。','mdn-array'),('JavaScriptのStringはどんな情報を表すの？','mdn-string'),
 ('MapというJavaScriptの機能は何を保存する？','mdn-map'),('SetというJavaScriptの機能は何を保存する？','mdn-set'),
 ('typeofの返す結果がどんなものか説明して。','mdn-typeof'),('Promiseが意味する処理の状態は？','mdn-promise'),
 ('HTMLのinputは何を作るための要素ですか。','mdn-input'),('textareaが入力できる文字列はどのようなもの？','mdn-textarea'),
 ('CSSでcolorを使うと何の色を決めるの？','mdn-color'),('CSSでfont-familyを使うと何を優先順にするの？','mdn-font-family')]:add(q,i,'web-knowledge')
for q,i in [
 ('イヤホンの登録された製品は合計何種類ありますか。','count-earphones'),('ヘッドホンの登録された製品は合計何種類ありますか。','count-headphones'),
 ('イヤホンとヘッドホンを合わせた機種の合計はいくつ？','count-audio'),('MERとVIVANTの主演俳優が共通か、名前込みで答えて。','drama-actor-comparison'),
 ('MERとVIVANTのテレビ局と放送枠は共通ですか。','drama-station-comparison'),('kyu cameraとHeadphone1の重量差と重いほうを教えて。','weight-comparison'),
 ('Headphone1とCMF BudsのBluetoothバージョンが一致するか答えて。','bluetooth-comparison'),('お気に入りのドラマを作品名だけで一覧にして。','favorite-dramas')]:add(q,i,'reasoning')
held=[p for p in c['provenance']['arithmeticPairs'] if p['partition']=='test' and p['a']<=p['b']];random.Random(429).shuffle(held)
arithmetic=[]
for p in held[:8]:
    a,b=p['a'],p['b'];add(f'手元に{a}個あります。そこへ{b}個をもらったので、合わせていくつになった？',kind='reasoning',answer=f'{a}+{b}={a+b}なので、合わせて{a+b}個です。');arithmetic.append(dict(id=rows[-1]['id'],a=a,b=b,bothOrdersTest=True))
for q,answer in [
 ('こんにちは。お話を少し聞きたいです。','こんにちは。何について知りたい？'),
 ('こんばんは。質問させてもらってもいいですか。','こんばんは。何について知りたい？'),
 ('おはようございます。聞きたいことがあるんです。','おはよう。何について知りたい？'),
 ('教えてもらえて助かりました。ありがとう。',answers['thanks'])]:add(q,kind='dialogue',answer=answer)
assert len(rows)==100,len(rows)
seen={tuple(r['tokens'][:r['prefixLength']]) for r in c['rows']}
for name in ['fresh-probe.json','binding-audit.json','continuous-audit.json']:
    a=json.loads((HERE/name).read_text());seen.update(tuple(prompt(r['question'],r['history'],t)) for r in a['rows'])
for r in rows:
    p=prompt(r['question'],r['history'],t)
    if tuple(p) in seen:raise ValueError('Repeated frozen/input question: '+r['question'])
    seen.add(tuple(p));assert len(p)+len(encode_stream(r['answer'],t))+1<=192
result=dict(schemaVersion=1,rows=rows,provenance=dict(frozenBeforeTraining=True,corpusSha256=c['sourceSha256'],selection='Never used for tokenizer, model weights or checkpoint selection. All prior audits are development.',coverage='Finite authored profile/spec/context/unknown/MDN/comparison/arithmetic diagnostic, not a representative chat benchmark.',arithmetic=arithmetic,arithmeticSplit='Both operand orders excluded from QA training and validation. Values themselves occur in training; bounded 0-20 addition is not general reasoning.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'prefix-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(questions=len(rows),sourceSha256=result['sourceSha256'],kinds={kind:sum(r['kind']==kind for r in rows) for kind in sorted({r['kind'] for r in rows})}),ensure_ascii=False))
