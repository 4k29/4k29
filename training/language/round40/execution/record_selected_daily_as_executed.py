"""Historical SHA-bound actual12 reading, not a reusable semantic grader."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';p=E/'daily-new-python.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(p)=='4fc12dbe85011b7aa7aa8b66d4c14993045c163f1ebce04d451e3a77e4913145';g=json.loads(p.read_text());assert len(g['rows'])==12
reasons=[
'帰りに行くのが行くのは何かの事だろうと思いますかと主述・行動の関係が成立せず、問いへ逸れる。有限19tokensEOSでprimary非loopだが行くのが等の侵入反復。',
'夕食は何か食べるのでしょうかという主体・因果の弱い疑問となり、残り物からの自然な継続にならない。同一prefix/textのR39と同じprimarywhole0。未提示の他者への食事確認という弱い代替は別記。',
'友達と会う予定から日常生活・週間天気予報の説明へ逸れ、先に行く予報・どのくらい等を192tokens反復して切れる。',
'出かける前の行動を継げず、降り降り・降雨雨・雨が降って等を192tokens反復する。',
'今夜は寝るのかなの後、寝るのは何か寝てるんですかと意味の弱い問いを続ける。有限19tokensのprimary非長期loopだが侵入反復で、自然な早寝の方針につながらない。',
'行くのがを重ね、その後、おもしろいろいろ、おかあさんの所有句やおおお等を192tokens反復して意味が崩れる。',
'時刻の相談に天気の毒が出るのかと語結合・主述も不明な質問を返し、待ち合わせの回答にならない。短いEOS非loop。',
'疲れへの応答がなく、天井に出てきた・今日は一緒に出てきた・それを等を長く反復して192tokensで切れる。',
'卵の調理相談に対して何かの時間を作るのが多いのでしょうかという別の不明な質問になる。有限19tokensEOS非loop。',
'週末の体験に答えず、天気はどうしてもかなりそうですねという述語・意味の崩れた返答になる。有限12tokensEOS非loop。',
'近況への応答がなく、天井の話をどんな話を聞いているのかという話題と係りの弱い問いへ逸れる。有限15tokensEOS非loop。',
'雨で公園の予定をどうするかの相談を継げず、公園の公園という所有句を重ねて既出の行く予定を再質問する。有限14tokensEOSでprimary非長期loop、侵入反復はあり。']
loops={2,3,5,7};intrusive=loops|{0,4,11};rows=[]
for i,x in enumerate(g['rows']):rows.append(dict(id=x['id'],fullOutputMeaningful=False,fullOutputLoop=i in loops,intrusiveRepetition=i in intrusive,reason=reasons[i],prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
r=dict(generationSha256=sha(p),actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=9000,all12FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=0,longLoopsPrimary=4,eos=sum(x['eos'] for x in g['rows']),notIndependentBlindHuman=True,notNewTest=True,notUsedForSelection=True,wholeMeaningSensitivityPermittingUnstatedOtherPersonDinnerQuestion=1,nonloopSensitivityTreatingFiniteEarlyAndSleepRepetitionAsLoops=6,rows=rows)
assert r['eos']==8;(E/'daily-new-reading.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n');print('Saved12 actual selected daily readings,whole0,loops4,EOS8')
