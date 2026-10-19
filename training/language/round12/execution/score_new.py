"""Manual reading of this exact completed Round12 raw generation only."""
import pathlib,json,hashlib
ROOT=pathlib.Path(__file__).resolve().parent
judgments=[
('validation-aozora-00',[2,2,2,2,2],True,True,'初文「のぼりはじめました」は自然。その後は虫からおじょうちゃんへ飛び、同じ所有関係を延々と反復する。全文意味は成立しない。'),
('validation-aozora-01',[2,1,1,2,2],True,True,'「寒さを防ぐために出て来た」は構文上成立するが、寒さを防ぐ行動として外へ出る目的関係が文脈から自然に定まらない。後続は夜の夜・夕方の夕方を反復し、「かくてはいって」「かかえりとり」へ崩れる。初文だけの局所改善を全文合格にしない。'),
('validation-aozora-02',[2,2,2,2,2],True,True,'葦が風のなかにかくれてしまったという初文は物語の擬人化とつながり自然。後続は「二人はもう一人」という人数・参照の破綻、「暮れてしまった」という動作の不整合から村の村の反復に崩れる。'),
('validation-mic-03',[0,0,0,0,0],True,False,'eシールの取組を立ち上げた説明から「AI exter exter」の高い高いシンガポールをクリックしたという不明な目的語・動作へ崩れる。一文でEOS、短い局所反復はあるが長い循環ではない。全文意味は不合格。'),
('validation-mic-04',[2,2,2,2,2],True,False,'初文は市場規模の自然な補完。後続は市場規模から赤字・出荷額へ飛び、携帯基地局と企業のシェア、MicrosoftとHuauaの関係が不明。「Microsoftが」を繰り返し内訳・単位・構文が崩れ、主文が閉じない。Microsoftの短い局所反復はあるが、対象と数値が変化し、長い同一節の循環とは分類しない。非EOSでも非ループとし、意味の破綻と区別する。数値や図表の事実性は認定しない。'),
('validation-env-05',[1,1,1,0,2],True,True,'法律と同法の番号を重ね、金融機関の経済活動と法改正の関係が不明。後続は第1回締約国会議・第1回日中韓国との句を繰り返し、主述・接続が成立しない。'),
('validation-env-06',[0,0,0,0,0],False,True,'目標に続く「改正事業者の改正事業の改正」が意味をなさず、海洋ごみ対策法と法律番号・に基づきを反復し続ける。閉じた主文がない。'),
('validation-jma-07',[0,0,0,2,2],True,True,'「発生をお知らせるおそれ」「旨を警戒を呼びかける範囲には」は活用・修飾・助詞が破綻。噴火速報と警戒レベル・警報予報を混同し、後半は噴火警報・予報を延々繰り返す。'),
('validation-jma-08',[1,0,1,2,2],True,False,'「解析雨量は発表状況の検討を行います」は数量データが検討を行うという主述の不成立。後続の参照文も予測処理との関係を補わない。二文でEOS、循環はないが全文意味は不合格。'),
('validation-mdn-new-00',[2,1,1,2,2],True,True,'CSS関数がCSSオブジェクトを返すという説明では返す対象の意味関係が曖昧。後続は同じメソッドを返す・配列の配列を返すを反復し、関数とメソッド・返却型を混同する。'),
('validation-mdn-new-01',[2,2,2,2,2],True,True,'初文のグローバル属性を設定できるという説明は自然。以後はHTML要素をHTML要素をと目的語を重ね、要素と属性の関係が崩れて反復する。'),
('validation-mdn-new-02',[2,0,1,2,2],True,False,'インターフェイスのメソッドという局所補完は自然だが、Internationオブジェクトという不明な返却対象を作り、IDBKeyRangeとの意味関係が成立しない。一文でEOS、非ループでも全文意味不合格。'),
('validation-mdn-new-03',[1,1,1,2,2],True,True,'ポリシーオブジェクトを使用してURLオブジェクトを返すという説明は述語の接続・意味関係が不明。後続はURLオブジェクトと「このメソッドを返します」を延々反復し説明が進まない。'),
('validation-stat-new-00',[1,1,1,0,2],True,True,'「ウェブサイトではデータを提供する際に使われます」は何が使われるか主述が不明。情報を提供する方法を提供するを反復し、企業のオンラインショッピングからWebGLへ話題が飛ぶ。'),
('validation-stat-new-01',[1,1,1,2,2],True,True,'「データなどの客観的な取組」は語の関係が不自然。以後は品質管理から販売・資金・法へ飛び、「管理や管理」「関係省庁と連携しつつ」を長く反復する。'),
('validation-bunka-new-00',[0,0,1,2,2],True,True,'小林副大臣が「国際協力機関の参加を開催」したという目的語・動作が不成立。後続でアジア太平洋地域と国際協力覚書の下を反復し、表彰・会合・文化政策との関係が崩れる。'),
('validation-bunka-new-01',[2,2,2,2,2],True,True,'必要な施策を講じるという初文は自然。後続は文化観光法の検討から締約国会議へ飛び、同じ日付・会合・閣議決定を繰り返し、法律条項と会合を混同する。')]
p=ROOT/'new-validation.json';g=json.loads(p.read_text());expected='2107ef2dcda95855bba86bfba41d19c33404ea0d4f96caf29f6be29e1ee6b081'
assert hashlib.sha256(p.read_bytes()).hexdigest()==expected
assert g['training']['completedSteps']==g['training']['bestStep']==10000
assert [r['id'] for r in g['rows']]==[j[0] for j in judgments]
rows=[dict(id=i,**dict(zip(['grammar','meaning','connection','repetition','breaks'],scores)),sentenceClosed=closed,fullOutputLoop=loop,fullOutputMeaningful=False,reason=reason) for i,scores,closed,loop,reason in judgments]
m=dict(generationSha256=expected,meaningPolicySha256=hashlib.sha256((ROOT.parents[1]/'round10/full-meaning-policy.json').read_bytes()).hexdigest(),reviewer='Assistant manual reading of every unedited Round12 step10000 continuation; not independent or blind human scoring',rows=rows,note='Exact generation bound judgments; not an automatic grader or training targets. Bounded short EOS does not establish meaning. All full outputs read; no repairs or penalties.')
(ROOT/'new-manual.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
