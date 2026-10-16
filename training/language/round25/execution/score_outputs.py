"""All17 prefix+full raw continuations read; fixed rubric and exact-output guards."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=read(E/'old-validation.json');b=read(E/'new-validation.json');m=read(R.parent/'round24/execution/new-manual.json')
assert sha(E/'new-validation.json')=='746e24f66472495f3fdd791331c16aafc8678650ada5f07064ac77410ed790fe'
assert a['maxNewTokens']==b['maxNewTokens']==192 and a['evaluationThreads']==b['evaluationThreads']==1
changes={
 'validation-aozora-00':dict(reason='初文ののぼりはじめましたは自然。後続はおい・おじさんからおじいちゃんへ呼び名が変わるが、長い同じ呼びかけの反復が再開する。おじいちゃんのかいという不自然な接続と、最後の所有句の未完もあり、会話の意味は進まない。創作の人物が出ること自体を失敗理由にしない。'),
 'validation-aozora-02':dict(reason='初文の葦が風のなかにかけていたという対象不足と、おかあさんの主語・対象の重複は旧と同じ。後半の一部においでになったが入るが、母の所有・対象を長く再帰し関係が成立しない。擬人化のみの失格ではない。'),
 'validation-env-05':dict(reason='初文の地方公共団体等と連携しつつ三回反復と地域の地域は旧と同じ。後続も法律・促進・地域の関係を重ね、最後は地域の所有を四回重ねた途中で切れる。局所再帰は残るが、旧と同じく長い周期ループとは区別する。説明の対象と接続は成立しない。'),
 'validation-env-06':dict(reason='海洋ごみの所有を重ね、海洋ごみの維持と再生可能エネルギーを不自然に接続する。利用の促進からエネルギーの導入を六回長く重ね、海岸保全施設の説明が進まない。初文も閉じず、全文意味は不成立。'),
 'validation-jma-08':dict(grammar=1,meaning=0,connection=1,repetition=2,breaks=1,reason='解析雨量はという主題から発表状況や少雨が地上の大雨を把握できるという述語へ移り、主語と把握する主体が成立しない。後続も発表状降水帯、災害の危険度の高まりをご覧くださいという対象不足、雨域を予測した表面などで関係が崩れる。各文は変化し長い同一周期ループではないが、文間の説明は一貫しない。引用も最後まで閉じない。'),
 'validation-mdn-new-01':dict(reason='初文のグローバル属性を指定しますは自然。後続は要素に設定されている要素という修飾を長く再帰して対象を失う。旧のEOSが今回はなくなるが、EOSの有無とは独立に長い再帰と意味の進行不足を失敗とする。未知の要素名だけを失敗理由にしない。'),
 'validation-mdn-new-02':dict(reason='メソッドがInternationオブジェクトを返す初文の文法・接続は成立し、未知名の真偽は認定しない。後続からメモの重複は減るが、同じ配列の返却文を四回重ね、最後は配列の単語列へ長く崩れる。局所的な重複除去は全文意味の改善を示さない。'),
 'validation-mdn-new-03':dict(grammar=2,meaning=1,connection=2,repetition=2,breaks=2,reason='ユーザー定義のポリシーオブジェクトを使用してJavaScriptでSVGリクエストを送信する初文は、旧の目的語二重置きが解消し文法・対象関係が成立する。SVGリクエストや実際のAPI挙動の真偽は認定せず、未知用語のみでは失格にしない。後続はSVGリクエストを送信するを長く入れ子に反復して説明が進まず、最後もSVG SVGで切れ、全文意味は不成立。'),
 'validation-bunka-new-01':dict(reason='必要な施策を講じますという初文は旧と同じく自然。後続は文化観光から対象物質の整備、事業者の整備、地方公共団体の整備へ対象が崩れ、地域計画の整備を十数回長く繰り返す。法の事実未確認とは別に、対象関係と説明の進行が成立しない。')
}
identical=[]
for x,y,row in zip(a['rows'],b['rows'],m['rows'],strict=True):
 assert x['id']==y['id']==row['id'] and x['prefix']==y['prefix']
 same=all(x[k]==y[k] for k in ['text','tokens','eos','validTokens','validUtf8','inputTokens'])
 assert same==(row['id'] not in changes),row['id']
 if same:identical.append(row['id'])
 else:row.update(changes[row['id']])
assert len(identical)==8
m.update(generationSha256=sha(E/'new-validation.json'),controlGenerationSha256=sha(E/'old-validation.json'),reviewer='Assistant full reading of all17 prefix+unedited continuations; same fixed prior rubric. Not independent blind human scoring.',note='Eight complete outputs identical retain exact previous judgments; nine changed outputs fully read and explicitly assessed. New mdn03 first sentence removes duplicate object, but whole output loops. No changed grade based on NLL alone.',identicalCompleteOutputs=identical)
(E/'new-manual.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
