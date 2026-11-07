"""Full reading of all17 unedited prefix+continuations under the unchanged rubric."""
import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(E/'new-validation.json')=='8fc95c6dfd40ef190b9923db669e3ada184a2d7ddbec7ac0df4fa1e9ce7d9110'
data=[
([2,2,2,2,2],True,True,'初文ののぼりはじめましたは自然。後続はおじさんを数十回呼び続けて意味が進まず、文が閉じない。'),
([2,1,2,2,2],True,True,'寒さを防ぐために出て来たという初文は文法的には成立する。出る先が不明で目的との関係は弱いが、文脈にない外気へ出たと決めつけて失格にしない。後続はその夜の夜の夜を長く反復する。初文の接続には解釈差を別記する。'),
([0,0,1,0,1],True,True,'葦が風のなかにかけていたという対象不足に加え、母が母にかかっていたという関係が初文から崩れる。後続も母の主語・対象が入れ替わり、最後は母の所有を長く再帰する。擬人化だけの失格ではない。'),
([0,0,1,0,0],False,True,'立ち上げた名称の引用が閉じず、Internationを長く反復する。未知英字名の存在ではなく文の未成立と反復を失敗理由にする。'),
([2,2,2,2,2],True,False,'初文は自然。後続はコンテンツ市場の内訳から電話契約へ移り、契約数を億円や百分率で表す対象・単位関係が崩れる。局所的な内訳・電話句の再利用はあるが長い周期ループとはしない。EOSだけでは全文合格にしない。'),
([2,1,2,0,1],True,True,'初文内で地方公共団体等と連携しつつを五回反復するため初文も不合格。後続は脱炭素化促進の法律と地域の所有を再帰して閉じない。法の実在性だけの判断ではない。'),
([0,0,1,0,1],False,True,'海洋ごみの海洋ごみという所有を重ね、海洋ごみの維持・再生可能エネルギー等の対象が崩れる。海域の利用と促進を長く再帰し、自然な文として閉じない。'),
([0,0,1,1,1],True,False,'お知らせると予想される現象ののと初文から活用・修飾が崩れる。とるべき防災対応を三回ずつ列挙して意味が進まないが、文全体は変化し、長い同一周期ループとは区別する。噴火速報・警報・レベルの説明の関係もつながらない。'),
([1,1,1,2,2],True,False,'解析雨量という主題と速報版の発表状況や解析雨量の基準を満たしたものという述語がつながらない。後続の解析の解析や解説情報の解説への案内も局所再帰。短いEOS出力だが全文意味は不成立。'),
([2,1,2,2,2],True,True,'関数がCSSパスをfalseに設定する初文は文法上成立し、API仕様の真偽は認定しない。後続はfont-fillプロパティの値が指定された場合を長く反復して閉じない。'),
([2,2,2,2,2],True,True,'初文はグローバル属性を指定する自然な文。後続は要素が指定された要素に設定されている要素という修飾を何度も再帰する。EOSで止まっても対象関係と説明の進行が成立しない。未知要素名だけの失格ではない。'),
([2,1,2,2,2],True,True,'メソッドがInternationオブジェクトを返す初文の文法・対象は成立し、未知名だけを失格にしない。後続は同じメモと返却説明を繰り返し、最後は配列の単語列へ崩れる。'),
([0,0,1,0,1],True,True,'SVGオブジェクトをという目的語を二重に置くため初文の関係が不成立。後続もSVG要素の目的語と指定節を長く再帰する。'),
([0,0,1,0,1],True,True,'ウェブサイトの所有を重ねたうえでHTML要素を提供・指定する句を多重に再帰する。後続も同じこの例ではから始まる文を長く反復し、統計の文脈からHTMLへ崩れる。EOSでも全文不合格。'),
([2,1,1,2,2],True,True,'データなどの客観的な取組という修飾関係は旧と同様に不自然。後続は具体的な取組の自己説明から製造業の創出・所有の長い反復へ崩れる。'),
([2,1,2,1,2],True,True,'表彰のための国際連携の下から再び協力強化のための国際連携の下へ重ね、初文は文法的だが冗長で対象・目的が弱い。後続は日中韓・日米国の関係が崩れて韓国を長く反復する。歴史的事実の未確認だけの判定ではない。'),
([1,1,2,2,1],True,False,'施策を講じられていますという受身と目的語の関係が不自然で、前の法附則の話題だけでは敬語の主体も明確でない。後続は施設の推進の法律、認定及び認定を局所再帰し、地方公共団体が認定された地域の認定者へ対象が崩れる。長い同一周期ループとは区別するが全文意味は不成立。敬語解釈の不確実性を別記する。')]
g=json.loads((E/'new-validation.json').read_text());rows=[]
for x,(scores,closed,loop,reason) in zip(g['rows'],data,strict=True):
 row=dict(zip(['grammar','meaning','connection','repetition','breaks'],scores));row.update(id=x['id'],sentenceClosed=closed,fullOutputLoop=loop,fullOutputMeaningful=False,reason=reason);rows.append(row)
out=dict(generationSha256=sha(E/'new-validation.json'),meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant reading of all17 complete unedited prefix+continuations; not independent or blind human scoring',rows=rows)
(E/'new-manual.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
