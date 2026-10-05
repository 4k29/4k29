"""Freeze author-defined current-profile controls before continued fitting."""
import collections,copy,hashlib,json,pathlib,re,unicodedata
from tokenizer import SPECIALS,prompt,encode_stream
HERE=pathlib.Path(__file__).resolve().parent
def normal(text):return unicodedata.normalize('NFKC',text).lower()
def write(name,result):
    result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    (HERE/name).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result['sourceSha256']
def main():
    c=json.loads((HERE/'owner-aligned-corpus.json').read_text());t=c['tokenizer']
    answers={r['intent']:r['answer'] for r in c['rows'] if r['partition']=='train'}
    forbidden={normal(r['question']) for r in c['rows']}
    for name in ['switch-audit.json','fresh-probe.json','binding-audit.json','continuous-audit.json','prefix-audit.json','switch-rollouts.json','prefix-rollouts.json']:
        d=json.loads((HERE/name).read_text());forbidden.update(normal(r['question']) for r in d.get('rows',[]));forbidden.update(normal(r['question']) for conv in d.get('conversations',[]) for r in conv['turns'])
    profile=[
      ('Appleという名前だけ送った場合にも、日本語で関心を答えてくれる？','interest-apple'),
      ('Nothingへの興味について、日本語でひとこと聞かせてもらいたい。','interest-nothing'),
      ('OpenAIに関心があるか、あなたの答えを聞かせてもらいたい。','interest-openai'),
      ('テクノロジーに興味があるか、短い文章で聞かせてほしい。','interest-tech'),
      ('UIとUXに関するあなたの関心をひとことで聞かせて。','interest-ui'),
      ('デザインへの関心はどうなのか、聞かせてもらいたい。','interest-design'),
      ('HCIへの関心について、名前とひとことを聞かせて。','interest-hci'),
      ('小規模言語モデルについては、あなたは興味を持っているのかな。','interest-slm'),
      ('人や状況に合わせた情報体験に、関心はあるのかな。','interest-context'),
      ('好きなものは、説明を付けず名前を全部並べてもらいたいな。','favorites'),
      ('関心を持っているものを、興味の一覧として聞かせてもらいたいな。','interests'),
      ('Nothing Headphone1について、使っているかではなく特徴と仕様をまとめて聞かせてほしい。','headphone-spec'),
      ('TOKYO MERの紹介を、主演とテレビ局の放送枠だけに絞ってお願い。','mer'),
      ('VIVANTの紹介を、主演とテレビ局の放送枠だけに絞ってお願い。','vivant'),
      ('kyuが扱うものを、ブランドの紹介として短く聞かせてもらいたいな。','kyu'),
      ('趣味の内容を、余暇の活動として簡潔に聞かせてもらいたいな。','hobbies'),
      ('音楽を聴く機器を、イヤホンとヘッドホンの名前で聞かせてもらいたいな。','audio'),
      ('Headphone1でLDACとノイキャンを併用したら、最大何時間か教えてもらいたいな。','headphones-battery-ldac-on'),
      ('Headphone1でAACを使いノイキャンを切ったら、最大何時間か教えてもらいたいな。','headphones-battery-aac-off'),
      ('Headphone1の本体の重さを、単位付きの数値で聞かせてもらいたいな。','headphones-weight'),
      ('Headphone1が扱える音声コーデックを、種類を省かず聞かせてもらいたいな。','headphones-codecs'),
      ('Tecircで行うことを、活動として一文で聞かせてもらいたいな。','tecirc'),
      ('CMF BudsでANCを切ると、単体とケースで何時間になるのか聞かせてもらいたいな。','earphones-cmf-battery-off'),
      ('Beats Fit Proの耐水性を、イヤホンとケースの違いまで聞かせてもらいたいな。','earphones-beats-resistance'),
    ]
    rows=[]
    def add(q,intent,kind='profile',history=None,answer=None):
        assert normal(q) not in forbidden,q
        target=answers[intent] if answer is None else answer
        prefix=prompt(q,history or [],t)
        assert len(prefix)+len(encode_stream(target,t))+1<c['provenance']['context'],q
        rows.append(dict(id='owner-aligned-audit:'+str(len(rows)),partition='test',group='owner-aligned-fresh:'+str(len(rows)),question=q,answer=target,history=history or [],kind=kind,intent=intent))
    for q,i in profile:add(q,i)
    preceding=[('まずVIVANTを聞きます。','vivant'),('まず音響機器を聞きます。','audio'),('最初にMERを聞きます。','mer'),('先に趣味を聞きます。','hobbies'),('先に関心のあるものを聞きます。','interests'),('最初に名前を聞きます。','name')]
    for index,(q,intent) in enumerate(profile):
        hq,hi=preceding[index%len(preceding)];add(q,intent,'context',[dict(question=hq,answer=answers[hi])])
    for q in [
      '普段使っている携帯電話について、実際の型番を今ここで聞かせてほしい。',
      '通学先の正式な学校名を、あなたの情報として聞かせてほしい。',
      'お気に入りの映画の題名を、好きなものとして聞かせてもらいたい。',
      '現在あなたが使っているパソコンの型番を聞かせてもらいたい。',
      'Nothing Headphone (9)の本体重量を、仕様として聞かせてもらいたい。',
      'CMF Buds Pro 9の最大再生時間を、仕様として聞かせてもらいたい。',
      '今のこの瞬間に札幌で何度あるのか、気温を聞かせてもらいたい。',
      'Nothing Headphone (1)を買うと決めた本当の理由を、あなたの体験として聞かせて。',
    ]:add(q,'unknown','unknown',answer='その情報は分かりません。')
    for q,intent in [
      ('JavaScriptでconstを宣言に使った変数は、後から再代入できるものなの？','mdn-const'),
      ('JavaScriptのMapが保持するデータの形を、短い説明で聞かせてもらいたい。','mdn-map'),
      ('HTMLでtextareaを置くと、どんな入力欄になるのか聞かせてもらいたい。','mdn-textarea'),
      ('CSSでoverflow-wrapを指定する目的を、短い説明で聞かせてもらいたい。','mdn-overflow-wrap'),
      ('JavaScriptのSetに保存される値には、どんな特徴があるか聞かせてほしい。','mdn-set'),
      ('CSSのfont-familyがフォントを選ぶしくみを、短い文章で聞かせてもらいたい。','mdn-font-family'),
      ('HTMLでinputを置くと、どんな部品になるのか短く聞かせてもらいたい。','mdn-input'),
      ('JavaScriptのStringが扱うものを、短い文章で聞かせてもらいたい。','mdn-string'),
    ]:add(q,intent,'web-knowledge')
    for q in [
      'Nothing Headphone1は、見た目と基本仕様だけを一文にまとめて紹介してほしい。',
      'Headphone (1)を、短い紹介文で特徴と仕様を聞かせてもらいたい。',
      '細かな再生時間の一覧は省いて、Headphone1を一文で紹介できる？',
      '主な特徴と基本仕様を、短い一文で説明してもらいたいな。Nothing Headphone1の話です。',
    ]:add(q,'headphone-brief')
    assert len(rows)==68
    audit=dict(schemaVersion=1,rows=rows,provenance=dict(frozenBeforeFitting=True,parentCorpusSha256=c['provenance']['parentCorpusSha256'],corpusSha256=c['sourceSha256'],profileSha256=c['provenance']['currentProfileSha256'],scope='Author-defined68 current-requirement questions,24 paired standalone/gold histories,4 brief-introduction controls,8 unknown and8 source definitions. Whole question strings absent from all training/validation/test and previous audits. Never tokenizer fitting, weight training or checkpoint selection. Not representative or independent human evaluation.'))
    audit_sha=write('owner-aligned-audit.json',audit)
    # Different, also unseen, question strings for live generated-history tests.
    specs=[
      [('ちょっとAppleへの関心を聞かせてほしいんだけど。','interest-apple'),('では、Nothingへの関心を聞かせてほしいんだけど。','interest-nothing'),('次はOpenAIへの関心を聞かせてほしいんだけど。','interest-openai')],
      [('今回は好きなものを名称のみで全部聞かせて。','favorites'),('次は興味を持っているものをまとめて聞かせて。','interests'),('最後にHCIへの興味を短く聞かせて。','interest-hci')],
      [('先にMERの紹介を主演と放送枠でお願い。','mer'),('次にHeadphone1のデザインと主な仕様を詳しく聞かせて。','headphone-spec'),('今度はVIVANTの主演と放送枠を聞かせて。','vivant')],
      [('最初にあなたの趣味を短く聞かせてほしい。','hobbies'),('今度はTecircで行っている活動を短く聞かせてほしい。','tecirc'),('では、あなたの趣味をもう一度まとめてほしい。','hobbies')],
      [('まずHeadphone1を仕様も含めて詳しく紹介してくれるかな。','headphone-spec'),('それではHeadphone1のLDAC接続でANCオンの最大時間を聞かせて。','headphones-battery-ldac-on'),('次はHeadphone1のAAC接続でANCオフの最大時間を聞かせて。','headphones-battery-aac-off')],
      [('最初は普段の音響機器を製品名で全部聞かせて。','audio'),('続いてNothing Headphone (8)の本体重量を聞かせて。','unknown'),('それから普段の音響機器をもう一度製品名で全部聞かせて。','audio')],
      [('先にkyuのブランド紹介を簡潔に聞かせてほしい。','kyu'),('では、小規模言語モデルへの興味を聞かせてほしい。','interest-slm'),('続いて、好きなものを説明なしで全部挙げてほしい。','favorites')],
      [('最初はJavaScriptのArrayが何か教えてもらいたい。','mdn-array'),('次にHTMLのtextareaが何か教えてもらいたい。','mdn-textarea'),('続いて好きなものを名前だけで全部聞かせてほしい。','favorites')],
      [('最初にNothing Headphone1のデザインと複数の仕様を詳しくまとめてほしい。','headphone-spec'),('今度はHeadphone1をデザインと基本仕様だけの短い一文で紹介して。','headphone-brief'),('それではHeadphone1の重さだけをグラムで聞かせて。','headphones-weight')],
    ]
    conversations=[];used={normal(r['question']) for r in rows}
    for index,spec in enumerate(specs):
        turns=[]
        for j,(q,intent) in enumerate(spec):
            assert normal(q) not in forbidden|used,q;used.add(normal(q))
            turns.append(dict(id=f'owner-aligned-rollout:{index}:{j}',question=q,answer=answers[intent] if intent!='unknown' else 'その情報は分かりません。',kind='unknown' if intent=='unknown' else 'web-knowledge' if intent.startswith('mdn-') else 'context',intent=intent))
        conversations.append(dict(id='owner-aligned-rollout:'+str(index),turns=turns))
    rollouts=dict(schemaVersion=1,conversations=conversations,provenance=dict(frozenBeforeFitting=True,corpusSha256=c['sourceSha256'],scope='Nine authored live conversations,27 unseen question strings. Inference appends actual generated valid answers, never gold substitution. A long accumulated answer may genuinely exceed the evaluated model context; count the failure, never silently crop.'))
    rollout_sha=write('owner-aligned-rollouts.json',rollouts)
    # Fresh raw seeds from complete held-out test-page paragraphs. Old raw
    # probes remain known development controls; no known prefix is recycled.
    old_prefixes={r['prefix'] for r in json.loads((HERE/'switch-raw-probes.json').read_text())['rows']}
    candidates=collections.defaultdict(list)
    for r in c['pretrainingTest']:
        if r.get('unit')!='complete-paragraph':continue
        text=bytes.fromhex(''.join(t['bytes'][i] for i in r['tokens'][1:-1])).decode('utf-8')
        if len(text)>=90 and text.count('。')>=1 and text[:28] not in old_prefixes and '。' not in text[:28]:candidates[r['document']].append(text)
    raw_rows=[]
    for document in sorted(candidates):
        text=sorted(candidates[document],key=lambda x:hashlib.sha256(x.encode()).hexdigest())[0]
        raw_rows.append(dict(id='owner-aligned-raw:'+str(len(raw_rows)),document=document,prefix=text[:28],reference=text,sourceUrl=next(d['url'] for d in c['provenance']['documents'] if d['id']==document),textSha256=hashlib.sha256(text.encode()).hexdigest()))
    raw=dict(schemaVersion=1,rows=raw_rows,provenance=dict(frozenBeforeFitting=True,corpusSha256=c['sourceSha256'],scope='First28 Unicode characters of complete paragraphs from held-out TEST pages. Prefix selection is deterministic before new fitting, not based on outputs. Raw BOS+prefix full-vocabulary greedy continuation, no repair/masks/catalogue. Strict fluency requires a complete meaningful sentence with continuity to the prefix.'))
    raw_sha=write('owner-aligned-raw-probes.json',raw)
    print(json.dumps(dict(auditSha256=audit_sha,auditRows=len(rows),auditKinds=dict(collections.Counter(r['kind'] for r in rows)),rolloutsSha256=rollout_sha,conversations=len(conversations),turns=sum(len(c['turns']) for c in conversations),rawSha256=raw_sha,rawRows=len(raw_rows)),ensure_ascii=False),flush=True)
if __name__=='__main__':main()
