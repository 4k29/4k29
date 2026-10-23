import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];O=R/'execution/paired-daily-generation-1000';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
reasons={38:[
'帰りに行きたいの目的地を省いたまま、何をしてもらうかという別の質問へ移る。行為と話者のつながりが成立しない。有限非loop。',
'夕食は大丈夫でしたという短い完結した継続。残り物があり夕食を賄えたという通常の省略を許しwhole1。料理名や外部事実は補わない。R37同一書き出し同一出力の既存judgmentと一致。具体的な調理内容の証明ではない。',
'友達の予定から日常生活・日本・地震へ逸れ、日本のと海溝沿いの同じ構文を長く反復し192tokensで途切れる。',
'準備を継がず雨が降ってを192tokensほぼ反復。',
'寝るのは何か寝るのかなの問いを重ね、更に同じ句を入れ子反復してEOS。有限49tokensでも主述の進行を失うloopをprimaryとする。有限問い直しとして非loopに寄せる感度を別記。',
'まずはどこかへ行くのがを3回重ねる未成立な文。19tokensで有限EOSなのでprimary非長期loopだが侵入反復。広くloopと数える代替も保持。',
'待ち合わせの時刻に対しておいしいと言うのですという引用が返り意味がつながらない。',
'今日はの連打から日曜日・夕日に逸れ、反復を続け192tokensで切れる。疲労への応答が成立しない。',
'卵の調理への応答がなく、人間への不明な質問からそうですねと私もいろいろの長いloopへ移り192tokensで切れる。',
'週末の出来事を答えず、おいしそうですか・あなたは等の言葉についての不明な引用と受身になる。有限非loop。',
'近況への応答がAIがおいしそうなのかなという不自然な主述に置き換わる。短いEOSでも意味不成立。',
'公園の所有句を多数連打し、整備を行くという崩れた行為へ転じる。EOSでも同じ所有句loop。'],39:[
'帰りに行くのがいないのでと主述・因果が崩れ、今日は何か行かないという不自然な質問へ移る。有限EOS非loop。',
'夕食は何か食べるのでしょうかという主体・因果の弱い疑問となり、残り物を使う自然な継続にならない。R38 selected同一prefix/textと同じprimarywhole0。未提示他者への食事確認という弱い代替を別記。',
'友達と会う予定から日常生活にあることを目的に確実に伝わるという関係不成立の説明へ逸れ、活発なされると活用も崩れる。有限68tokensのprimary非loopだが日常生活の侵入反復、広いloop代替あり。',
'雨が降ると・降り降り等の崩れた活用を192tokens反復し準備を継げない。',
'寝ると寝る・寝るを192tokens反復。',
'趣味を始める話から何かのようなものを書いているのでしょうかという無内容な疑問へ移り、行動・対象がつながらない。有限EOS非loop。',
'時刻の相談に天気の毒が出来るのかという語結合・主述も不明な問いを返す。有限EOS非loop。',
'疲れへの応答がなく今日はを何度も連打し、暮らす・泊まるという行為へ逸れる。有限83tokensのEOSでもprimaryloop、単なる自然な相槌とはしない。',
'自分は何かの時間にかかわいという未成立の活用・主述で終わり、卵の調理相談に関係しない。13tokensEOS非loop。',
'週末の体験を答えず今日はお休みですかという言葉についての不明な説明になる。二度の引用は有限でprimary非loopだが侵入反復。',
'近況への応答がAIがお米が多いかもしれないのでしょうかという不成立な主語連結・意味へ逸れる。有限EOS非loop。',
'公園に行かない・行きたいを並べ、既に予定として提示された公園について再質問する。対策や自然な応答が成立しない。有限42tokensでprimary非長期loopだが所有句反復は侵入。広いloop代替あり。']}
assert sha(O/'round38.json')=='c7d8bf6cdf3dd8cc504b9120a3a52734538acafb54f42dca38db65875dd510fb'
assert sha(O/'round39.json')=='32ccd98d255ca92c6fea20a777be48313777aaa204d25bf2554e6420c98c4763'
reports=[]
for n in [38,39]:
 p=O/f'round{n}.json';g=read(p);rows=[];loops={2,3,4,7,8,11}if n==38 else{3,4,7};intrusive=loops|({5}if n==38 else{2,9,11})
 for i,(x,reason)in enumerate(zip(g['rows'],reasons[n],strict=True)):
  assert x['validUtf8']and x['validTokens'];h=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();rows.append(dict(id=x['id'],fullOutputMeaningful=n==38 and i==1,fullOutputLoop=i in loops,intrusiveRepetition=i in intrusive,reason=reason,prefixAndTextSha256=h))
 a=dict(generationSha256=sha(p),actualEvaluatedUpdates=1000,all12FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=sum(r['fullOutputMeaningful']for r in rows),longLoopsPrimary=sum(r['fullOutputLoop']for r in rows),eos=sum(x['eos']for x in g['rows']),notIndependentBlindHuman=True,notNewTest=True,notUsedForSelection=True,final10000AssessmentStillPending=True,rawFp32PythonOnly=True,rows=rows);dest=O/f'round{n}-reading.json';dest.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');reports.append(dict(round=n,wholeMeaning=a['wholeMeaning'],longLoopsPrimary=a['longLoopsPrimary'],eos=a['eos'],generationSha256=sha(p),readingSha256=sha(dest)))
review=dict(actualUpdatesEach=1000,all24FullPrefixesAndContinuationsActuallyRead=True,states=reports,interpretation='Shorter/EOS and fewer primary loops do not establish better meaning; new primarywhole0 versus old1. Matched humanDEV NLL difference -0.00005321294 remains tiny. Posthoc interim evidence, not official final gates.',sensitivities={'oldSleepFiniteInsteadOfLoop':'old loops5 rather than6','oldShortHobbyBroadLoop':'old loops7 rather than6','newFiniteWeekendAndParkBroadLoop':'new loops4 or5 rather than3','strictDinnerSpecificity':'oldwhole0 rather than1; not primary and identical historical text keeps same primary judgment','allowUnstatedOtherPersonDinnerQuestion':'newwhole1 rather than0; weak contextual alternative only'},notNewTest=True,notUsedForSelection=True,publicModelChanged=False,additionalOptimizerUpdates=0)
(O/'reading-complete.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');print(json.dumps(review,ensure_ascii=False))
