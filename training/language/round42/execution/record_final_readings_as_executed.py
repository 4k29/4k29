import pathlib,json,hashlib
R=pathlib.Path('/workspace/4k29/training/language/round42');E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();keys=['grammar','meaning','connection','repetition','breaks','sentenceClosed'];first={};whole={};refs=[]
spec=[('original17','new-validation.json','new-manual.json'),('daily12','daily-new-python.json','daily-new-reading.json'),('native8','content-native-dev/new-python.json','content-native-dev/new-reading.json'),('mrmp5','fixed-source-mrmp-dev/new-python.json','fixed-source-mrmp-dev/new-reading.json')]
for n in [39,40,41]:
 p=R.parent/f'round{n}';bound={x['path']:x for x in read(p/'execution/artifact-manifest.json')['files']}
 for state in ['selected','terminal']:
  for group,g,m in spec:
   if state=='terminal':g=f'terminal-state-diagnostic/{group}-python.json';m=f'terminal-state-diagnostic/{group}-'+('manual.json' if group=='original17' else 'reading.json')
   gp=p/'execution'/g;mp=p/'execution'/m
   assert sha(gp)==bound[str(gp.relative_to(p))]['sha256'] and sha(mp)==bound[str(mp.relative_to(p))]['sha256']
   a,b=read(gp),read(mp);assert b['generationSha256']==sha(gp)
   for x,y in zip(a['rows'],b['rows'],strict=True):
    loc=f'R{n}/{state}/{group}/{x["id"]}'
    if group=='original17' and '。' in x['text']:
     k=x['prefix']+x['text'].split('。')[0]+'。';v={z:y[z] for z in keys}
     if k in first:assert first[k][0]==v
     first[k]=(v,loc)
    k=(x['prefix'],x['text']);v=(y['fullOutputMeaningful'],y['fullOutputLoop'])
    if k in whole:assert whole[k][0]==v,(loc,whole[k])
    whole[k]=(v,loc)
   refs.append(dict(round=n,state=state,group=group,generationSha256=sha(gp),manualSha256=sha(mp)))

# Frozen historical outputs only; must never apply these judgments to a later trial.
assert sha(E/'new-validation.json')=='934ecc14b251afca2a21f15e3a36698b3ef41d59007c5c8bb886d25b36855244'
assert sha(E/'daily-new-python.json')=='09c6c101ae504e7d2a15b409c140732406852e69eab6dd3f66823fcc1f98f232'
assert sha(E/'content-native-dev/new-python.json')=='c11ec5f11b8b1a7d1c6f0eb2c972982bb544dbb85c33e8e3f20c425b1ce57895'
assert sha(E/'fixed-source-mrmp-dev/new-python.json')=='17cb78f3c0dfed45c5c2123f22e707cc38fec245ead7a7fc56f2e10d4fe6ed3e'
assert sha(E/'terminal-state-diagnostic/original17-python.json')=='71086f8ee1cd79f419fbd1383cf09f83a7fa08af28d741b5117a7a1741825666'
assert sha(E/'terminal-state-diagnostic/daily12-python.json')=='f82d1aaceccc6b377b947059c19091ea6e2f543dba8232aa62c8e19a19eeea35'
assert sha(E/'terminal-state-diagnostic/native8-python.json')=='4861731ab15b607aea9ed0b34e5c12007dd501e7f2116828ef81d957ece29efd'
assert sha(E/'terminal-state-diagnostic/mrmp5-python.json')=='8326ca9379873e2bd90e44be50751ff9f967df29925fcb813804b2387ea6283c'

# Explicit judgments after reading every new complete prefix/continuation in this session.
reasons={
 'selected':{
 'original17':[
 '初文は自然に閉じるが、家族呼称と所有・主語句の長い反復で引用と文が崩れる。創作人物自体は失敗理由でない。',
 '寒さ回避の因果が弱い同一初文の従来判定を保持。夜の夜を長く反復して主述が崩れる。寒い場所から出たと補う代替は別記。',
 '風のなかにかけていて、お光りがあっていたの動作・項の結合が弱い。その後お母様とおおおを長く反復。',
 '引用名称がInternation等の長い断片反復になり文と引用が閉じない。未知名自体を失敗理由としない。',
 '初文は自然だが情報端末の主要202億円という内訳の項と修飾が不成立。短いEOS非loop。数値の外部真偽だけで落とさない。',
 '同法と再生可能エネルギーの創出を繰り返して同じ目的・述語が停滞する。',
 '初文は旧と同じで自然。後は海域の海域を長く反復し、規制・移行の関係が崩れる。',
 '速報が共同検討を行うという主語と行為の関係、噴火警戒レベルと大雨特別警報の結合が弱い。以後も警戒レベルの述語を循環する。',
 '解析雨量は速報版の発表状況を把握という主体・用途の関係が弱い。同一初文の旧判定を維持。全文は短く非loop。',
 'SVGプロパティをの二重目的語。後も要素を指定するの長い循環で意味が崩れる。',
 '初文は自然だが以後要素を指定するの長い循環。',
 '初文は未知名称を許せば自然で旧判定を保持。後のcomportype等の名前断片の長い循環で崩れる。',
 'SVGリクエストを提供するを二重化した初文から、送信するを長く重ねる。',
 '方法を提供する方法の同一初文。後はWebGLのを長く反復し主題が失われる。',
 '客観的な取組という語の種類の弱さは従来と同じ。後は調査票を提出・記入を長く反復して目的が崩れる。',
 '文化大臣の表現のためにの項が弱く、アジアを長く反復し文が閉じない。',
 '施策を講じられていますの主体・助詞は旧判定と同じ。後は文化庁長官民連携の下を長く反復。'],
 'daily12':[
 '帰りに行くのが一番好きという行先を欠く接続から、何かの事を聞いている等を長く循環して主述も崩れる。',
 '卵とキャベツが残った因果から夕食は何か食べたかったかという相手への過去の問いに移る。問い自体の文法は認めるがprimary接続不足。未提示他者への希望確認の弱い別解は残す。',
 '友人との予定から予報の説明へ逸れ、週間天気予報の同じ問いを反復し、発表して発表へ崩れる。',
 '出かける前の自然な準備を続けられず降り・雨雨を長く連打する。',
 '今夜は寝るのかなという確認から寝る時間が寝るという主述へ崩れる。有限二文EOSでprimary非長期loop。',
 '行くのが・その後・家族所有句を長く反復し趣味の話が失われる。',
 '時刻の質問に天気の毒が出るのかと返し、語結合と文脈が不成立。',
 '天井に出かけてもらえたという行為の項が弱く、今日は三連続の侵入反復。有限の短い疑問EOSでprimary非長期loop。',
 '卵を使う料理の問いから自分は何かの時間を作るのが多いという曖昧な時間の話へ逸れる。',
 '週末の過ごし方から天気・ご飯への問いへ逸れ、どうしてもと疑問の関係も弱い。',
 '近況の質問への天井の話はどんな話を聞いているのかという対象・主語の関係が弱い。',
 '雨で公園予定をどうするかに、公園の公園という侵入重複と行かないですかという方向の弱い問い。短い有限EOSでprimary非loop。重複を除去して採点しない。'],
 'native8':[
 '歩くことが健康によいという話への私も好きですという普通の対象省略を許す自然な共有の好み。最小の意味成立で具体名・新情報はない。',
 'バイクのレストアからおいしいですという味覚へ逸れる。',
 '挨拶切替から味覚へ逸れ、そうなんですね・それはどうしてもおいしいですねの同じ複合相槌を三回反復する。EOSでもprimaryloop。',
 '酸っぱい飲料をおいしく飲む方法に同じおいしいですねを十回ほど重ね停滞。EOSでもloop。',
 '暑さと外出回避から今日は何かのことですかという対象不明の問いになる。同一全文の従来判定。',
 '女優の好みを既に述べた相手にあなたはと問い返し、話者と質問対象が曖昧。未提示の別の好みを尋ねる普通の省略ならwhole1の代替。新情報の欠如だけでは落とさない。',
 'ストックを積み上げメモすると説明した後、それはどんなことですかという問いの対象が曖昧。同一全文の従来primary0、呼称の具体化要求ならwhole1の代替。',
 'パスタがおいしいという直前発話への自然な同意。最小の意味成立で具体名・新情報はない。'],
 'mrmp5':[
 '仕事とポップコーンの香りの話からおすすめですかという対象不明の問いになる。仕事や食べ物への推薦確認と補う弱い代替whole1。',
 'お母さんの子供の世代所有句を有限二つの名詞句で重ね、主述と項も弱い。旧R40と同型の短いEOSでprimary非長期loop、強い侵入反復。family-recursionを広くloopとすれば別集計。',
 '土産店・ロープウェイの話へのあとはの追加対象が曖昧でprimary0。同一全文の旧判定。別の購入場所を尋ねる省略ならwhole1。',
 'スカイダイビング願望にあなたは何かのことですかと対象・述語不成立の問いを返す。同一全文の旧判定。',
 '洗面所問題から今日は毎日を長く連打し、述語が成立しない。']},
 'terminal':{
 'original17':[
 '初文は自然だが後はおじいちゃんと所有句を長く循環して引用と主述が崩れる。',
 '寒さを防ぐために出て来たという同一初文の因果の弱さを旧と同じ判定。以後夜の夜を長く反復。',
 '風のなかにかきらがあってという語結合が弱く、ぼんやりとぼくのの長い断片反復へ移る。初文も閉じない。',
 '名称断片Internation等を長く反復して引用と文が閉じない。未知名称そのものを落とすのではない。',
 '初文は自然だが内訳の項が不成立で、放送事業に係るものを長く反復し人口減少へ逸れる。数値の外部真偽のみを失敗理由としない。',
 '初文は同法に基づくを有限に重ねる侵入反復で旧と同じ。後の会議・年号・閣議決定の項と引用が崩れるが、同じ系列が長く循環するloopとは区別する。capだけでloopとしない。',
 '海域の海域の長い所有句反復が初文から続き、海域を推進するなど項・行為も弱い。',
 '速報が共同検討を行うという主語・行為の関係と大雨警戒との結合が弱い。後もレベル運用と発表の同じ述語を循環する。',
 '解析雨量が発表状況を把握という同一初文の主述・用途の弱さを保持。短い有限EOS非loop。',
 'SVGプロパティをという二重目的語から値が指定された場合の長い循環へ進む。',
 '初文は自然だが要素を指定・設定の長い循環へ進む。',
 '未知名称を許せば自然な旧と同じ初文。以後配列の配列を長く反復し形も崩れる。',
 '初文は自然な旧と同じSVG提供文。後はSVGリクエストを送信するを一つの文内で何度も循環する。短く閉じてもprimaryloop、有限の構文重複と見る非loop感度を残す。',
 '方法を提供する方法の同一初文。後はWebGLのを長く反復して文脈が崩れる。',
 '初文の客観的な取組の種類の弱さは旧と同じ。以後管理の連打・法律・省庁への逸脱が続く。',
 '大臣の表現のためという接続の弱さに、アジアの十五回ほどの反復。EOSでもprimaryloop。',
 '施策を講じられていますという同一初文の項の弱さ。以後地方公共団体と地域計画を長く反復する。'],
 'daily12':[
 '帰りに行くのがいないのでと人・行為の関係が成立せず、何をしてくれるのかへ逸れる。短いEOS非loop。',
 '夕食は何か食べたいですかは文法的な問いだが、残り物がある自分の夕食から未提示他者への希望確認となる。同系列の旧primary0を保持。他者への普通の希望質問ならwhole1の代替。',
 '友人との予定から日常生活・17時・日本の説明へ逸れ、語結合・日数の関係が崩れる。日常生活の侵入反復は強いが有限で異なる四文へ進むためprimary非長期loop。広い語彙循環ならloop感度あり。cap自体ではloopにしない。',
 '雨が降りますかと降るのは等の同じ問いを長く循環し活用も崩れる。',
 '寝ると寝るから寝るだけの長い反復に陥る。',
 '行くのが・その後・家族所有句を長く反復し趣味の予定との意味が失われる。',
 '時刻の問いから天気の毒へ逸れ、二つの疑問とも語結合が弱い。有限EOS非loop。',
 '疲れの訴えに友人は今日は三連続の後、食べたいかという問いへ逸れる。短い侵入stutterでprimary非長期loop。',
 '自分は何かの時間にかかわいという不成立文から今日はいを二度返す。有限二つの短い反復でprimary非長期loop。',
 '週末の行動からおいしそうという言葉についてのメタ疑問へ逸れる。引用二度の有限文でprimary非長期loop。',
 '近況の質問においしいと言うという未提示の引用行為を返し、対象と話題が接続しない。',
 '公園の公園を長く反復し、雨での予定変更から公園整備の行政文へ逸れる。EOSでもloop。'],
 'native8':[
 '歩行健康の話から私もお好きですかという自分への好意確認に移り、話者と対象が成立しない。同一全文の旧判定。',
 'バイクの説明からおいしいですへ逸れる。同一全文の旧判定。',
 '挨拶時刻の説明から私も今日は何かお好きですかという対象・話者の弱い問いへ逸れる。',
 '酸っぱい飲料の飲み方からおいしいですよねだけを長く循環して閉じない。',
 '暑さの話から何かのことですかという曖昧な問い。同一全文の旧判定。',
 '女優の好みへの私も好きですという自然な共有の好み。同一全文の旧判定。具体名・新情報の成立とは区別。',
 'ストックとメモから米の好みへ逸れ、おいしいですよねと複合相槌を長く循環する。EOSでもloop。',
 'パスタの味への自然な同意。同一全文の旧判定。最小の意味成立で具体名や新情報はない。'],
 'mrmp5':[
 '仕事内容と香りの話にお話ししますと宣言するが、どの問いや内容を続けるかが曖昧なまま閉じる。会話継続の申し出と補う普通の省略ならwhole1の代替。',
 'お母さんと子供の世代所有句を長く反復し子供子などへ崩れる。',
 '土産店・ロープウェイの話へのあとはの対象が曖昧。同一全文の旧primary0、場所の追加確認ならwhole1。',
 'スカイダイビング願望に何かのお話ありますかと返し、何を聞くかが弱い。問いの文法を破綻とはしない。経験やきっかけを尋ねる普通の省略ならwhole1の代替。',
 '洗面所の話から毎日を長く連打し述語が成立しない。']}}
loops={'selected':{'original17':set(range(17))-{4,8},'daily12':{0,2,3,5},'native8':{2,3},'mrmp5':{4}},'terminal':{'original17':set(range(17))-{5,8},'daily12':{3,4,5,11},'native8':{3,6},'mrmp5':{1,4}}}
meaning={'selected':{'original17':set(),'daily12':set(),'native8':{0,7},'mrmp5':set()},'terminal':{'original17':set(),'daily12':set(),'native8':{5,7},'mrmp5':set()}}
fresh={'selected':{2:[1,1,1,2,1,True],3:[0,0,0,0,0,False],7:[1,1,1,2,1,True],15:[0,0,0,0,0,False]},'terminal':{2:[0,0,1,0,0,False],3:[0,0,0,0,0,False],6:[2,1,2,0,1,True],7:[1,1,1,2,1,True],15:[1,1,1,0,1,True]}}
for state in ['selected','terminal']:
 for group,g,m in spec:
  if state=='terminal':g=f'terminal-state-diagnostic/{group}-python.json';m=f'terminal-state-diagnostic/{group}-'+('manual.json' if group=='original17' else 'reading.json')
  gp=E/g;mp=E/m;gen=read(gp);rows=[]
  for i,x in enumerate(gen['rows']):
   k=(x['prefix'],x['text']);v=(i in meaning[state][group],i in loops[state][group])
   if k in whole:assert v==whole[k][0],(state,group,i,v,whole[k])
   row=dict(id=x['id'],fullOutputMeaningful=v[0],fullOutputLoop=v[1],intrusiveRepetition=v[1] or (group=='original17' and i in {5,9,12,13}) or (group=='daily12' and i in ({7,11} if state=='selected' else {2,7,8,9})) or (group=='mrmp5' and i==1),reason=reasons[state][group][i],prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
   if group=='original17':
    f=x['prefix']+x['text'].split('。')[0]+'。' if '。' in x['text'] else None
    if f in first:scores,loc=first[f];row.update(scores,firstSentenceScoreProvenance='Literal full prefix+observed first sentence matches '+loc+'; components unchanged')
    else:row.update(dict(zip(keys,fresh[state][i])),firstSentenceScoreProvenance='Fresh complete first sentence or unclosed continuation actually read; no automated semantic grader')
   rows.append(row)
  out=dict(generationSha256=sha(gp),actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=9000 if state=='selected' else 10000,allFullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=sum(x['fullOutputMeaningful']for x in rows),longLoopsPrimary=sum(x['fullOutputLoop']for x in rows),eos=sum(x['eos']for x in gen['rows']),notIndependentBlindHuman=True,notNewTest=True,notUsedForSelection=True,noOutputRepair=True,rows=rows)
  if group=='original17':out.update(meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant actual complete R42 full reading, not independent blind human',historicalFirstSentenceReferences=refs)
  out['semanticSensitivitiesSeparatelyReported']=True
  if group=='daily12':out['sensitivities']={'ordinaryUnstatedOtherPersonDinnerQuestionWhole':1,'broadLoopIncludingShortStutterAndCompoundDuplication':'primary counts retained; short today/cooking repetitions and finite prose separately described in row reasons','terminalFiniteProseWeekendAsLoop':5 if state=='terminal' else None}
  if group=='native8':out.update(explicitRelevantReference=0,newRelevantInformation=0,sensitivities={'ordinaryClarificationOrPreferenceEllipsisWhole':4 if state=='selected' else 2})
  if group=='mrmp5':out['sensitivities']={'ordinaryOmittedTargetsWhole':2 if state=='selected' else 3,'finiteFamilyRecursionAsLoop':2 if state=='selected' else 2}
  mp.parent.mkdir(exist_ok=True);mp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(state,group,out['wholeMeaning'],out['longLoopsPrimary'],out['eos'])
