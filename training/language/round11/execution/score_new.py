"""Recorded assistant manual judgments of all unedited step1000 outputs.
Scores are evidence records, never training targets or checkpoint selectors.
"""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
# First-sentence grammar/meaning/connection/repetition/breaks; full output loop.
judgments=[
('validation-aozora-00',[2,2,2,2,2],True,True,'初文「のぼりはじめました」は自然になった。しかし以降は全角空白を生成枠の終わりまで反復し、文間の接続や物語の進行がない。'),
('validation-aozora-01',[0,0,0,0,1],False,True,'「ために、そのまま」のまま述語が成立せず、「そのまま」から読点だけの反復へ崩れる。'),
('validation-aozora-02',[1,0,1,2,2],True,True,'「風のようにかんとんぼりと光っている」は語の結び付き・意味が不明。ぼくから私へ突然移り、そのまま・立ちあがりの節を反復する。'),
('validation-mic-03',[2,1,1,1,2],True,True,'初文は文法上読めるが、2020年に立ち上げた対象をeシールそのものとして循環的に説明する。以降は会議から日付の羅列へ崩れ、66日など根拠不明の数値を反復。'),
('validation-mic-04',[2,2,2,2,2],True,True,'初文「なっています」は自然。全文ではコンテンツ市場から情報通信へ飛び、携帯電話・PHAPSの反復と架空の略語・年代・数値列に崩れる。数値の事実性は認定しない。'),
('validation-env-05',[1,0,1,0,0],False,True,'循環分野の経済活動に関する説明を法律・産業省の節に置き換え、引用を閉じず、関係省庁・協力を通じての反復に入り主文が完成しない。'),
('validation-env-06',[1,0,1,0,2],True,True,'海岸法の目標から海洋ごみを除くという不明な述語へつながり、初文から海洋ごみを反復。後続では生態系の入れ子と助詞・語形が崩れる。'),
('validation-jma-07',[0,0,1,2,2],True,True,'「お知らせるおそれのある避難の判断」は活用・修飾関係が成立しない。後続でも警報と火山泥流と警戒レベルの役割を混同し、同じ説明の節を反復する。'),
('validation-jma-08',[0,0,1,2,2],True,True,'「解析雨量は、予測処理において、また、速報版の発表状況や…ご覧ください」は主語と述語が不整合。後続は解析の反復と「行うととともに」に崩れる。'),
('validation-mdn-new-00',[1,0,1,0,2],True,True,'CSをCSSへ補完できたが、初文でCSSのCSSのCSSを反復する。path関数からプロパティへ対象を混同し、値・オブジェクトを返しますを全文で反復。EOSでも意味の成立は認めない。'),
('validation-mdn-new-01',[2,2,2,2,2],True,True,'初文はグローバル属性を定義するという読める文。ただし技術的正確性は認定しない。後続は要素に設定されるの循環から架空textable/tabタグとtableの反復へ崩れる。'),
('validation-mdn-new-02',[2,1,1,2,2],True,True,'「インターフェイスのメソッドで」は自然に補完するが、説明のないIDateオブジェクトとlowerBoundの関係が不明。DOM・メソッドを返す節から配列の配列の反復へ移る。'),
('validation-mdn-new-03',[1,1,1,2,2],True,True,'「信頼型オブジェクトは…参照してください」は対象の説明と読者への命令が混在し主述関係が弱い。以降はDOMオブジェクト/メソッドを返しますの長い循環に入る。'),
('validation-stat-new-00',[0,0,1,0,1],False,True,'企業サイトからCSS ARIAへ話題が飛び、「ユーザーがユーザーが表示されるように」を反復。統計上の説明も述語の完成もない。'),
('validation-stat-new-01',[1,0,1,0,2],True,False,'EOSで一文だけ閉じるため長い循環はない。しかし「客観的な管理や管理のための適切な管理のため」は不自然な修飾と冗長な同語列で、データによる品質管理の意味が成立しない。'),
('validation-bunka-new-00',[1,0,1,0,0],False,True,'表彰を開催したという曖昧な結び付きから架空の会議・条項へ飛び、括弧を閉じず第1条を反復し続ける。'),
('validation-bunka-new-01',[2,1,1,1,2],True,True,'法附則の規定の説明から実施した事業の報告へ移り、初文の対象と述語の関係が弱い。後続は文化庁から化学物質管理法へ唐突に移って条文句を反復する。')]
generation=ROOT/'new-validation.json';assert hashlib.sha256(generation.read_bytes()).hexdigest()=='d3be69466bec3f95d778dbedcaf3cae23a47b62f388a0bb1459df11cf90b6e1e', 'These manual judgments apply only to the recorded step1000 generation';g=json.loads(generation.read_text());assert [r['id'] for r in g['rows']]==[x[0] for x in judgments]
rows=[dict(id=i,**dict(zip(['grammar','meaning','connection','repetition','breaks'],scores)),sentenceClosed=closed,fullOutputLoop=loop,fullOutputMeaningful=False,reason=reason) for i,scores,closed,loop,reason in judgments]
manual=dict(generationSha256=hashlib.sha256(generation.read_bytes()).hexdigest(),meaningPolicySha256=hashlib.sha256((ROOT.parents[1]/'round10/full-meaning-policy.json').read_bytes()).hexdigest(),reviewer='Assistant manual reading of every unedited full step1000 continuation; not independent or blind human scoring',rows=rows)
(ROOT/'new-manual.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2)+'\n')
