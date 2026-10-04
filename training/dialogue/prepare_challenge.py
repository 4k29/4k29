"""Freeze a new small diagnostic, never consumed by a trainer/tokenizer fitter.

Two candidate weights and the replay candidate's data/config are fixed first.
Expected factual prose comes from approved source labels; no model writes gold.
"""
import datetime
import hashlib
import json
import pathlib

HERE=pathlib.Path(__file__).resolve().parent
base=json.loads((HERE/'generalization-corpus.json').read_text())
web=json.loads((HERE/'web-curriculum-corpus.json').read_text())
gold={r['intent']:r['answer'] for r in base['rows']}
rows=[]
def add(question,answer,kind='profile',history=None):
    rows.append(dict(id='new-challenge:'+str(len(rows)),group='new-challenge:'+str(len(rows)),partition='test',kind=kind,question=question,answer=answer,history=history or []))
for intent,question in [
 ('name','あなたを何と呼べばいいかな？'),('role','普段は何をしている人ですか？'),
 ('hobbies','趣味を二つ教えてほしい。'),('audio','いつも音楽は何を使って聴いているの？'),
 ('favorites','お気に入りの名前だけ聞かせて。'),('tecirc','Tecircには何をして関わっているの？'),
 ('topics','Tecircで書く記事はどんな話題が中心？'),('running-app','走った記録を残すのに使うアプリはどれ？'),
 ('running-shoes','ランニングのときはどのシューズを履くの？'),('mer','merってどういうドラマなの？'),
 ('vivant','vivantを簡単に説明してくれる？'),('kyu','kyuのブランドについて聞きたい。'),
 ('headphones-weight','Headphone 1って何グラムあるの？'),('headphones-driver','Headphone (1)に載っているドライバーを教えて。'),
 ('headphones-codecs','nothing headphone(1)で使える音声コーデックは？'),('earphones-cmf-battery-off','CMF BudsでANCを切った場合の電池持ちを教えて。'),
 ('earphones-cmf-anc','CMF Budsはどんなノイズキャンセルを使う？'),('earphones-beats-resistance','Beats Fit Proの耐水性能とケースの対応を聞かせて。'),
 ]:add(question,gold[intent])
for question,history,answer in [
 ('そのドラマの主演の名前を聞かせて。',[dict(question='VIVANTは？',answer=gold['vivant'])],gold['vivant-actor']),
 ('今話したほうの主演は誰ですか？',[dict(question='VIVANTは？',answer=gold['vivant']),dict(question='MERについて。',answer=gold['mer'])],gold['mer-actor']),
 ('それはどの放送枠？',[dict(question='MERは？',answer=gold['mer'])],gold['mer-station']),
 ('そのヘッドホンの重量も知りたい。',[dict(question='Headphone1のスペックは？',answer=gold['headphone-spec'])],gold['headphones-weight']),
 ]:add(question,answer,'context',history)
web_gold={r['question']:r for r in web['rows'] if r['kind']=='web-qa' and not r['question'].startswith(('教えてほしい。','ねえ、','質問です。'))}
for fragment,question in [
 ('雪の色','雪が白く見える理由を教えてほしい。'),('風速」と','平均風速と瞬間風速って何が違うの？'),
 ('初雪とは','初雪はどういう意味の言葉？'),('初冠雪','山の初冠雪ってどんな状態？'),
 ('猛暑日','猛暑日や夏日は何度からなの？'),('熱帯夜','熱帯夜ってどんな夜を指すの？'),
 ]:
    matches=[r for q,r in web_gold.items() if fragment in q]
    if len(matches)!=1:raise ValueError('Ambiguous source gold: '+fragment)
    add(question,matches[0]['answer'],'web-knowledge')
for question in ['あなたの誕生日を月と日で知りたい。','普段使っているカメラの機種は？','Nothing Headphone (3)の重さを教えて。','CMF Buds Proの電池持ちはどのくらい？','今使っているイヤホンをどこで買ったの？','現在、東京では雨が降っていますか？','いま通っている学校はどこなの？','友人が使っているイヤホンの型番を知りたい。']:add(question,'その情報は分かりません。','unknown')
add('こんばんは。よろしく！','こんにちは。何について知りたい？','dialogue')
add('丁寧に教えてくれてありがとう。','どういたしまして。','dialogue')
result=dict(schemaVersion=1,rows=rows,provenance=dict(createdAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidateDataAndConfigFixed=True,authoredModelSha256=hashlib.sha256((HERE/'generalization-candidate.js').read_bytes()).hexdigest(),webModelSha256=hashlib.sha256((HERE/'web-curriculum-candidate.js').read_bytes()).hexdigest(),replayCorpusSha256=web['sourceSha256'],note='New engineer-defined diagnostic paraphrases. Never fit vocabulary, train or select checkpoints. Earlier failures inform its chosen topics, so this is a challenge set rather than an unbiased population benchmark. Replay learning-rate/data/replay configuration is fixed before writing questions.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'new-challenge.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(total=len(rows),byKind={k:sum(r['kind']==k for r in rows) for k in sorted({r['kind'] for r in rows})},sha256=result['sourceSha256'])))
