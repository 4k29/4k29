"""Complete raw-output reading; no altered thresholds, no factual API certification."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(E/'new-validation.json')=='707b3e807300e81cb60d2cbed24b580624d37cdf44fa8df4564f838cfd21163c'
data=[
([2,2,2,2,2],True,True,'初文は自然に「のぼりはじめました」で閉じる。その後「あんまりから」の接続が崩れ、おじょうちゃんの所有関係を長く再帰し、意味が進まない。'),
([0,0,0,0,0],False,True,'寒さを防ぐ行為や述語に至らず、そのまま・いつものの・いまを反復し、句読点まで崩れる。'),
([0,0,1,2,1],True,True,'葦が風のなかにかけていたという述語の対象が欠け、顔を見たい主語も曖昧。後続は母の所有と変化の節が破綻し、おおおを反復する。擬人化そのものは失敗理由ではない。'),
([1,0,1,0,1],True,True,'eシールの所有連鎖と、テーマでチップを開催するという対象関係が不自然。後続のシステムのシステムや団体の長い列挙も意味が進まない。未知の英字名だけを失敗理由にしない。'),
([2,2,2,2,2],True,False,'初文は自然。後続の情報端末の主要23億円や、MVNOが1兆円の赤字額がという主述、対応しない括弧で崩れる。内訳・図表の再登場はあるが長い周期ループではなく、EOSで終わる。数値の真偽だけの失格ではない。'),
([2,1,2,2,2],True,True,'初文は法律に基づく取組を進めるという関係が成立し、法律名の真偽は未認定。後続は同じ法条文に基づく句を長く反復し、括弧と文の閉じ方も崩れる。'),
([0,0,1,0,1],True,True,'海洋ごみの海洋ごみという修飾と、目標及び改正という並列が崩れ、同じ法律と所有関係を再帰する。引用内の句点だけでは自然な初文の成立にならない。'),
([0,0,1,2,1],True,False,'噴火速報は発生をお知らせると予想される避難の判断をとることが重要、という主述・修飾が不成立。後続も警報・予報の入れ子が不自然。語句再利用は多いが同一文の長い周期ループとは判定しない。全文意味は不成立。'),
([1,1,1,2,2],True,False,'解析雨量という主題に、速報版の発表状況や解析雨量の基準を満たしたものという述語が自然につながらない。短くEOSで閉じ、後続の案内文もあるが、冒頭の重大な関係の崩れを補えない。'),
([2,1,2,2,2],True,True,'関数がCSSオブジェクトのメソッドを返す初文の文法・関係は成立。API仕様は未認定。後続はSVGプロパティの値が指定された場合という節を何重にも反復する。'),
([2,2,2,2,2],True,True,'初文のグローバル属性を指定する関係は成立。後続は要素が要素にフォーカス可能にするという再帰的修飾に崩れ、フォーカスを指定する際にを長く反復する。'),
([2,1,2,2,2],True,True,'メソッドが別オブジェクトのメソッドを返す初文は成立し、未知名Interrorだけでは失格にしない。後続は返却対象の関係が定まらず、配列の配列を返す節から配列の単語ループへ崩れる。'),
([0,0,1,0,1],True,True,'SVG要素をという目的語を初文から何度も重ね、設定の対象関係が成立しない。後続も同じ設定節を長く繰り返す。'),
([1,0,1,0,2],True,False,'ウェブサイトのウェブサイトを提供する、提供する際に必要なデータを提供する際に、という短い局所再帰で対象が不明。短くEOSで終わるため長い周期ループとはしないが全文意味は不成立。'),
([2,1,1,2,2],True,True,'データなどの客観的な取組という関係が曖昧。後続は製品の管理や管理を再帰し、製造業の製造業の実現に向けた取組という同じ文を反復する。EOSでも全文成立とはしない。'),
([1,0,1,2,1],True,True,'国際協力覚書を開催するという動詞と対象が不適切。後続も共同声明が開催されたと崩れ、国の文字を長く反復する。訪問の事実や年号だけの判定ではない。'),
([2,2,2,2,2],True,True,'初文の法施行後に必要な施策を講じるという関係は成立。後続は法に基づく施設の促進を再帰し、地方公共団体と地域の地域を長く反復する。')]
g=json.loads((E/'new-validation.json').read_text());rows=[]
for x,(scores,closed,loop,reason) in zip(g['rows'],data,strict=True):
 row=dict(zip(['grammar','meaning','connection','repetition','breaks'],scores));row.update(id=x['id'],sentenceClosed=closed,fullOutputLoop=loop,fullOutputMeaningful=False,reason=reason);rows.append(row)
out=dict(generationSha256=sha(E/'new-validation.json'),meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant reading of all 17 complete unedited prefix+continuations; not independent or blind human scoring',rows=rows)
(E/'new-manual.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
