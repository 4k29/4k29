"""Record root's actual complete reading of R46 raw1000 outputs; no semantic classifier."""
import pathlib,json,hashlib,copy
repo=pathlib.Path('/workspace/4k29');B=repo/'training/language';R=B/'round46';E=R/'execution';O=E/'paired-daily-generation-1000';P=B/'round44/execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected='5d97d8162915360e398e5b9c2dc989c423599d156b2c5a2e589cf3a7b2cd191b';assert sha(O/'round46.json')==expected, 'Reading notes are bound to this exact already-read generation'
new=read(O/'round46.json');old=read(O/'round44.json');historical=read(P/'paired-daily-generation-1000/round44.json');oldread=read(P/'paired-daily-generation-1000/round44-reading.json')
bound={x['path']:x for x in read(P/'artifact-manifest.json')['files']}
for rel in ['execution/paired-daily-generation-1000/round44.json','execution/paired-daily-generation-1000/round44-reading.json']:
 p=B/'round44'/rel;assert sha(p)==bound[rel]['sha256']
for a,b in zip(old['rows'],historical['rows'],strict=True):
 for k in ['id','prefix','text','tokens','eos','validUtf8','validTokens','inputTokens']:assert a[k]==b[k],k
assert oldread['generationSha256']==sha(P/'paired-daily-generation-1000/round44.json')
oldread=copy.deepcopy(oldread);oldread['generationSha256']=sha(O/'round44.json');oldread['historicalJudgmentsPreservedExactly']=True;oldread['currentFullReadingAlsoPerformed']=True
(O/'round44-reading.json').write_text(json.dumps(oldread,ensure_ascii=False,indent=2)+'\n')
# These judgments were written only after all 24 full prefix+continuation texts were read by root.
reasons=[
'帰りに行きたいという希望から、相槌を挟んで今日は何か行きたいですかと問い返す。行先省略だけで失格にせず、何か行きたいの結合と独白/対話の接続不足で全文0。短い有限の希望の言い直しで非長期loop、軽い侵入反復。',
'卵とキャベツの残りから夕食は大丈夫ですかへ移る同一全文。過去のprimary0を維持し、普通の食事充足確認として読むwhole1の感度を併記する。非loop。',
'今日は何を予定ですは何をと予定ですの統語が不成立。続くそうなんですかも週末の友人との予定を補えない。有限二文EOS非loop。',
'雨が降り降ってという活用崩れと雨が降っての長い循環。出かける前に何をするかの主述を作れず、192token末尾でも未完。loop。',
'寝るのが寝るので寝るから寝ると寝るを長く循環し、今夜の行動の主述が崩れる。192tokenで未完、loop。',
'どこかへ行くのが行くのが行くのだろうという重複名詞化で主述が崩れ、お互いのお店は何か行きたいでは店が希望する関係になる。趣味の開始からも逸れる。有限の語片stutterと三文EOSでprimary非長期loopだが侵入反復。',
'待ち合わせ時刻の問いへ天気はどのくらいですかと返す同一全文。何の量/時刻への接続かが不明という過去のprimary0/非loopを維持。',
'今日はを三回重ねて何を食べたいかなと返す。食事相談そのものは疲れへの気遣いと読めるが、短い侵入stutterで全文の自然さはprimary0。有限一文EOSで非長期loop。普通の言い淀みならwhole1の別解。',
'卵の料理相談へ自分が作ってるのはいかなと不完全な疑問/終止を返し、相槌の後の今日はいも述部を作らない。22tokenの有限EOSで非loopだが意味の通る料理応答にならない。',
'週末の過ごし方を尋ねられ、今日は何を食べたいですかへ話題を変える。問い自体は文法的だが過去の行動への応答/自然な接続がなくprimary0。短いEOS非loop。',
'近況質問から武蔵野の武蔵野/武蔵野を見るを長く循環し、名詞修飾と見る/作るの関係が崩れる。固有名詞の外部真偽ではなく主述と反復を失敗理由とする。192token未完loop。',
'公園へ行きたいという気持ちは文脈に接続するが、行きたいですねという同一全文を二度そのまま重ねて終わる。R44native3の同じ裸の評価文の二重反復と同じく全文自然さはprimary0、有限二文なので非長期loop/侵入反復。R45の公園を明示する言い直し/行ってみたいから行きたいという異なる二文の希望を合格にした例との境界は曖昧で、普通の口頭の強調ならwhole1を感度として残す。具体策や新情報の欠如だけで落とさない。'
]
loops={3,4,10};intrusive={0,5,7,11};rows=[]
for i,x in enumerate(new['rows']):
 rows.append(dict(id=x['id'],fullOutputMeaningful=False,fullOutputLoop=i in loops,intrusiveRepetition=i in loops|intrusive,reason=reasons[i],prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
record=dict(noteSourceSha256=sha(pathlib.Path(__file__)),generationSha256=sha(O/'round46.json'),actualRetainedUpdates=1000,evaluatedStep=1000,all12FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=0,longLoopsPrimary=3,eos=sum(x['eos']for x in new['rows']),notIndependentBlindHuman=True,notNewTest=True,notUsedForSelection=True,noOutputRepair=True,sensitivities=dict(ordinaryDinnerAdequacyQuestionWhole=1,ordinaryShortTodayStutterAndCaringMealQuestionWhole=1,ordinaryExactRepeatedParkDesireAsSpokenEmphasisWhole=1,allThreeOrdinaryInterpretationsWhole=3,shortInlineVerbStutterAsLoop=4,shortTodayStutterAsLoop=4,bothShortStuttersAsLoop=5),rows=rows)
assert record['eos']==9
(O/'round46-reading.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
h=read(E/'paired-human-dev-1000/complete.json');summary=dict(actualUpdatesEach=1000,all24FullPrefixesAndContinuationsActuallyRead=True,oldReadingVerifiedByFrozenManifestAndRegeneratedCoreIdentity=True,oldWholeMeaning=0,newWholeMeaning=0,oldLongLoopsPrimary=5,newLongLoopsPrimary=3,oldEos=8,newEos=9,humanDevNllControl=h['oldHumanNllPerByte'],humanDevNllNew=h['newHumanNllPerByte'],newHumanNllImproved=False,shorterOutputOrEosNotCountedAsMeaningSuccess=True,ambiguousParkEmpathyAlternativeWhole=1,broadMeaningOrGeneralizationImprovementEstablished=False,trainingConditionUnchangedAfterInterim=True,notNewTest=True,notUsedForSelection=True,rawFp32OnlyNoInterimJavascriptClaim=True,fullTextSha256=sha(O/'FULL_GENERATIONS.md'),oldReadingSha256=sha(O/'round44-reading.json'),newReadingSha256=sha(O/'round46-reading.json'),additionalOptimizerUpdates=0)
(O/'reading-complete.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary))
