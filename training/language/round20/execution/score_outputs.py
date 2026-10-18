"""All 17 complete raw outputs read; fixed rubric, no API truth certification."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(E/'new-validation.json')=='c8200961c08f221a9d0ff9c7759f1a7907ead9267bcf0dd7279f835dd86868ec'
assert sha(E/'old-validation.json')=='534f852dd87a19d2fada44f8e253a68826656bea132504b44f63f433aed10c3e'
data=[
([2,2,2,2,2],True,True,'初文は自然に閉じる。後続は「あんまりから」の接続が崩れ、おじょうちゃんの所有関係を長く再帰する。旧と全文が同じで意味が進まない。'),
([0,0,0,0,0],True,True,'寒さを防ぐ行為や自然な述語に至らず、そのままとおおおを長く反復する。句点後もお母様の所有関係を延々と再帰する。'),
([0,0,1,2,1],True,True,'葦が風のなかにかけていたという述語の対象が欠け、顔を見たい主語も曖昧。後続も母の所有と変化の節が破綻し、同じ母の節を長く反復する。擬人化だけを失敗理由としない。'),
([1,0,1,0,1],True,False,'初文からeシールの所有関係とテーマでチップを開催する対象関係が崩れる。後続も国際協力覚書を開催するという動詞の対象が不適切。語句の局所再帰はあるが、旧の団体列挙のような長い周期ループとはしない。全文意味は不成立。未知英字名だけの判定ではない。'),
([2,2,2,2,2],True,False,'初文は自然。後続の情報端末の主要23億円や、一度産業活動の実現に向けた周波数が大きいという関係が崩れ、市場の修飾も再帰する。長い周期ループとはしないが全文の説明はつながらない。数値の真偽だけの判定ではない。'),
([2,1,2,2,2],True,True,'初文は法律を踏まえた取組を進める関係が成立し、法律の真偽は未認定。後続は同じ締約国会議を長く列挙し、我が国が署で開催されたという主述へ崩れる。'),
([0,0,1,0,1],True,True,'海洋ごみの所有連鎖と目標及び改正という並列が崩れ、後続は海域の海域を十回以上反復する。ごみをごみにする必要という説明も意味が進まない。'),
([0,0,1,2,1],True,False,'初文の噴火速報は発生をお知らせると予想される避難の判断をとることが重要という主述・修飾が成立しない。後続も警報・予報の入れ子と指標を明示的に示す指標という再帰が不自然。多い語句再利用と長い同一文周期ループは区別するが、全文意味は不成立。'),
([1,1,1,2,2],True,False,'解析雨量という主題と、速報版の発表状況や解析雨量の基準を満たしたものという述語が自然につながらない。短いEOS出力だが冒頭の重大な関係の崩れを補えない。旧と全文が同じ。'),
([2,1,2,2,2],True,True,'関数がCSSオブジェクトのメソッドを返す初文の文法・関係は成立し、API仕様は認定しない。後続はSVGプロパティの値が指定された場合を何重にも長く反復する。'),
([2,2,2,2,2],True,True,'初文のグローバル属性を指定する関係は成立する。後続は要素とフォーカスの修飾が再帰し、フォーカスを指定する際にを長く反復する。'),
([2,1,2,2,2],True,True,'メソッドが別オブジェクトのメソッドを返す初文は成立し、未知名Interrorだけを失格理由としない。後続は返却対象が定まらず、配列の配列を返す同じ文から配列の単語ループへ崩れる。'),
([0,0,1,0,1],True,True,'初文からSVG要素をという目的語を重ね、設定の対象関係が不成立。後続も同じ設定節を長く反復する。'),
([1,0,1,0,2],True,False,'ウェブサイトのウェブサイトを提供する、提供する際に必要なデータを提供する際にという局所再帰で対象が不明。短くEOSで閉じるが全文意味は不成立。旧と全文が同じ。'),
([2,1,1,2,2],True,False,'データなどの客観的な取組という関係が曖昧。後続も管理の入れ子と製品・サービスの製造業の実現という修飾が崩れる。旧の同一文の長い反復は消えたが、最後は国際的な取組は国際的な取組を進めるという同語循環で内容が成立しない。EOSや周期ループ減少だけで全文意味を認めない。'),
([1,0,1,2,1],True,True,'初文の国際協力覚書を開催するという動詞と対象が不適切。後続もアジアの修飾を再帰し、APAPAPなどの文字列反復へ崩れる。事実未確認だけの失格ではない。'),
([2,2,2,2,2],True,True,'初文の法施行後に必要な施策を講じる関係は成立。後続は同じ法に基づく句を何重にも反復し、施設の促進を図るための施設の促進という対象関係も再帰する。')]
g=json.loads((E/'new-validation.json').read_text());rows=[]
for x,(scores,closed,loop,reason) in zip(g['rows'],data,strict=True):
 row=dict(zip(['grammar','meaning','connection','repetition','breaks'],scores));row.update(id=x['id'],sentenceClosed=closed,fullOutputLoop=loop,fullOutputMeaningful=False,reason=reason);rows.append(row)
out=dict(generationSha256=sha(E/'new-validation.json'),meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant reading of all 17 full unedited prefix+continuations; not independent or blind human scoring',rows=rows)
(E/'new-manual.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
