"""Complete reading of all17 unedited paired continuations, fixed rubric."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(E/'new-validation.json')=='09a69b9fba323f3d6dcae9afec1232ba673f43f54f0af292251f3707fac19903'
assert sha(E/'old-validation.json')=='c991362fcf05e1bf3676a82f0f1b00d8a4fab3c5d7b4190706265b825de8fa5b'
data=[
([2,2,2,2,2],True,True,'初文は自然に閉じる。後続はあんまりからという接続が崩れ、おじょうちゃんの所有関係を長く再帰する。旧と全文が同じ。'),
([0,0,0,0,0],False,True,'寒さを防ぐ行為や述語に至らず、そのまま、いつものの、いっぱいののを長く反復し、文が閉じない。'),
([0,0,1,0,1],True,True,'葦が風のなかにかけていたという述語の対象が欠け、おかみの関係も不明。おぼえになる語内からおおおを長く反復し、後続は同じ文字に占められる。擬人化だけを失敗理由としない。'),
([1,0,1,0,1],True,False,'eシールの所有連鎖とチップを開催する対象関係が初文から崩れる。後続もタブやタスクの関係がつながらない。語句の局所再帰は多いが長い同一文周期ループとは区別する。未知名だけの失格ではない。'),
([2,2,2,2,2],True,False,'初文は自然。後続はコンテンツ市場の内訳から投資・輸入額へ説明なく移り、2024年には2023年にはという時点関係も崩れる。短いEOS出力でも全文の接続は成立しない。未知の通貨名や数値の真偽だけの判定ではない。'),
([2,1,2,2,2],True,True,'初文は法律を踏まえて取組を進める関係が成立する。後続は同じ締約国会議を何度も列挙し、同法と会合の関係が崩れ、閉じない。法律名の真偽だけの判定ではない。'),
([2,2,2,1,2],True,True,'初文は重複した海洋環境保全の並列で冗長だが、法の目標や改正法に基づく取組を推進するという文法・主述の関係は成立する。法の実在性は認定しない。後続は再生及び再生と再生可能エネルギーの促進を何度も反復し、全文意味は不成立。'),
([0,0,1,2,1],True,False,'初文は発生をお知らせると予想される避難の判断をとることが重要という主述・活用が不成立。後続も警報が火山を中心に活動するという主述、警報に伴って警報を発表という循環が不自然。EOSで終わり長い周期ループとはしないが、全文意味は不成立。'),
([1,1,1,2,2],True,False,'解析雨量という主題と速報版の発表状況や解析雨量の基準を満たしたものという述語が自然につながらない。短いEOS出力でも冒頭の重大な関係の崩れを補えない。旧と全文が同じ。'),
([2,1,2,2,2],True,True,'関数がCSSオブジェクトのメソッドを返す初文の関係は成立し、API仕様は認定しない。後続はSVGプロパティの値が指定された場合を何重にも反復する。'),
([2,2,2,2,2],True,True,'初文のグローバル属性を指定する関係は成立する。後続は要素とフォーカスの修飾が再帰し、フォーカスをフォーカスを移動する節を長く反復する。'),
([2,1,2,2,2],True,True,'メソッドが別オブジェクトのメソッドを返す初文は成立し、未知名だけを失格にしない。後続は返却対象の説明がつながらず、配列の配列を返す同じ文から配列の文字列ループへ崩れる。'),
([0,0,1,0,1],True,True,'SVG要素をという目的語を初文から何度も重ね、設定の対象関係が不成立。後続も同じ設定節を長く反復する。'),
([1,0,1,0,2],True,False,'ウェブサイトのウェブサイトを提供する、データを提供する際に提供するという短い局所再帰で、提供対象が不明瞭。EOSで終わるが全文の自然さ・意味は成立しない。'),
([2,1,1,2,2],True,False,'データなどの客観的な取組という修飾関係が不自然。旧と同じこの問題を、短いEOS出力になったという理由で合格へ変えない。反復はないが、データ自体を取組と並列化する冒頭の関係は自然な続きとして成立しない。'),
([1,0,1,2,1],True,True,'初文は国際協力覚書を開催するという動詞の対象が不適切。後続も会合と首脳会談の修飾が再帰し、共同声明が公表される文を何度も反復する。事実未確認だけの判定ではない。'),
([2,2,2,2,2],True,True,'初文の法施行後に必要な施策を講じる関係は成立する。後続は施設と事業者の整備の対象が曖昧になり、文化観光推進事業者の整備を十回以上反復して閉じない。')]
g=json.loads((E/'new-validation.json').read_text());rows=[]
for x,(scores,closed,loop,reason) in zip(g['rows'],data,strict=True):
 row=dict(zip(['grammar','meaning','connection','repetition','breaks'],scores));row.update(id=x['id'],sentenceClosed=closed,fullOutputLoop=loop,fullOutputMeaningful=False,reason=reason);rows.append(row)
out=dict(generationSha256=sha(E/'new-validation.json'),meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant reading of all17 complete unedited prefix+continuations; not independent or blind human scoring',rows=rows)
(E/'new-manual.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
