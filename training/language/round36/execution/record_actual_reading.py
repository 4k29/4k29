"""Explicit judgments after all84 full saved outputs were actually displayed/read."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';P=R.parent/'round35/execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def digest(r):return hashlib.sha256(json.dumps(dict(prefix=r['prefix'],text=r['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
assert read(R/'continue-10000/result.json')['completedSteps']==10000
expected={'selected':{'original17':'603774813e136ff7b1921ce3748c2aea103ce97a7db1ae8465f0dda087bce036','daily12':'5ef58ebd5205b5fb7cf8cd54762381da3c40e3a2755974f770e5e7fe9312785a','native8':'1316c9600bec702df4658ef8ca7787eb6a36d6c6c42bb1448b8ee6564aa0856f','mrmp5':'fc709d12c98624c4fba15b339eab052519b529cd49ea261d581400f7ac0f06ad'},'terminal':{'original17':'58be80b1cc3f03ec519115b1849f86e9c12643591340ec8625ab2b0178991f6c','daily12':'894695c3a29198f6466ae2ed4c54b9d08e0d482f2214e0e958d02eeac33cf67a','native8':'bcf7db4bfedda3719b19ccb86b7ca99cf49d4898f53b32d12199fd1738966da2','mrmp5':'1eee141e3a865a41e1c06cb8a05cd7f770da34e98e4ac0c92d63df926c2e3ebd'}}
paths={'original17':'new-validation.json','daily12':'daily-new-python.json','native8':'content-native-dev/new-python.json','mrmp5':'fixed-source-mrmp-dev/new-python.json'};manualpaths={'original17':'new-manual.json','daily12':'daily-new-reading.json','native8':'content-native-dev/new-reading.json','mrmp5':'fixed-source-mrmp-dev/new-reading.json'}
selected_reasons=[
'初文したは自然。子供たちの所有句を再帰し主述・展開が崩れる。',
'寒さを防ぐために出来るは何ができるか欠落。夜の長い反復。同じ旧全文判定を維持。',
'風の中へ駆けて来る時にかきらが現れる初文は創作として許容。後続の活用・母様の所有句が崩れ長く反復。未知名だけを失格にしない。',
'名称の引用が閉じずInternation等を反復。旧全文と同一。',
'市場規模の初文は自然。Stationの反復へ崩れる。旧全文と同一。',
'法律を踏まえ取組を進める初文は同法の局所重複を含む9点。後続は設置の設置や法引用・係りの崩れ。年号の虚偽のみを理由とせず、変化する有限の法説明をprimary非長期loopとする。',
'初文は成立。後続の海洋ごみの水域の水質、重なった法の修飾が崩れる。変化する有限の法列をprimary非長期loopとし強い意味反復の感度も別記。',
'機関の省略を許す従来基準で初文9点。後続は警戒レベルに応じる警戒レベルという循環で全文意味不成立。同じ短文を5回繰り返すR35より変化がありprimary非長期loop、広い反復基準ではloop。',
'初文の解析雨量・把握主体が曖昧。後続の基準を満たす指数の基準を満たす基準という循環で説明が曖昧。EOS111でもprimary意味不成立。非長期loop。緩く警報基準の説明と読めば代替成立あり。',
'初文からSVGプロパティを4回重ね、値・指定を自己参照反復。EOSでも全文不成立。旧全文同一。',
'初文はグローバル属性を設定できる自然な文。後続は指定することでの長い反復。EOSでも不成立。旧全文同一。',
'IDBKeyRangeのメソッドが別オブジェクトのメソッドを返す、という一文がEOSで閉じる。返り値が関数であることは言語として可能で、未知Internation名や実APIとの真偽だけを失格にしない。R35の初文を自然とした同じ基準で全文成立。実API正確性は認定しない。',
'初文のSVGリクエストを送信する方法を提供するは言語として成立。以後同句を長く繰り返し内容が進まない。',
'初文から提供する方法を4回再帰。以後WebGL所有句を反復し崩壊。旧全文同一。',
'客観的な取組の接続が弱い初文。製品の製品・製造の長い反復。旧全文同一。',
'表彰を開催・協力を発揮の係りが不自然。後続は国立公園の長い所有句反復。旧全文同一。',
'初文必要な施策を講じますは自然。法人の長い反復へ崩れる。旧全文同一。']
terminal_reasons=[
'初文は自然。おじいちゃんの主格・所有句を長く反復し引用も閉じない。',
'寒さを防ぐために出て来たは未知の創作状況を許す従来基準で9点。外へ出たと勝手に補わない。後続夜の長い反復。',
'風のなかにかんとりとりあがるの活用が崩れ、以後ああの反復。未知名だけが失格理由ではない。',
'AIのAIの高いシステムという修飾が不明でprimary不成立。引用全体を不透明な固有名として扱えば代替成立あり。旧R35terminal全文同一で主判定・初文7点・非loopを維持。',
'市場規模の初文は自然。種類の種類の再帰や有害なものがカウンターになる飛躍で不成立。EOS115でも長期loop。',
'同法・法律第11号に基づきを反復して主節が閉じず、法引用も崩れる。',
'海洋ごみの所有句と輸出入の長い反復。旧terminal全文同一。',
'共同検討を行う機関の省略を許す基準で初文9点。速報や警報が警報・予報を発表する主語の循環でprimary全文不成立。全節で機関省略を許す弱い読みの感度を残す。有限な警戒説明で非長期loop。旧terminal全文同一。',
'初文の把握主体が曖昧。後続は引用の閉じ方と情報が情報を発表する係りが崩れる。変化する有限の情報列を非長期loop、広い基準ではloop。旧terminal全文同一。',
'初文からSVGプロパティの目的語が重複。後続は値・指定の場合の反復で不成立。',
'初文は成立。要素を指定する要素の循環をEOSまで反復して説明にならない。',
'初文はメソッドが別メソッドを返す自然な文でAPI真偽は別。以後メソッドを呼び出せるを長く反復し全文不成立。',
'初文はSVGリクエストを提供するという言語として成立。送信する際・送信するの長い反復で全文不成立。',
'短いEOSだが提供する方法を提供する際にデータを提供する際に提供するという再帰で何を説明するか不明。局所反復を長期周期loopとは数えない。',
'データなど客観的な手段と統計調査重複で初文8点。以後調査を実施するを長く反復。',
'表彰の施策を開催という目的語・述語関係が不自然。以後法律に基づきを長く繰り返す。',
'施策を講じられていますは通常の受動の目的格が不自然で初文7点。敬語の主体省略と読む感度は別。計画・法に基づくの繰り返しから末尾計画の反復へ崩れる。']
scores={
'selected':[(2,2,2,2,2,True),(2,0,1,2,1,True),(2,1,2,2,2,True),(0,0,1,0,0,False),(2,2,2,2,2,True),(2,2,2,1,2,True),(2,2,2,2,2,True),(2,1,2,2,2,True),(1,1,1,2,1,True),(1,1,2,0,1,True),(2,2,2,2,2,True),(2,2,2,2,2,True),(2,2,2,2,2,True),(1,1,2,0,1,True),(2,1,1,2,2,True),(2,1,1,2,1,True),(2,2,2,2,2,True)],
 'terminal':[(2,2,2,2,2,True),(2,1,2,2,2,True),(1,0,1,0,0,True),(2,1,2,1,1,True),(2,2,2,2,2,True),(0,0,1,0,0,False),(0,0,1,0,0,False),(2,1,2,2,2,True),(1,1,1,2,1,True),(1,1,2,1,1,True),(2,2,2,2,2,True),(2,2,2,2,2,True),(2,2,2,2,2,True),(1,1,2,0,1,True),(2,1,2,1,2,True),(1,1,1,2,1,True),(1,1,2,2,1,True)]}
supp={
('selected','daily12'):['行くのが行かないという不成立から行きたいの反復。','夕食は食べたいの接続が弱く食べたいを反復。','友人と会う文脈から予報へ移り発表していますのでを長く循環。','雨・降の文字反復へ崩壊。','寝ると寝てるなど述語・係りが崩れ反復。','趣味を始める行為を示さず何かの時間にかかるという曖昧句を反復。','待合時刻に答えずおいしいから人々の所有句反復へ。','疲労への応答から食べたいと思い出すの反復・不自然な活用へ。有限変化を広く許す代替非loopはあり得るがprimary長期反復。','料理提案に答えず人間にかかる・大変・今日はいけないを反復。','週末の活動を答えず日曜日と言い出すを循環。','AIが実験してみたいという格が弱い冒頭から相槌といっぱいの長い反復へ。','雨への対応を決めず公園へ行く・行かない・行きたいと同じ往復を長く反復。EOS178でも全文不成立。'],
('terminal','daily12'):['行ったらしかったの活用が崩れいつものの事を書いてを反復。','夕食は大丈夫ですかと逸れ食べたいを長く反復。','友人と会う予定から地震注意の話題へ移り初文も主述不成立。変化する有限の防災文をprimary非長期loop。','雨が降っての長い反復。','寝るのは寝るのですがの長い反復。','何を書いているのかもしれないの疑問形が崩れ好きですの往復へ。','待合時刻に答えず統計の教科書を自己参照反復。','疲労に応答せず食事の相槌を長く反復。','料理提案に答えず人間にかかる等の不自然句からおいしいの反復。','活動を答えずうん・あの文字反復へ。','近況への返答として主体が合わずAI活用に向けたを反復。','公園の公園という所有句を増殖し行くか否かの往復を反復。'],
('selected','native8'):['健康・歩行の話から何かの時間が多いですかという主述不成立を経て好きなのでを反復。','バイク修復の話からそれはいつも買ってみますと逸れ相槌を長く反復。','挨拶の切替時刻に答えず何かの時間が多い・かかるを反復。','酸っぱい飲料の飲み方を示さずおいしい・今日の話を反復。','気温への相槌は一部成立するが何かの時間が多いから暑いのは暑いのでを長く反復。','女優への好意に続く応答はあなたは・あれはの長い反復。','ストック・メモの話からものを作る話へ逸れどんな感じを長く反復。','私もおいしいは主体・述語が弱く、相槌の長い反復へ。'],
('terminal','native8'):['健康の話から何かの時間が多いですか、好きですを反復し最後は食事へ逸れる。','バイク修復をおいしいと受け、相槌を長く反復。','挨拶の時刻から好きですか・好きですを長く往復。','飲み方を示さずおいしいですよねを長く反復。','暑いという冒頭の相槌は成立するが以後同じ暑いの往復で全文不成立。','女優が好きという相槌は成立するが以後そうなんですねの長い反復。','ストックやメモの話からおいしい・楽しい・あなたはと逸れ同じ往復を反復。','食べたいという最初の接続は許容できるが食べたいですよねを長く反復。'],
('selected','mrmp5'):['驚きの初句は旧モデルと同様の最小会話行為だが相槌4回からおすすめの不明な往復へ崩れる。EOS54でも全文不成立。primaryは長期反復、短い有限往復を許す感度では非loop。','母子の話を展開せず同じ相槌を長く反復。','土産店・ロープウェイの話からあなたは・あれはを反復。','スカイダイビングに続かず何かの事を聞いてみたいを循環。','洗面所の話から毎日の文字列反復へ。'],
('terminal','mrmp5'):['驚きの初句からおおの文字反復へ。','母子の話から子供の所有句を長く再帰。','買物への接続が一部あってもあまり買ってみたい・あなたはの往復と文法の崩れ。','スカイダイビングから何かのことが多いを長く反復。','洗面所の話から毎日の文字列反復へ。']}
for state in ['selected','terminal']:
 completion=[]
 for group,n in [('original17',17),('daily12',12),('native8',8),('mrmp5',5)]:
  gp=E/paths[group]if state=='selected'else D/f'{group}-python.json';assert sha(gp)==expected[state][group];g=read(gp);rows=[]
  reasons=(selected_reasons if state=='selected'else terminal_reasons)if group=='original17'else supp[(state,group)]
  nonloop=({5,6,7,8,11}if state=='selected'else{3,7,8,13})if group=='original17'else({2}if state=='terminal'and group=='daily12'else set())
  meaningful={11}if state=='selected'and group=='original17'else set()
  for i,(r,reason)in enumerate(zip(g['rows'],reasons,strict=True)):
   v=dict(id=r['id'],fullOutputMeaningful=i in meaningful,fullOutputLoop=i not in nonloop,reason=reason,prefixAndTextSha256=digest(r))
   if group=='original17':
    v.update(dict(zip(['grammar','meaning','connection','repetition','breaks','sentenceClosed'],scores[state][i])))
    oldg=read(P/('new-validation.json'if state=='selected'else'terminal-state-diagnostic/original17-python.json'))['rows'][i];oldm=read(P/('new-manual.json'if state=='selected'else'terminal-state-diagnostic/original17-manual.json'))['rows'][i]
    if oldg['text'].split('。')[0]==r['text'].split('。')[0]:
     for k in ['grammar','meaning','connection','repetition','breaks','sentenceClosed']:v[k]=oldm[k]
    if digest(oldg)==digest(r):assert all(v[k]==oldm[k]for k in ['fullOutputMeaningful','fullOutputLoop','grammar','meaning','connection','repetition','breaks','sentenceClosed'])
   else:v['intrusiveRepetition']=True
   rows.append(v)
  mp=E/manualpaths[group]if state=='selected'else D/(f'{group}-manual.json'if group=='original17'else f'{group}-reading.json')
  out=dict(generationSha256=sha(gp),reviewer='Assistant actual complete reading of all84 new state outputs, not independent blind human evaluation',actualRetainedUpdates=10000,selectedStep=8000,evaluatedStep=8000 if state=='selected'else 10000,wholeMeaning=len(meaningful),longLoopsPrimary=n-len(nonloop),eos=sum(r['eos']for r in g['rows']),notNewTest=True,notUsedForSelection=True,rows=rows);out[f'all{n}FullPrefixesAndContinuationsActuallyRead']=True
  if group=='original17':out['meaningPolicySha256']=sha(R.parent/'round10/full-meaning-policy.json')
  if group in ['native8','mrmp5']:out.update(wholeMeaningSensitivityRequiringContentBeyondBackchannels=0,minimalContextCompatibleSpeechActsNotProofOfUnderstanding=True)
  if group=='mrmp5':out.update(independentCastFamilies=1,distinctPublicSpeakerIds=3)
  if state=='selected'and group=='daily12':out['longLoopsSensitivityFiniteTiredNarrative']=11
  if state=='selected'and group=='mrmp5':out['longLoopsSensitivityFiniteShortExchange']=4
  write(mp,out);completion.append(dict(group=group,inputs=n,generationSha256=sha(gp),manualSha256=sha(mp),wholeMeaning=len(meaningful)))
  if group=='original17':subprocess.run(['python',str(R.parent/'round10/review.py'),'--generation',str(gp),'--manual',str(mp),'--out',str(E/'new-review.json'if state=='selected'else D/'original17-review.json')],check=True,stdout=subprocess.DEVNULL)
 write(E/'selected-full-reading-complete.json'if state=='selected'else D/'full-reading-complete.json',dict(actualTrainingUpdates=10000,selectedEvaluatedStep=8000,all42FullPrefixesAndContinuationsActuallyRead=True,groups=completion,notNewTest=True,noCombinedIndependentLanguageSuccessRate=True,strictGatePassed=False))
print('Saved actual84 complete-reading SHA-bound explicit judgments; selected original whole1/nonloop5; terminal whole0/nonloop4; daily0/0; no model or optimizer updates')
