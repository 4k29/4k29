"""Freeze actual-history topic switching conversations before training."""
import hashlib,json,pathlib,unicodedata
HERE=pathlib.Path(__file__).resolve().parent
c=json.loads((HERE/'switch-corpus.json').read_text());answers={r['intent']:r['answer'] for r in c['rows'] if r['partition']=='train'}
def turn(q,intent=None,answer=None):return dict(question=q,answer=answer if answer is not None else answers[intent])
conversations=[
 [turn('初めにMERというドラマを紹介してくれるかな。','mer'),turn('今度はあなたの身分を一言で答えてくれる？','role'),turn('話を戻すと、MERの主演俳優はどなたなのかな。','mer-actor')],
 [turn('まずVIVANTの作品紹介を聞かせてくれるかな。','vivant'),turn('今度は趣味として取り組む活動を聞きたいな。','hobbies'),turn('それでは、VIVANTの主演を名前で聞かせて。','vivant-actor')],
 [turn('こんばんは。少し質問をしてもいいかな。',answer='こんばんは。何について知りたい？'),turn('あなたが名乗る名前と読み仮名を聞かせて。','name'),turn('次は、現在の立場を短く教えてくれるかな。','role'),turn('今度は余暇に取り組む趣味を聞かせて。','hobbies')],
 [turn('最初に何を気に入っているか、名称だけ挙げてくれるかな。','favorites'),turn('続いて、Tecircで取り組む活動を聞かせて。','tecirc'),turn('今度は、kyuというブランドの紹介を聞きたいな。','kyu')],
 [turn('最初にNothing Headphone1の主要な仕様を紹介してくれる？','headphone-spec'),turn('次は、kyu cameraが何gなのか聞きたいな。','favorite-kyu-weight'),turn('さっき先に紹介した製品の重量を聞き直したいな。','headphones-weight')],
 [turn('まずkyu cameraの重量をグラムで聞きたいな。','favorite-kyu-weight'),turn('続いてNothing Headphone1を、主な仕様を含めて紹介してくれる？','headphone-spec'),turn('先に質問したカメラの重量を、もう一度聞きたいな。','favorite-kyu-weight')],
 [turn('音楽を聴くときの機器を、製品名で全部聞かせてくれるかな。','audio'),turn('話は変わるけれど、書いている記事のテーマを聞かせて。','topics'),turn('音楽の話に戻ると、イヤホンとヘッドホンは何を愛用するのかな。','audio')],
 [turn('最初にCMF Budsのノイズキャンセリングの性能を聞かせて。','earphones-cmf-anc'),turn('その次にCMF Buds Pro 5の性能を聞かせてくれる？',answer='その情報は分かりません。'),turn('元のCMF BudsのANCは、何方式で何dBなのかな。','earphones-cmf-anc')],
 [turn('初めにMERの主演と放送枠を聞かせてくれる？','mer'),turn('次にVIVANTの主演と放送枠を聞かせてくれる？','vivant'),turn('今の2作品で、後に紹介したほうの主演を聞き直したいな。','vivant-actor')],
 [turn('最初はVIVANTの主演と放送枠を聞かせてくれる？','vivant'),turn('今度はMERの主演と放送枠を聞かせてくれる？','mer'),turn('今の2作品で、先に紹介したほうの主演を聞き直したいな。','vivant-actor')],
 [turn('JavaScriptのArrayが何に使うものか、最初に聞かせて。','mdn-array'),turn('次はHTMLのtextareaが何に使うものか聞きたいな。','mdn-textarea'),turn('ところで、あなたがどんな立場の人なのか聞きたいな。','role')],
 [turn('おはようございます。少し話を聞いてもいいかな。',answer='おはよう。何について知りたい？'),turn('次に、走った記録を付けるアプリを聞かせて。','running-app'),turn('続いて、走るときに履くシューズの名前を聞きたいな。','running-shoes'),turn('聞きたかったことが分かったよ。教えてくれてありがとう。','thanks')]
]
normal=lambda q:unicodedata.normalize('NFKC',q).lower()
seen={normal(r['question']) for r in c['rows']};seen.update(normal(r['question']) for r in json.loads((HERE/'switch-audit.json').read_text())['rows'])
for conversation in conversations:
    for t in conversation:
        assert normal(t['question']) not in seen,t['question'];seen.add(normal(t['question']))
result=dict(schemaVersion=1,conversations=[dict(id='switch-rollout:'+str(i),turns=turns) for i,turns in enumerate(conversations)],provenance=dict(corpusSha256=c['sourceSha256'],frozenBeforeTraining=True,frozenBeforeCandidateEvaluation=True,history='Actual complete valid generated answers only, never inject gold as history.',selection='Never used in fitting, training or checkpoint selection.',scope='Twelve authored conversations, not representative general dialogue or independent human assessment.'))
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'switch-rollouts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(conversations=len(conversations),turns=sum(map(len,conversations)),sourceSha256=result['sourceSha256'])))
