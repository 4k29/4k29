"""Manual judgments bound to this exact full unedited completed Round13 generation."""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
judgments=[
('validation-aozora-00',[2,2,2,2,2],True,True,'初文「のぼりはじめました」は自然。以降は虫からおい・おじさん・おじいさん・おかあさんへ飛び、所有関係と呼びかけを延々重ね、動作語形も崩れる。'),
('validation-aozora-01',[0,0,0,0,0],False,True,'寒さを防ぐ動作・述語がなく、そのままを反復し、おおおという文字列とおかあさんの所有関係へ崩れる。閉じた初文も意味の進展もない。'),
('validation-aozora-02',[0,0,1,2,2],True,True,'冒頭の隠れるという句の後、さっきのなかにかわらい・おまえてはいってという語形と修飾が不成立。後半はおかあさんの所有関係を延々反復する。'),
('validation-mic-03',[1,0,1,1,2],True,True,'eシールシンガポール計画・開催したeシールを策定・eシールシールを実施という対象と行為が不明。以後は日付と第1回会合を開催する句を繰り返し、会合と国会を混同する。'),
('validation-mic-04',[2,2,2,2,2],True,False,'初文は自然。後続はコンテンツ市場の内訳を電話契約数とドルの差に結び、何の差か不明で単位が混同する。4文でEOS、同じ2024年の節を局所的に重ねるが、長い同一節の循環とは区別する。数値と図表の事実性は認定しない。'),
('validation-env-05',[2,2,2,2,2],True,False,'循環分野の経済活動に関する国際協力という初文は自然。後続は我が国の我が国の・経済産業省におけるの重複、産業と省庁の修飾混同、いわゆっくという語形崩れと未完文がある。対象・節は変化し、長い同一節の循環とは分類しない。非EOSでも非ループと全文意味を区別する。'),
('validation-env-06',[0,0,1,0,0],False,True,'目標に続けて海洋ごみ対策法と法律番号・に基づきを延々重ね、整備の主文が閉じない。法律や年を変えても文の意味は進展しない。'),
('validation-jma-07',[0,0,1,2,2],True,True,'発生をお知らせると予想される避難をとるという活用・修飾・主述が不成立。後続で噴火警戒レベルを付してという長い同句を近接3回重ね、警報が警報・注意報を発表する関係も崩れる。観測範囲の反復としてloopとし、無限反復を数学的に証明したとはしない。'),
('validation-jma-08',[1,0,0,2,2],True,False,'速報版の発表状況・浸水害と高解像度予報を未完成の並列でつなぎ、発表況を予測を発表という対象と助詞が不成立。解析雨量の解説・基準・分布・5段階分析の関係も不明。5文でEOS、短い語の重複はあるが長い同一節の循環ではない。'),
('validation-mdn-new-00',[2,1,1,2,2],True,True,'初文は構文上成立するがCSSオブジェクトのプロパティという返却対象・関数との関係が曖昧。後続ではSVGプロパティを返すという同じ節を延々重ね、説明が進まない。事実の正しさだけを全文意味の尺度にはしない。'),
('validation-mdn-new-01',[2,1,2,2,2],True,True,'初文はHTMLのグローバル属性という話題を自然な構文で維持する。定義と指定・保持との役割は曖昧なためmeaning1、固定合計基準では初文合格。後続は要素を指定できる・できないを混在させ、目的語と要素の再帰を延々繰り返す。'),
('validation-mdn-new-02',[2,0,1,2,2],True,False,'複雑なInternateTormStreamToker等の識別子とIDBKeyRangeの操作関係が不明。後続はDOMElementやSetchの呼び出し、呼び出せるかの確認へ移り、説明対象・目的が定まらず末尾も未完。長い同一節循環はなく、DOMElementの節の一度の局所重複はnonloopとする。未知名詞だけを機械的に不合格にした自動判定ではない。'),
('validation-mdn-new-03',[1,1,1,2,2],True,True,'信頼型オブジェクトの定義からSVGオブジェクトを参照してくださいという指示へ移り、ポリシーと参照・返却の関係が不明。以後はSVGオブジェクトを返す・メソッドを返すを延々反復する。'),
('validation-stat-new-00',[0,0,1,0,0],False,True,'企業のオンラインショッピングからウェブサイトを提供するCSSリクエストという対象混同へ移り、同じ句とCSSSの文字列を反復する。主文が閉じない。'),
('validation-stat-new-01',[1,0,0,0,0],False,True,'客観的な取組を進めに続けて説明のない件数を列挙し、品質管理から水質汚濁へ飛ぶ。同じ数値と水質汚濁に係るものが減少する句を長く反復し、文が閉じない。'),
('validation-bunka-new-00',[0,0,1,2,2],True,True,'副大臣が表彰のための施策を開催したという目的語と動作が不自然。以後は日米首脳会談を繰り返し、会談を発出・会議を公表する動作関係と話題が崩れる。'),
('validation-bunka-new-01',[1,1,1,2,2],True,True,'この法附則の説明で施策を講じられていますは助詞・態の関係が不自然。以後は文化観光法に基づきを繰り返し、化学物質管理施設の観光推進へ話題が飛ぶ。')]
p=ROOT/'new-validation.json';g=json.loads(p.read_text());expected='80043c32264109bc73ce422b97b522828ef38f94b8bda2f9db28df4fb8b0330c'
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
assert g['training']['completedSteps']==g['training']['bestStep']==10000
assert [r['id'] for r in g['rows']]==[j[0] for j in judgments]
rows=[dict(id=i,**dict(zip(['grammar','meaning','connection','repetition','breaks'],scores)),sentenceClosed=closed,fullOutputLoop=loop,fullOutputMeaningful=False,reason=reason) for i,scores,closed,loop,reason in judgments]
m=dict(generationSha256=expected,meaningPolicySha256=hashlib.sha256((ROOT.parents[1]/'round10/full-meaning-policy.json').read_bytes()).hexdigest(),reviewer='Assistant manual reading of all17 unedited Round13 step10000 continuations; not independent or blind human scoring',rows=rows,note='Exact generation bound, no training targets or automatic grader. Short repetitions and EOS status are separate from long observed clause recurrence and full meaning. Unsupported facts are not certified; ambiguous wording remains a manual-review limitation.')
(ROOT/'new-manual.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
