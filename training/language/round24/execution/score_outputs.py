"""Bind complete assistant reading to immutable raw generations; no gate relaxation."""
import pathlib,json,hashlib,copy
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=read(E/'old-validation.json');b=read(E/'new-validation.json');m=read(R.parent/'round23/execution/new-manual.json')
assert sha(E/'new-validation.json')=='a1c13ef0f9e422636b8df2947cc6b93a8786db72b31c92714ccb1208fdd43cba'
assert a['maxNewTokens']==b['maxNewTokens']==192 and a['evaluationThreads']==b['evaluationThreads']==1
changes={
 'validation-env-05':dict(fullOutputLoop=False,reason='初文で地方公共団体等と連携しつつを三回重ね、地域の地域も再帰する。後続は脱炭素化促進の法律と施行の関係が重なり、文が途中で切れる。局所三回反復は残るが旧の長い所有再帰から変化し、JMA等と同じ基準で長い同一周期ループとは区別する。全文意味は不成立。'),
 'validation-env-06':dict(reason='海洋ごみの所有を繰り返し、海洋ごみに関する法律に基づく法律という接続を長く再帰する。海岸施設の整備という話題が進まず、初文も閉じない。法の事実未確認だけの判断ではない。'),
 'validation-jma-07':dict(reason='お知らせる、予想される現象ののという初文の活用と修飾の崩れは残る。後続はとるべき防災対応を三回ずつ重ね、警報と警戒レベルの説明が接続しない。局所反復はあるが全文は変化し、旧と同様に長い同一周期ループとは区別。最後も引用途中で切れる。'),
 'validation-jma-08':dict(grammar=1,meaning=1,connection=1,repetition=0,breaks=1,reason='解析雨量というデータの主題から警報等を発表するという述語へ移り、速報版の把握と三時間先までの内容の対象関係が不明。初文内で警報・注意報を三回、気象防災速報を四回重ねる。後続も一般向けの大雨から発表イメージへ崩れる。局所列挙反復と長い周期ループを区別し非長期ループだが、EOSで全文意味は合格にしない。'),
 'validation-mdn-new-02':dict(reason='初文のメソッドがInternationオブジェクトを返す文法・対象は成立し未知名のみで失格にしない。後続は同じメモと返却説明を反復し、最後は配列を長く連ねる。旧から配列の並びの一部は変わるが説明が進まない。'),
 'validation-mdn-new-03':dict(reason='初文でSVGオブジェクトをという目的語を二重に置き関係が不成立。後続もSVG要素の目的語を三重に重ね、同じ指定節を長く再帰する。改行の追加は説明の進行を回復せず、最後もSVで切れる。'),
 'validation-bunka-new-01':dict(grammar=2,meaning=2,connection=2,repetition=2,breaks=2,fullOutputLoop=True,reason='法施行後三年以内に必要な施策を講じますという初文は主述・接続が自然になった。後続は文化観光拠点施設から対象物質の有効利用へ対象が崩れ、地域計画の整備と地方公共団体等の句を長く反復する。初文改善と全文意味の不成立を分け、旧の局所再帰から今回は長い反復へ悪化したと記録する。')
}
for x,y,row in zip(a['rows'],b['rows'],m['rows'],strict=True):
 assert x['id']==y['id']==row['id'] and x['prefix']==y['prefix']
 equal=all(x[k]==y[k] for k in ['text','tokens','eos','validTokens','validUtf8','inputTokens'])
 assert equal==(row['id'] not in changes)
 if not equal:row.update(changes[row['id']])
m.update(generationSha256=sha(E/'new-validation.json'),controlGenerationSha256=sha(E/'old-validation.json'),reviewer='Assistant complete reading of all17 prefix+unedited continuations; fixed prior rubric. Not independent blind human scoring.',note='Ten complete outputs identical retain exact prior judgments. Seven changed outputs read completely and scored explicitly. First-sentence improvement does not imply whole-output success; one long-loop recovery and one long-loop regression offset.')
(E/'new-manual.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
