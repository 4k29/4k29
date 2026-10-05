"""Freeze live dialogue probes before looking at candidate outputs.

These use the model's own answers as subsequent history, unlike idealized
gold-history audits. The probes do not train or select a checkpoint.
"""
import hashlib
import json
import pathlib
import unicodedata
HERE=pathlib.Path(__file__).resolve().parent
c=json.loads((HERE/'prefix-corpus.json').read_text());answers={r['intent']:r['answer'] for r in c['rows'] if r['partition']=='train'}
def turn(q,intent=None,answer=None):return dict(question=q,answer=answer if answer is not None else answers[intent])
conversations=[
 [turn('MERのことを、まず概要だけ紹介してください。','mer'),turn('次にVIVANTというドラマの基本情報を教えてください。','vivant'),turn('いまの2作のうち、後で取り上げた作品の主演俳優を答えて。','vivant-actor')],
 [turn('最初にVIVANTの簡単な紹介をお願い。','vivant'),turn('続いてMERを短く紹介してください。','mer'),turn('2つの作品のうち、先に取り上げた作品の主演俳優だけ答えて。','vivant-actor')],
 [turn('TOKYO MERについて基本情報を聞かせてください。','mer'),turn('丁寧に教えてくれてありがとう。','thanks'),turn('先ほどのドラマを主演している方はどなたでしたか。','mer-actor')],
 [turn('VIVANTの基本情報を最初に聞かせて。','vivant'),turn('今度は、あなたがどんな立場なのか教えて。','role'),turn('立場の前に紹介してくれたドラマの主演を聞きたい。','vivant-actor')],
 [turn('Headphone1の主要な性能を最初にまとめてください。','headphone-spec'),turn('その次に、kyu cameraの重量を教えてください。','favorite-kyu-weight'),turn('今の2製品のうち、先に出たほうの重さだけ教えて。','headphones-weight')],
 [turn('まずkyu cameraの重量を聞かせて。','favorite-kyu-weight'),turn('続いてHeadphone1の主な仕様をまとめて。','headphone-spec'),turn('2番目に出てきた製品は何グラムの重さですか。','headphones-weight')],
 [turn('普段音楽を聴く道具の製品名をまとめて紹介して。','audio'),turn('そのうちイヤホンの機種数だけ答えてください。','count-earphones'),turn('最初に挙げた音響機器を、もう一度製品名でまとめて。','audio')],
 [turn('CMF BudsのANC方式を最初に教えて。','earphones-cmf-anc'),turn('CMF Buds Pro 4の仕様は確認できますか。',answer='その情報は分かりません。'),turn('初めに聞いたCMF BudsのANC方式をもう一度答えて。','earphones-cmf-anc')],
 [turn('こんばんは。少しお話を聞いてもいいですか。',answer='こんばんは。何について知りたい？'),turn('あなたの名前を読み方も添えて答えて。','name'),turn('楽しんでいる趣味を挙げてほしいです。','hobbies'),turn('いろいろ答えてくれて感謝しています。','thanks')],
 [turn('最初に好きなものを名前で挙げてもらえますか。','favorites'),turn('その中のkyuは何を展開しているブランドですか。','kyu'),turn('あなたの好きなドラマだけを名称でまとめてください。','favorite-dramas')]
]
known={unicodedata.normalize('NFKC',r['question']).lower() for r in c['rows']}
known.update(unicodedata.normalize('NFKC',r['question']).lower() for r in json.loads((HERE/'prefix-audit.json').read_text())['rows'])
for conversation in conversations:
    for t in conversation:
        key=unicodedata.normalize('NFKC',t['question']).lower()
        if key in known:raise ValueError('Repeated live question '+t['question'])
        known.add(key)
result=dict(schemaVersion=1,conversations=[dict(id='prefix-rollout:'+str(i),turns=turns) for i,turns in enumerate(conversations)],provenance=dict(corpusSha256=c['sourceSha256'],frozenBeforeCandidateEvaluation=True,frozenAfterTrainingStart=True,selection='Created before inspecting candidate audit answers; never supplies data, losses, tokenizer counts or checkpoint selection.',history='Append only actually generated complete valid answers, matching chat.mjs; never inject gold history.',scope='Ten authored conversations, not a representative natural dialogue benchmark.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'prefix-rollouts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(conversations=len(conversations),turns=sum(map(len,conversations)),sourceSha256=result['sourceSha256'])))
