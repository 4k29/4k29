"""Full unedited paired output reading, bound to exact observed generation SHAs.
Thresholds/rubric unchanged; legacy Round16 scores preserved, not overwritten.
"""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parents[1];E=R/'execution';B=R.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert sha(E/'new-validation.json')=='d7d48d6c034bb6ba01f86d08a4053d75e7a1bd27e415aef22e65153827d346a5'
assert sha(E/'old-validation.json')=='fe393d193e6569dc12b5c1e30d9b97cdca0618ae7ae35fe6a6a0c1ce6489d7b2'
new=[
(2,2,2,2,2,True,True,'初文の「のぼりはじめました」は自然。後続は呼びかけを長く反復し、おじいちゃんの所有関係が再帰し、意味が進まず未完となる。'),
(0,0,0,0,0,False,True,'寒さを防ぐ行為も述語も現れず、「そのまま」「いつものの」を延々反復する。文法・意味の成立がない。'),
(2,1,1,2,1,True,True,'葦が風のなかにかかっていたことと母の発言の因果が不明瞭。後続に「一度もみがとりがたくさんのごろ」などの崩れがあり、母が母になる節と所有関係を反復する。擬人化そのものを失敗理由とはしない。'),
(0,0,1,0,1,False,True,'立ち上げた対象の説明にならず、eシールのeシールという所有連鎖を十回以上重ねる。後半も同じ仮名・英字列を反復して閉じない。'),
(2,2,2,2,2,True,True,'市場規模の初文は自然。後続では市場規模が基地局として総務省が発表しているという主述が崩れ、同年10月に開催という節を繰り返す。数値や年号の真偽だけの判定ではない。'),
(0,0,1,0,0,False,True,'法律に基づきという節を重ね、法番号と日付列が反復するだけで述語まで到達しない。初文も全文も成立しない。'),
(1,1,1,1,2,True,True,'目標及び第11号という並列と、海洋ごみの海域の水域の水質という重複修飾が不自然。後半は同じ法律に基づくという句を周期的に重ねて未完となる。'),
(0,0,1,2,2,True,True,'「お知らせるおそれがある」の活用と主述関係が不自然。後続も噴火警戒レベルを付して発表するという同一文を何度も繰り返す。'),
(2,1,1,2,2,True,True,'解析雨量という主題と予測処理・速報版の発表状況を把握する行為の関係が曖昧。後続は解説をご覧くださいという文と気象解説情報の列挙を反復し、意味が進まない。'),
(2,1,2,2,2,True,True,'関数が別オブジェクトのメソッドを返すという初文の文法・関係は成立する。実在API仕様は認定しない。後続はSVGオブジェクトのメソッドを返す同じ文を延々反復する。'),
(2,2,2,2,2,True,True,'グローバル属性を指定できるという初文は自然。後続は要素を指定する要素に設定するという修飾の再帰と同一節の反復に崩れる。未知の要素名だけで失敗とはしない。'),
(2,1,2,2,2,True,True,'インターフェイスのメソッドが別オブジェクトのメソッドを返すという初文の関係は成立する。Internationの実在性は認定しない。以降は返却対象が説明なく配列に変わり、配列の配列を返す文を長く反復する。'),
(2,2,2,1,2,True,False,'初文は使用して使用できるという軽い冗長さを含むが、ポリシーオブジェクトを使ってJavaScriptで利用するという関係は成立する。後続はURLのURLのURLや二重の使用節で対象関係が崩れる。短くEOSで閉じ、長い周期ループとは判定しないが全文意味は成立しない。'),
(0,0,1,0,2,True,True,'ウェブサイトのウェブサイトを提供するという修飾と、ユーザーがユーザーがという重複主語が初文から崩れる。後続も同じ送信節と主語を長く反復する。'),
(2,1,1,2,2,True,False,'データなどの客観的な取組という名詞関係が曖昧。後続は管理の短い入れ子反復に加え、取り組む必要な管理を図ることが必要という修飾・述語関係が崩れる。長い周期文ループとはしないが、EOSだけでは全文意味は成立しない。'),
(2,2,2,1,2,True,True,'副大臣が外国大臣の表彰のため施策を進めるという初文は、一般的だが文法・関係が成立する。実際の訪問内容は認定しない。後続は大臣会合を何重にも反復し、首脳会談による首脳会談を発出するという対象関係へ崩れる。'),
(1,0,1,0,1,True,True,'法と同じ法条文に基づく句を初文内で再帰し、施設の促進・地域計画の施設の促進という対象関係が不明瞭。後続は地域計画の整備を十回以上反復して未完となる。')]
g=read(E/'new-validation.json');rows=[]
for x,d in zip(g['rows'],new,strict=True):
 a,b,c,e,f,closed,loop,reason=d;rows.append(dict(id=x['id'],grammar=a,meaning=b,connection=c,repetition=e,breaks=f,sentenceClosed=closed,fullOutputLoop=loop,fullOutputMeaningful=False,reason=reason))
reviewer='Assistant reading of every complete unedited paired prefix+continuation; not independent or blind human scoring'
write(E/'new-manual.json',dict(generationSha256=sha(E/'new-validation.json'),meaningPolicySha256=sha(B/'round10/full-meaning-policy.json'),reviewer=reviewer,rows=rows))
legacy=E/'old-manual-legacy.json'
if not legacy.exists():shutil.copyfile(E/'old-manual.json',legacy)
m=read(legacy);fix={
 'validation-env-05':([2,1,2,2,2],False,'初文は循環分野の法律を踏まえ政策対話を開催したという行為の関係が成立する。会合の名称や年号の真偽は認定しない。後続は同年10月の開催節を反復し、法と会合の対応も崩れるため全文意味は不成立。'),
 'validation-mdn-new-00':([2,1,2,2,2],False,'SVG文字列を受け取る関数がCSSオブジェクトのメソッドを返すという初文の文法・関係は成立する。API仕様の真偽は未認定。後続は同じSVGオブジェクトのプロパティを返す文を長く反復する。'),
 'validation-mdn-new-02':([2,1,2,2,2],True,'メソッドがInternationオブジェクトを返すという一文は文法・主述・接続が成立し、反復せずEOSで閉じる。Internationという未知名の実在/API仕様は認定しない。固定rubricは事実未確認だけの失格を求めていないので、短いこの出力の全文意味を認める。旧Round16記録は保存し、今回の再判定を区別する。'),
 'validation-mdn-new-03':([2,1,2,2,2],False,'ポリシーオブジェクトを用いてSVGリクエスト送信方法を提供するという初文の文法・関係は成立する。APIの正しさは未認定。後続は送信する節を何重にも長く反復するため全文意味は不成立。')}
for x in m['rows']:
 if x['id'] in fix:
  scores,full,reason=fix[x['id']]
  for k,v in zip(['grammar','meaning','connection','repetition','breaks'],scores):x[k]=v
  x['fullOutputMeaningful']=full;x['reason']=reason
m.update(reviewer=reviewer,legacyManualSha256=sha(legacy),note='Round18 same-rubric re-adjudication after complete paired raw reading. Four first-sentence interpretations corrected; unknown facts alone are not language failures under existing frozen rubric. Original Round16 official artifact and its immutable rebound copy retained. Thresholds unchanged.')
write(E/'old-manual.json',m)
