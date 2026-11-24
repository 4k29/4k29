"""Explicit judgments after actually reading all42 terminal full continuations."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=[
'初文したは自然。以後おい・おじいちゃん・おじさんの呼称と所有句を長く反復し引用・述語が崩れる。',
'同じ防寒のため出て来たという弱い初文はselectedと同じ8点。夜の所有句とがすかにかかすか等へ長く崩れる。',
'葦の擬人化来訪の同じ自然な初文。おもしろいろ・もう一度もあったがの活用から母の所有句とおの文字へ長く反復。',
'初期の引用が閉じずAIのAIの高度化という修飾からform・Internationを長く循環し、294年に比べて等の数値へ崩れる。',
'市場規模の初文は自然。種類の種類を各段落で何度も反復し、種類が有するもの等の主述が崩れる。EOS137tokensでも長い所有句loop。',
'同法に基づきの反復、適正な管理8回以上の列から法律・計画の定義と引用・括弧が崩れ、全文・初文とも不成立。',
'海岸法の目標から海域の所有句、海域で発生する同一節を長く反復し、海溝沿いの地震周期へ話題が崩れる。初文も開かない引用の閉じを含む。',
'住民等の避難をとるべきという初文の係り・動作が不自然。以後レベルを付す・発表する同一節が繰り返され、主体も警報とレベルを循環する。',
'selectedとprefix/text全文同一。解析雨量と把握主体・速報版状況の関係が弱い同じ6点でprimary全文失敗。短い解説参照は非loop。手段省略を補う弱い全文成立代替は共通に残す。',
'CSSパスを返す初文は言語として自然で事実は認定しない。CSSパスのパスを返すという同一節を長く反復し146tokensのEOSでも全文は崩れる。',
'要素がグローバル属性を指定する初文は技術文の同じ主題許容で成立。要素を指定された要素に設定する自己参照が192tokens続く。',
'IDBKeyRangeのメソッドがInterオブジェクトのメソッドを返すという単文でEOS。関数を返す言語は成立し未知名だけでは不成立にしないR37基準を維持する。実APIの真偽は認定せず不透明名を厳格に扱う代替では不成立。',
'ポリシーを使用してJavaScriptで使うURLを返す初文は言語として成立。以後URLのURLオブジェクト、オブジェクトのオブジェクトの再帰と未導入メソッドの指示へ崩れる。有限3文53tokensをprimary非長期loop、再帰を広くloopとする感度も保存。',
'CookieがCookieで提供するという初文から主述と修飾が自己参照し、Cookieファイルを提供する同一節を長く反復。',
'統計分析を客観的手段として行える初文は各分析が曖昧な分9点。以後統計データの分析やを長く反復。',
'表現件・開催の係りが不明な初文からアジア8回と国際連邦共和国の所有句を反復。架空の国名自体で失格にはしないが、日ASEAN会合の修飾も再帰し引用を閉じない。',
'selectedと同じ講じられていますのを・受身の関係が弱い初文7点。文化観光推進事業計画に基づき・設置という同一語列を長く反復。']
scores=[[2,2,2,2,2,True],[2,1,1,2,2,True],[2,2,2,2,2,True],[0,0,1,0,0,False],[2,2,2,2,2,True],[0,0,1,0,0,False],[0,0,1,0,0,False],[1,0,1,2,1,True],[1,1,1,2,1,True],[2,2,2,2,2,True],[2,2,2,2,2,True],[2,2,2,2,2,True],[2,2,2,2,2,True],[1,0,1,0,0,True],[2,1,2,2,2,True],[1,0,1,0,0,True],[1,1,2,2,1,True]]
daily=[
'帰りの行為を継がず行くのが出来るのが一番と思い出すの係りから母の所有句へ長く反復。',
'材料が残ったので夕食は何か食べたかもしれないですかという過去可能性の問いは主体・因果が不明で、自然な夕食の継続が成立しない。短いEOS非loop。',
'友人と会う予定の話を今日は201週間以上に行われていますと継ぎ、主語・期間・時制が崩れる。短いEOS非loop。',
'出かける前の行動を継がず雨が降ってを192tokens反復し切断。',
'寝るのが寝るのかなと思うという初文から寝ると寝るの長いloopへ崩れる。',
'新しい趣味を始めるためまずは何かのことが多いのでしょうかでは何が多いかも行動も不明。短いEOS非loop。',
'待ち合わせ時刻の問いに天井・おいしいという無関係な引用を導き、私は・あの人にはを長く反復し引用も閉じない。',
'友人の疲れへの応答を友人は今日は4回・昼食希望へ転じ、何を述べるのかと話者が崩れる。51tokensの有限2文を旧R37疲労例と同様primary非長期loopとし、広い反復基準のloop感度を残す。',
'料理の提案を返さず自分はいやいという不明な引用が多いのか尋ねる。短いEOS非loop。',
'selectedとprefix/text全文同一。週末の行動を答えずおいしそうですかという言葉が思い出されるという受身の記憶へ逸れる同じprimary不成立。',
'近況の問いをAIが使う映画の種類の問いへ転じ、使う対象と話者・近況の関係が不明。架空AI自体を失格理由とはしない。短いEOS非loop。',
'公園の公園の公園という3回の局所所有句と既定予定の再質問で全文不成立。15tokensで終了しselectedの5回/旧terminal6回の所有句loopより短いためprimary侵入反復・非長期loop、3回でもloopとする広い感度も残す。']
native=[
'歩く健康効果の共有にそうなんですね！と自然に受け止める最小の相槌で成立。新しい内容・明示的参照はない。',
'selectedと同じバイクの説明へのそうですね！という最小の自然な相槌。',
'挨拶時刻の境界の話へ今日は何かの時間がかかるかと尋ね、何の所要時間かが不明。短いEOS非loop。',
'酸っぱい飲料をおいしく飲む方法探しにおいしそう・おいしいを3回重ね、今はいという語接続の崩れで終わる。29tokensの有限列をprimary非長期loop・侵入反復、広い反復基準ではloopとする感度を残す。',
'selectedとprefix/text同一。暑くて外出を避ける説明への今日は何かのことですかは指示が不明でprimary不成立、短いEOS非loop。',
'相手が既に女優の好みを説明した後であなたは？だけを再質問し、問いの対象が不明で従来同様primary不成立。追加の好みを尋ねる省略の弱い代替のみ保存。',
'積み上がるストックとメモの話をおすすめ映画かという問いへ転じ、今日はとの関係も不明。短いEOSで映画の問い自体は統語的でも文脈失敗。',
'selectedとprefix/text同一。パスタが食べたいという共有へのそうですね、おいしいですねはパスタを暗黙主題にした自然な最小の味の共感。新情報や明示的文脈語はない。']
source=[
'ポップコーンの香りと仕事の話にあなたはおすすめ、あなたは何かあってもおいしいかと返し、人物を美味とする主述や条件が文脈につながらない。短い有限2文非loop。',
'母親・子どもの所有句を8回ほど繰り返し、子を買っておくことが多いという行為へ崩れる。短いEOSでも長い所有句loop。',
'selectedの句読点違いのそうですね、あとは？と同じ意味。追加で何を聞くかが曖昧で従来primary不成立。追加の場所を尋ねる省略を許す弱い代替は保存。',
'スカイダイビングを一度したいと既に述べた相手にあなたは何かありますかと尋ね、何を追加で問うかが不明でprimary不成立。ほかに人生で一度したいことと補う広い代替では最小行為成立。出力は補わない。',
'洗面所の話を今日はの局所重複から毎日を192tokens反復し述語が成立しない。']
specs=[('original17','7faa1d1f3d4548ae054aa46d50b5314b9b44610a1f5dd30bcbeff793fba146f5',original,{11},{8,11,12},'original17-manual.json'),('daily12','9387ab398ca7ea471d392f51d30dc7920529e431db8eeff94b8864edc2e35275',daily,set(),{1,2,5,7,8,9,10,11},'daily12-reading.json'),('native8','7de671fd219e80d8b4320345c67df6775dbcc5d8b2e7533168696ef9d013ef9e',native,{0,1,7},set(range(8)),'native8-reading.json'),('mrmp5','9d6a6ba11817fa09205ff58b858b22e88dabde10dbd162dee2c054edcd398635',source,set(),{0,2,3},'mrmp5-reading.json')]
for group,expected,reasons,meaning,nonloop,mp in specs:
 p=D/f'{group}-python.json';assert sha(p)==expected;g=read(p);assert len(g['rows'])==len(reasons);rows=[]
 for i,(x,reason)in enumerate(zip(g['rows'],reasons,strict=True)):
  j=dict(id=x['id'],fullOutputMeaningful=i in meaning,fullOutputLoop=i not in nonloop,intrusiveRepetition=i not in nonloop or (group=='original17'and i==12)or(group=='daily12'and i in {7,11})or(group=='native8'and i==3),reason=reason,prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
  if group=='original17':j.update(dict(zip(['grammar','meaning','connection','repetition','breaks','sentenceClosed'],scores[i],strict=True)),firstSentenceScoreProvenance='Actual complete terminal first sentence and full continuation read under unchanged rubric; selected identical spans keep scores')
  if group in ['native8','mrmp5']:j.update(contentBeyondBackchannel=group=='native8'and i==7,explicitContextObjectReference=False,newInformation=False)
  rows.append(j)
 out=dict(generationSha256=sha(p),reviewer='Assistant actual complete terminal reading, not independent blind human evaluation',actualRetainedUpdates=10000,selectedStep=9500,evaluatedStep=10000,notNewTest=True,notUsedForSelection=True,wholeMeaning=len(meaning),longLoopsPrimary=len(rows)-len(nonloop),eos=sum(x['eos']for x in g['rows']),rows=rows)
 out[f'all{len(rows)}FullPrefixesAndContinuationsActuallyRead']=True
 if group=='original17':out.update(meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),opaqueNameStrictWholeAlternative=0,wholeMeaningSensitivityPermittingInstrumentEllipsis=2,nonloopSensitivityCountingShortUrlRecursionAsLoop=2,firstSentenceSensitivityPermittingColdEscapeAndPassiveHonorific=10)
 if group=='daily12':out.update(longLoopsSensitivityIncludingShortParkRecursion=5,longLoopsSensitivityIncludingFiniteFatigue=5,longLoopsSensitivityIncludingBoth=6)
 if group=='native8':out.update(contentBeyondBackchannel=1,explicitContextObjectReferences=0,newInformationResponses=0,wholeMeaningSensitivityPermittingVagueActressQuestion=4,longLoopsSensitivityIncludingShortTasteRepetition=1)
 if group=='mrmp5':out.update(contentBeyondBackchannel=0,explicitContextObjectReferences=0,wholeMeaningSensitivityPermittingEitherWeakQuestion=1,wholeMeaningSensitivityPermittingBothWeakQuestions=2,independentSpeakerCombinationFamilies=1,distinctPublicSpeakerIds=3,notIndependentFiveSpeakers=True)
 (D/mp).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 if group=='original17':subprocess.run(['python',str(R.parent/'round10/review.py'),'--generation',str(p),'--manual',str(D/mp),'--out',str(D/'original17-review.json')],check=True)
 print(json.dumps(dict(group=group,wholeMeaning=len(meaning),longLoops=len(rows)-len(nonloop),eos=out['eos'])))
