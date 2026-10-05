"""Direct questions after unrelated histories and varied complete Japanese.

Targets are approved authored facts/source summaries, never model output. All
earlier audits are development diagnostics; new controls freeze before fitting.
"""
import collections
import copy
import functools
import hashlib
import json
import pathlib
import re
import unicodedata
from tokenizer import SPECIALS,fit_fast,encode_stream
from stream_windows import windows
HERE=pathlib.Path(__file__).resolve().parent
base=json.loads((HERE/'prefix-corrected-corpus.json').read_text())
rows=copy.deepcopy(base['rows'])
normal=lambda q:unicodedata.normalize('NFKC',q).lower()
key=lambda q,h:json.dumps([normal(q),[(normal(t['question']),t['answer']) for t in h]],ensure_ascii=False)
seen={key(r['question'],r['history']) for r in rows}
old_questions=set()
for name in ['fresh-probe.json','fresh-audit.json','binding-audit.json','continuous-audit.json','prefix-audit.json','prefix-rollouts.json']:
    path=HERE/name
    if not path.exists():continue
    d=json.loads(path.read_text());probes=d.get('rows',[])+[t for c in d.get('conversations',[]) for t in c['turns']]
    old_questions.update(normal(r['question']) for r in probes)
representatives={}
for r in rows:
    if r['partition']=='train' and not r['history'] and not r['intent'].startswith(('context-','reference-')):representatives.setdefault(r['intent'],r)
answers={i:r['answer'] for i,r in representatives.items()}
added=collections.Counter()
def add(intent,question,family,partition,history=None):
    history=history or [];question=normal(question);identity=key(question,history)
    if identity in seen or question in old_questions:return
    seen.add(identity);r=copy.deepcopy(representatives[intent]);r.update(id='switch:'+str(len(rows)),intent=intent,question=question,history=history,group='switch:'+family,partition=partition)
    rows.append(r);added[r['kind']]+=1

focuses={
 'name':['あなたの名前と読み方','自己紹介するときの名前','名前の表記と読み仮名'],
 'role':['いまの身分','現在の立場','学生か社会人かということ'],
 'hobbies':['趣味','余暇に取り組む趣味の活動','休日に楽しむ趣味'],
 'favorites':['好きなものの名前だけ','お気に入りのものの名称だけ','好きなものを名前で並べた一覧'],
 'audio':['普段使っているイヤホンとヘッドホン','音楽を聴くときの愛用機器','使っている音響機器の製品名'],
 'tecirc':['Tecircで行っている活動','Tecircでの執筆活動','Tecircで何をしているか'],
 'topics':['記事にするテーマ','Tecircの記事で取り上げる内容','書いている記事の題材'],
 'running-app':['ランニングの記録に使うアプリ','走った記録を付けるアプリの名前','ランニング用のアプリ'],
 'running-shoes':['ランニングで履くシューズ','走るときの靴の製品名','愛用するランニングシューズ'],
 'mer':['MERの主演とテレビ局の放送枠','TOKYO MERの基本情報','MERというドラマの簡単な紹介'],
 'vivant':['VIVANTの主演とテレビ局の放送枠','VIVANTの基本情報','VIVANTというドラマの簡単な紹介'],
 'kyu':['kyuというブランドの事業','kyuが展開している製品','kyuというブランドの紹介'],
 'headphone-spec':['Headphone1の主な特徴と複数の仕様','Nothing Headphone (1)の仕様をまとめた説明','Headphone (1)という製品の概要とスペック'],
 'favorite-dramas':['好きなドラマの作品名だけ','お気に入りのドラマの名称','好きなドラマを並べた一覧'],
 'count-audio':['使っている音響機器の合計機種数','イヤホンとヘッドホンを合わせた種類の数'],
 'count-earphones':['使っているイヤホンの機種数','愛用するイヤホンの種類の数'],
 'count-headphones':['使っているヘッドホンの機種数','愛用するヘッドホンの種類の数'],
 'mer-actor':['MERの主演俳優の名前','TOKYO MERで主演する人'],
 'vivant-actor':['VIVANTの主演俳優の名前','VIVANTで主演する人'],
 'mer-station':['MERのテレビ局と放送枠','TOKYO MERを放送した局と枠'],
 'vivant-station':['VIVANTのテレビ局と放送枠','VIVANTを放送した局と枠'],
}
fields={
 'driver':['ドライバーの方式と口径','音を鳴らすドライバーの仕様'],
 'bluetooth':['Bluetoothのバージョン','Bluetoothの版'],
 'codecs':['対応している音声コーデック','使えるコーデックの種類'],
 'anc':['ノイズキャンセリングの方式と性能','ANCの仕様'],
 'resistance':['防塵・防水の等級','水や汗への対応'],
 'weight':['本体の重さ','重量をグラムで示した値'],
 'impedance':['インピーダンスの値'],
 'battery-capacity':['バッテリー容量','電池の容量'],
 'connection':['接続に使える端子や方式'],
 'multipoint':['複数機器へ同時接続する機能'],
 'wireless-charging':['ワイヤレス充電への対応'],
 'charging':['充電に使う端子'],
 'fast-charging':['短時間の充電で再生できる時間','急速充電の性能'],
 'storage':['内蔵ストレージの容量'],
 'video-front':['前面カメラで撮れる動画の仕様'],
 'video-back':['背面カメラで撮れる動画の仕様'],
 'dimensions':['本体の寸法'],
 'battery-off':['ANCを無効にした場合の再生時間','ANCを使わずに聴ける時間'],
 'battery-on':['ANCを有効にした場合の再生時間','ANCを使って聴ける時間'],
}
for codec in ['aac','ldac']:
    for state in ['on','off']:
        fields['battery-'+codec+'-'+state]=[codec.upper()+'接続でANCを'+('使う' if state=='on' else '使わない')+'場合の再生時間',codec.upper()+'でANCを'+('有効' if state=='on' else '無効')+'にしたときの電池持ち']
products=json.loads((HERE.parent/'product-specifications.json').read_text())['products']
for product in products:
    for field in product['fields']:
        intent=product['id']+'-'+field['key']
        if intent not in representatives:continue
        focuses[intent]=[product['name']+'の'+phrase for phrase in fields[field['key']]]
for intent in representatives:
    if intent.startswith('mdn-'):
        name=intent[4:];language='JavaScript' if name not in ['input','textarea','color','font-family','overflow-wrap'] else 'HTML' if name in ['input','textarea'] else 'CSS'
        focuses[intent]=[language+'の'+name+'の役割',name+'が何を表すかということ',language+'で'+name+'を使う目的']

# Whole question families, not random duplicated rows, determine partitions.
forms=[
 '{f}を説明してもらえますか。','教えてほしいのは{f}です。','{f}が知りたいので、短く答えて。',
 '質問があります。{f}を聞かせてください。','{f}について、要点を教えてくれる？',
 '気になっているのは{f}です。どのようなものか教えて。','{f}を簡単な文章で紹介してほしい。',
 '確認したいことがあります。{f}はどうなっていますか。','{f}を分かりやすく教えてもらえる？',
 '{f}を一度教えてください。','{f}を聞いてもいいですか。','{f}を教えてほしいんだけど。',
 '詳しく聞く前に、{f}の要点を説明してください。','{f}がどんなものか、教えていただけますか。',
 '今聞きたいのは{f}です。答えてもらえますか。','{f}がどうなっているのか聞かせてもらいたい。']
histories=[]
for intent in ['mer','vivant','audio','hobbies','name','role','headphone-spec','kyu','greeting-evening','greeting-morning','unknown-category']:
    if intent not in representatives:continue
    q={'mer':'MERについて教えて。','vivant':'VIVANTについて教えて。','audio':'何で音楽を聴く？','hobbies':'趣味は？','name':'名前は？','role':'どんな立場？','headphone-spec':'Headphone1の仕様は？','kyu':'kyuとは？','greeting-evening':'こんばんは。','greeting-morning':'おはよう。','unknown-category':'好きな映画は？'}[intent]
    histories.append((intent,[dict(question=q,answer=answers[intent])]))
histories += [('two-dramas',[dict(question='MERは？',answer=answers['mer']),dict(question='VIVANTは？',answer=answers['vivant'])]),('thanks',[dict(question='趣味を教えて。',answer=answers['hobbies']),dict(question='ありがとう。',answer=answers['thanks'])])]
for index,(intent,phrases) in enumerate(focuses.items()):
    for form_index,form in enumerate(forms):
        partition='train' if form_index<12 else 'validation' if form_index<14 else 'test'
        for phrase in phrases:
            q=form.format(f=phrase);family='form:'+str(form_index)
            add(intent,q,family,partition)
            # Every explicit question also appears after varied unrelated
            # history; new topic recognition must not mean copying old answers.
            for offset in [0,4,8]:
                old_intent,h=histories[(index+form_index+offset)%len(histories)]
                if old_intent==intent:continue
                add(intent,q,family,partition,copy.deepcopy(h))
            if form_index<4:add(intent,'ところで、'+q,family,partition,copy.deepcopy(histories[(index+form_index+2)%len(histories)][1]))

# The same short question is grounded in different unrelated preceding topics.
# Input question families keep the partition they already held in the base.
for index,r in enumerate(list(rows[:len(base['rows'])])):
    if r['history'] or r['intent'] not in representatives or r['kind'] not in ['profile','dialogue','web-knowledge','unknown']:continue
    old_intent,h=histories[index%len(histories)]
    if old_intent!=r['intent']:add(r['intent'],r['question'],'base:'+r['group'],r['partition'],copy.deepcopy(h))

# New own vocabulary sees only training texts and keeps ordinary numeric BPE.
texts={};old_meta={d['id']:d for d in base['provenance']['documents']}
for name in ['pretraining','pretrainingValidation','pretrainingTest']:
    by_doc=collections.defaultdict(list)
    for r in base[name]:by_doc[r['document']].extend(r['tokens'][r['prefixLength']:])
    for identity,tokens in by_doc.items():texts[identity]=bytes.fromhex(''.join(base['tokenizer']['bytes'][t] for t in tokens[:-1])).decode('utf-8')
fit_texts=[texts[d['id']] for d in old_meta.values() if d['partition']=='train']
for r in rows:
    if r['partition']!='train':continue
    fit_texts.extend([normal(r['question']),r['answer']])
    for h in r['history']:fit_texts.extend([normal(h['question']),h['answer']])
fragments=collections.Counter(fragment for r in rows if r['partition']=='train' for text in [normal(r['question']),r['answer']] for fragment in re.findall(r'[A-Za-z][A-Za-z_-]*',text) if len(fragment)>1)
for fragment,count in fragments.items():fit_texts.extend([fragment]*(4*count))
tokenizer=fit_fast(fit_texts,merges=1024)
@functools.lru_cache(maxsize=60000)
def enc(text):return encode_stream(text,tokenizer)
def prefix(q,history):
    result=[SPECIALS['bos']]
    for h in history:result += [SPECIALS['user']]+enc(normal(h['question']))+[SPECIALS['assistant']]+enc(h['answer'])+[SPECIALS['turn']]
    return result+[SPECIALS['user']]+enc(normal(q))+[SPECIALS['assistant']]
kept=[];skipped=[]
for r in rows:
    tokens=prefix(r['question'],r['history']);full=tokens+enc(r['answer'])+[SPECIALS['eos']]
    if len(full)>=256:skipped.append(dict(id=r['id'],length=len(full)));continue
    r.update(tokens=full,prefixLength=len(tokens));kept.append(r)
counts=collections.Counter(tuple(r['semantic'].values()) for r in kept if r['partition']=='train');unknown_count=sum(r['partition']=='train' and r['kind']=='unknown' for r in kept)
for r in kept:
    scale=0.25 if r['intent']=='addition' else 1.5 if r['kind']=='context' else 0.5 if r['kind']=='web-qa' else 1
    r['weight']=8/unknown_count if r['kind']=='unknown' else scale/counts.get(tuple(r['semantic'].values()),1)
language={p:[] for p in ['train','validation','test']};metadata=[]
for d in old_meta.values():
    text=texts[d['id']];assert hashlib.sha256(text.encode()).hexdigest()==d['textSha256']
    frames=windows(text,tokenizer,d['id'],maximum_input=128,lookback=16)
    for f in frames:
        f['weight']=1/len(frames)
        if d['id'].startswith('mdn:'):f.update(license='CC BY-SA 4.0',sourceUrl=d['url'])
    language[d['partition']].extend(frames);metadata.append(dict(d,frames=len(frames),tokens=sum(len(f['tokens'])-f['prefixLength'] for f in frames)))
provenance=copy.deepcopy(base['provenance']);provenance.update(baseCorpusSha256=base['sourceSha256'],documents=metadata,augmentation='Complete Japanese direct questions after varied unrelated histories. Question-form families split before fitting; previous audits excluded as added question strings and retained as development controls.',tokenizer='Own fresh training-only byte BPE,1024 merges,max12 bytes,no numeric boundary; observed training identifiers add4x counts,no outside vocabulary.',curriculum='Stage1-3 emphasis: addition sample mass0.25 instead of8; retained bounded arithmetic diagnostic is not general reasoning.')
provenance.pop('referenceClarification',None)
result=dict(schemaVersion=6,tokenizer=tokenizer,rows=kept,pretraining=language['train'],pretrainingValidation=language['validation'],pretrainingTest=language['test'],provenance=provenance)
result['sourceSha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
(HERE/'switch-corpus.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
manifest=dict(sourceSha256=result['sourceSha256'],partitions=dict(collections.Counter(r['partition'] for r in kept)),vocabulary=len(tokenizer['bytes']),maxSequence=max(len(r['tokens']) for r in kept),rawFrames={p:len(language[p]) for p in language},added=dict(added),skipped=skipped,historyRows={p:sum(r['partition']==p and bool(r['history']) for r in kept) for p in language})
(HERE/'switch-data.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n');print(json.dumps(manifest,ensure_ascii=False))
