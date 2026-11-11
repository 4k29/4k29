"""Freeze supplementary assistant-authored grounded queries, never training teachers."""
import json,pathlib,sys,hashlib
P=pathlib.Path(__file__).resolve().parent;ROOT=pathlib.Path('/workspace/4k29');V=ROOT/'training/language/conversation-v2'
sys.path.insert(0,str(V));from new_tokenizer import Encoder
enc=Encoder(json.loads((V/'data/tokenizer.json').read_text()));old=json.loads(pathlib.Path('/dev/shm/response-ce-study/CANDIDATE_SPANS.json').read_text())['parts']['dev'];new=json.loads((P/'ADDITIONAL_DATA.json').read_text())['parts']['dev'];byid={r['id']:r for r in old+new}
spec=[
('realpersona:13656:11','パンを食べなくなった理由は何でしたか？',['B','F'],['オーブンレンジに買い替えた','パンがうまく焼けなくなった'],'食欲不振や健康目的など原文にない原因へ置換しない。'),
('realpersona:06911:11','コーヒーの時はパンと米のどちらですか？',['C','D','F'],['コーヒー時にはパン'],'米が嫌いとは言っていない。選択のみでは比較理由の成功としない。'),
('realpersona:01590:4','財布を替えたい理由を説明してください。',['B','F'],['長く使いボロボロになった'],'五年は補助的な原文事実。金銭事情を捏造しない。'),
('realpersona:12328:5','雨の日は洗濯物をどこに干しますか？',['D','F'],['室内・部屋干し'],'原文の普段から室内干しという条件を参照する。'),
('realpersona:12126:5','何を買ってあり、何を作る予定ですか？',['D','F'],['天ぷらを買ってある','そうめんを作る予定'],'二つの明示情報の結合であり複雑な推論ではない。'),
('realpersona:06914:3','会話に出た二つの運動を挙げてください。',['F'],['サイクリング・自転車','剣道'],'会話内の経験として述べる。AIの経歴と主張しない。'),
('realpersona:09285:6','作るのが好きな料理は何でしたか？',['A','F'],['オムライス'],'問い返しや相槌のみ不可。')]
rows=[];excluded=[]
for id,q,c,required,rule in spec:
 r=byid[id];t=r['tokens'];role=t[r['response_body_start']-1];other=7-role;prefix=t+[other]+enc(q)+[2,role]
 if len(prefix)+32>256:excluded.append(dict(id=id,reason='Complete original history plus authored query and fixed32 continuation exceeds256',length=len(prefix)));continue
 rows.append(dict(id=id+':grounded-followup',source_id=id,family=r['family'],speakers=r['speakers'],source_url=r['source_url'],license=r['license'],attribution=r['attribution'],source_sha256=r['source_sha256'],prefix=prefix,query=q,categories=c,required_facts=required,interpretation=rule,maxNewTokens=32,source_tokens_sha256=hashlib.sha256(json.dumps(t,separators=(',',':')).encode()).hexdigest(),source_full_tokens=t,original_human_reply_in_context=True,query_author='main assistant, not human original',answer_teacher_generated=False,score='semantic fact fulfillment and naturalness independently; no string-exact requirement'))
out=dict(status='FROZEN_BEFORE_READING_MODEL_OUTPUTS',rows=rows,excluded=excluded,source='already exposed original DEV families; no new source/test',independent_human_evaluation=False,training_used=False,semantic_rules='All required facts plus coherent relevant text; unsupported additions fail. Human self-report interpreted as conversation facts, not externally verified autobiographical facts.',optimizer_calls=0)
(P/'GROUNDED_DEV.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(dict(cases=len(rows),excluded=excluded,lengths=[len(r['prefix'])for r in rows],sha256=hashlib.sha256((P/'GROUNDED_DEV.json').read_bytes()).hexdigest()))
