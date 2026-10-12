"""Assistant manual judgments of the selected step9500 after actual10000 updates.
Every full raw output was read; these records are never training targets or selectors.
"""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
judgments=[
('validation-aozora-00',[2,2,2,2,2],True,True,'初文「のぼりはじめました」は自然。以降はおじょうちゃん・おじさんの所有関係を延々と重ね、「おかしなさいんの」などの語形に崩れ、虫の話が続かない。'),
('validation-aozora-01',[0,0,0,0,1],False,True,'寒さを防ぐための述語がなく、そのまま・いつもののを反復し続ける。文が閉じず行動や意味の進展がない。'),
('validation-aozora-02',[1,0,1,2,2],True,True,'「葦が風のなかにかけていた」は語の結び付き・動作が不明。後続は「もう一度もなくなってしまいました」の反復からお父様の所有関係の列に崩れる。'),
('validation-mic-03',[0,0,0,0,0],True,False,'AI EANI EANI EEEEEEEESDEという不明な文字列、括弧・引用の不整合、2020年の対象と2025年の取組の関係の欠落がある。短い一文でEOSになり、局所的文字反復はあるが延々続く同一節の循環とは分類しない。全文意味は不合格。'),
('validation-mic-04',[2,2,2,2,2],True,False,'初文は自然。後続でコンテンツ市場の内訳を携帯基地局と企業向け・米中の6割とし、何の内訳か不明になり、日本のデジタル化投資と米国情報化投資のシェアを混同する。有限の3文でEOS、冗長な節はあるが長い循環ではない。数値や図表の事実性は認定しない。'),
('validation-env-05',[0,0,1,0,0],False,True,'法律番号や年を変えながら「に基づき」を重ねる。最初の句点も「同法第111号」で主文の述語がなく、括弧が不整合。後半は第1条を反復する。'),
('validation-env-06',[2,2,2,2,2],True,True,'初文は海岸法の目標・実施と対策という自然な文。後続は海洋ごみ・海域の生態系を反復し、架空の略語や括弧を混在させ、「海洋環境の変化を推進する」など意味の結び付きが崩れる。'),
('validation-jma-07',[0,0,1,0,2],True,False,'「お知らせるおそれが著しく大きな噴石」は活用・修飾関係が不成立。「避難をとるべき」も不自然。後続の警報が警報を発表するという主述と「とるべきとって」も破綻。短い3文でEOS、冗長・同義的な節はあるが延々続く循環とは分類しない。'),
('validation-jma-08',[1,1,1,2,2],True,False,'予測処理・速報版の並列が未完成のまま「発表状況や解析雨量の基準を満たしたものです」とつながり、解析雨量と発表状況の意味関係が成立しない。2文でEOSになり長い循環はないが、後続の参照指示でも説明は補えない。'),
('validation-mdn-new-00',[0,0,1,0,2],True,True,'CSをCSSに補完できるが、「SVGオブジェクトをSVGオブジェクトを返します」と目的語を重複。後続は同じSVGプロパティを返す命題を繰り返す。EOSでも長い循環なので非ループとは扱わない。'),
('validation-mdn-new-01',[2,2,2,2,2],True,True,'初文はグローバル属性を指定できるという自然な文。全文では属性・プロパティ・要素の関係を混同し、要素を指定する要素という自己参照の節を反復する。'),
('validation-mdn-new-02',[0,0,1,0,0],False,True,'インターフェイをスへ補完するが、Formation/Format/Promissionなどの不明な識別子に入り、JavaScriptらしい句とASCII点列を反復する。日本語の主文も文末もない。'),
('validation-mdn-new-03',[2,1,1,2,2],True,True,'初文は構文上読めるが、信頼型オブジェクト・ポリシーとSVGリクエスト送信との関係が不明。全文でSVGリクエストを送信するという同じ節を重ね、説明が進まない。'),
('validation-stat-new-00',[0,0,1,0,0],False,True,'ウェブサイトがウェブサイトを提供するという循環からワーク/ワットワークの列に移り、企業サイトの説明にも主文の完成にも至らない。'),
('validation-stat-new-01',[1,1,1,2,2],True,True,'「データなどの客観的な取組」は語の関係が不自然。後続は品質管理から販売・資源循環へ飛び、「資源循環の促進を図るため」を反復。EOSでも長い同一節の循環なので非ループとは扱わない。'),
('validation-bunka-new-00',[1,1,1,0,2],True,True,'初文で小林副大臣から文化庁長官へ主語が移り、表彰と国際連携を曖昧に結ぶ。後続では会合が協力覚書を開催したという不整合、文化からパリ協定への話題逸脱、APAPの文字列反復がある。'),
('validation-bunka-new-01',[1,1,1,2,2],True,True,'「施策を講じられています」はこの法条文の説明では助詞・態の関係が不自然。後続は文化観光から化学物質管理へ飛び、法に基づき・地方公共団体・事業者の句を反復する。')]
generation=ROOT/'new-validation.json';g=json.loads(generation.read_text());assert g['training']['completedSteps']==10000 and g['training']['bestStep']==9500
EXPECTED_SHA='74b1bce35bde9d552c4a62e231517cf0d7aac0f512c98ab4c71e0c1b1b89f117'
assert hashlib.sha256(generation.read_bytes()).hexdigest()==EXPECTED_SHA,'Judgments are bound only to this recorded final generation'
assert [r['id'] for r in g['rows']]==[x[0] for x in judgments]
rows=[dict(id=i,**dict(zip(['grammar','meaning','connection','repetition','breaks'],scores)),sentenceClosed=closed,fullOutputLoop=loop,fullOutputMeaningful=False,reason=reason) for i,scores,closed,loop,reason in judgments]
manual=dict(generationSha256=EXPECTED_SHA,meaningPolicySha256=hashlib.sha256((ROOT.parents[1]/'round10/full-meaning-policy.json').read_bytes()).hexdigest(),reviewer='Assistant manual reading of every unedited selected-step9500 continuation after actual10000 updates; not independent or blind human scoring',rows=rows,note='Nonloop does not mean meaningful: four bounded EOS outputs still fail grammar/semantics/context. EOS alone is not a nonloop criterion; the long repeated MDN and stat outputs are loops despite EOS.')
(ROOT/'new-manual.json').write_text(json.dumps(manual,ensure_ascii=False,indent=2)+'\n')
