from pathlib import Path
import json,hashlib
B=Path('/workspace/4k29/training/language');E=B/'round17/execution';g=json.loads((E/'new-validation.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(E/'new-validation.json')=='04c28c6524074061971fd9c8c4f18b70cc544f9f30e71cafee12902223b0bffc', 'These judgments apply only to the actually read raw generation'
data=[
(2,2,2,2,2,True,True,'初文は「のぼりはじめました」と自然に接続する。後続は「いましたくさん」の活用・語境界が崩れ、おじいさんの所有関係を五重以上に重ね、呼びかけも長く反復して未完となる。'),
(0,0,0,0,0,False,True,'寒さを防ぐ行為も述語も出ず、「そのまま」「いつものような」「いま」と読点を延々反復する。文が閉じず意味が進まない。'),
(2,2,2,2,2,True,True,'葦が風のなかにかけて来たのが見えたという初文は自然で、会話する葦の擬人化とも整合する。後続の「おりがたいなのだった」「おりまえ」などの語形が崩れ、おかあさんの主述・所有関係を再帰的に反復する。'),
(1,1,1,1,1,True,True,'既に立ち上げた団体を設立するという重複と「AIのAI」、AIの実施・推進・活用の連鎖が不自然。eシールからAI施策へ説明なく移り、推進するという節を重ねる。未知の団体名や日付の事実性だけで不合格とはしていない。'),
(2,2,2,2,2,True,True,'初文は自然。内訳の説明は米国企業のシェアがソフトウェアを占めるという対象関係へ崩れ、日本の情報化投資が自分自身のシェアを占める同じ節を三度反復する。EOSで閉じても全文の意味は成立しない。'),
(2,1,2,1,2,True,False,'初文は文法的に閉じるが、取組を取組を通じて促進するという循環と「産業構造の促進」の対象関係が不明瞭。後続は会合番号と法律の名称、閣議決定時期の修飾が崩れる。末尾に会合の短い入れ子反復はあるが、長い同一節の周期反復とは認定せず非ループ扱い。非ループでも全文意味は不成立。'),
(1,1,1,2,2,True,True,'海岸法の目標及び調査を実施するという並列・述語の対象が不自然。後続は海洋ごみの海洋ごみ、把握・把握、及び及びという局所重複と、排出把握の長い反復を続ける。法令名の真偽だけを評価基準にはしない。'),
(0,0,1,2,2,True,True,'「お知らせるおそれがある」の活用と主述関係が初文から崩れる。後続は噴火警報・予報の列挙と読点を反復し、説明が進まない。'),
(2,0,1,2,2,True,False,'初文は閉じるが、予測処理においてと発表状況・基準を満たす予測値の並列・役割が曖昧。後続の解析雨量の解析雨量の解析という局所的な再帰と、把握する領域で資料をご覧という関係が不明瞭。短くEOSで閉じ、長い周期ループとは認定しないが、全文意味は不成立。予報の事実性だけで不合格にはしていない。'),
(0,0,1,0,2,True,True,'CSS関数がSVGファイルをSVGファイルを使用するという二重目的語が初文から不成立。後続は同じSVGファイルを使用してという節を十回以上反復する。'),
(2,2,2,2,2,True,True,'グローバル属性を定義するという初文は自然に接続する。後続は要素を指定・設定・定義する関係を再帰的に重ね、長い同一節を反復して意味が進まない。未知のHTML要素名だけを失敗の条件にはしていない。'),
(2,1,2,2,2,True,True,'初文のインターフェイスのメソッドが別オブジェクトのメソッドを返すという文法・関係は成立する。Interrorという未知名の実在やAPI仕様の正しさは認定しない。後続は返却対象がInterror、Inter、配列へ説明なく変わり、配列の配列を返す節を延々反復するため全文意味は不成立。初文の解釈には旧モデル判定との感度を別記する。'),
(2,1,1,0,2,True,True,'初文からSVGリクエストを送信する節を三度重ね、信頼型オブジェクト・ポリシーの役割が曖昧。以降も同じ送信節を長く反復する。SVGという話題の事実性だけを不合格理由にしていない。'),
(0,0,1,0,2,True,True,'企業のウェブサイトではウェブサイトのウェブサイトを提供するHTML要素を提供するという主述・修飾が再帰的に崩れる。後続の要素を定義・指定する節も長く反復する。'),
(2,1,1,2,2,True,True,'経験や勘のみに頼らず客観的な取組が必要という接続は文法的に閉じるが、データなどの客観的な取組という名詞関係が曖昧。後続は管理や管理、結果を用いて調査する節、調査票を受け取る節を長く反復し、「取りまとめとめる」の語形も崩れる。'),
(2,1,1,2,2,True,True,'文化大臣の表彰のための施策から国内外の施策へ移る初文は閉じるが、訪問文脈の行為と目的の関係が不明瞭。後続は同じ日ASEANデジタル大臣会合においてという節を三重にし、会合の名前と開催句を反復する。'),
(1,0,1,1,2,True,True,'法附則においては必要な施策を講ずる法律に基づき施行されましたという主語・述語と法の入れ子が不成立。後続は法に基づき、事業者の認定を図るためという節を長く反復する。法令番号や日付の正誤だけを評価していない。')]
assert len(data)==len(g['rows'])==17
rows=[]
for x,d in zip(g['rows'],data,strict=True):
 a,b,c,e,f,closed,loop,reason=d;rows.append(dict(id=x['id'],grammar=a,meaning=b,connection=c,repetition=e,breaks=f,sentenceClosed=closed,fullOutputLoop=loop,fullOutputMeaningful=False,reason=reason))
m=dict(generationSha256=sha(E/'new-validation.json'),meaningPolicySha256=sha(B/'round10/full-meaning-policy.json'),reviewer='Assistant reading of every complete unedited prefix+continuation; not independent or blind human scoring',rows=rows)
(E/'new-manual.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
