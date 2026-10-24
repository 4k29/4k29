"""SHA-bound terminal full reading records for these12+8+5 outputs only."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=[('daily12','4a560a0404d92a9f5b22eb1715cc238614a4981a60d1cff9eea585c5e1a71160',12,set(),{2,3,4,5,7,9,11},{0,2,3,4,5,6,7,9,11}),('native8','442c633567da7e60531b540dc2c3405ef4a4b4a1fbb6f04c5e39ecf884238114',8,{5,7},{0,3,6},{0,3,6}),('mrmp5','d3b45dc385d3dbc5bacc75fa1743b1e6751ba720aae7a8f432122d37ce549ffa',5,set(),{1,4},{1,4})]
notes={
'daily12':[
'帰りに行くのが行くのは何かの事だと思いますかという主述・行為の弱い問いになり、早く仕事が終わった後の自然な継続にならない。有限18tokensEOS非長期loop、侵入反復。',
'夕食は何か食べたいですかは質問単体なら文法として成立するが、残り物を理由とする自己の食事の流れから未提示の他者へ質問する接続が弱くprimarywhole0。通常の話者・宛先省略を広く補えばwhole1となる感度を別記し、不自然な文法と一律にはしない。',
'会う日・日曜日の所有句から曜日の文字を192tokens反復し、友人との予定・話題が進展しない。',
'雨が降るのはず・降り降りてください等と語順・活用が崩れ、雨の同じ句を192tokens反復する。',
'寝るのが寝るのかなから寝ると寝る・寝るを192tokens反復し、今夜の自然な方針に接続しない。',
'行くのが、その後、おもしろいを多数連打し、お母様の所有句の長い反復へ崩れる。',
'待ち合わせの時刻に天気の毒が出るのか、天気の人には等を返し、語結合と話題が成立しない。41tokensの有限EOSでprimary非長期loopだが侵入反復。広いloop感度は別記。',
'疲れへの応答がなく、天井の友人・今日等からその日の日の所有句を長く反復し192tokensで切れる。',
'卵の調理に対し自分は何かの時間にかかわいと活用・関係が崩れ、自分で作るのは大変という一般論と今日いつも作るのが好きですかという問いへ逸れる。有限44tokens非長期loop。',
'週末の体験に答えず、おいしそう等の引用の後、そうかを20回以上重ね、僕は僕はへ崩れる。192tokensloop。',
'近況への応答がなく、おいしいと言うという突然の引用・行為になる。短い11tokensEOS非loop。',
'公園の公園の所有句を長く連打し、行くのが行かないと活用・否定が崩れ、公園整備という別の行政説明へ逸れる。100tokensEOSでもprimaryloop。'],
'native8':[
'歩行の健康の話に私もお好きなので・好きなのでという相槌を4回ほど重ね、最後は私も好きなんですかと自己への問いになる。58tokens有限EOSでもprimaryloop。有限相槌連打として非loopに寄せる感度も保持。',
'バイクの説明へのおいしいですは味覚へ話題が逸れ、自然な同意として成立しない。短いEOS。',
'挨拶の切替時刻の話に今日は何かお好きですかという対象・話者の不明な質問を返す。短いEOS非loop。',
'酸っぱい飲料を美味しく飲む方法を継がず、おいしいですね・おいしいですよねを182tokens反復する。EOSでもprimaryloop。',
'暑さと外出回避に今日は何かのことですかという対象不明の問いを返す。selected同一prefix/全文と同じprimary失敗。',
'女優の芝居・容姿が好きという発話への私も好きですという自然な共有の好み。selected同一全文と同じ最小の意味成立。対象名・新情報はない。',
'積層とメモの話からお米・お前はおいしいへ逸れ、同じ味覚の相槌を192tokens反復して切れる。',
'パスタがおいしいという直前発話へのおいしいですねという自然な味の同意。selected同一全文と同じ意味成立。対象名や新情報はない。'],
'mrmp5':[
'仕事内容とポップコーンの香りの話から何を勧めるか不明なおすすめですかへ移る。selected・R39同一全文と同じprimary失敗。弱い未提示の食べ物推奨という代替は感度のみ。',
'お母さんの子供の所有句から子供子・子の文字を192tokens反復し、主述・会話の意味が崩れる。',
'土産店とロープウェイの話にあとはと返すが、追加で何を尋ねるか曖昧でprimary不成立。R39terminal同一全文と同じ判定。追加の場所を尋ねる省略を広く補う弱い自然な代替は保持。',
'スカイダイビングを一度したいという希望にあなたは何かあったんですかと未提示の過去事象を尋ね、primaryでは文脈接続が弱い。希望のきっかけを尋ねる普通の省略と読む自然な代替はwhole1として別記し、文法が壊れているとはしない。',
'洗面所の問題への相槌の後、今日は毎日を192tokens反復して述語が閉じない。selected・R39同一全文と同じloop。']}
for name,wanted,n,whole,loops,intrusive in spec:
 gp=D/f'{name}-python.json';assert sha(gp)==wanted;g=read(gp);assert len(g['rows'])==n;rows=[]
 for i,x in enumerate(g['rows']):rows.append(dict(id=x['id'],fullOutputMeaningful=i in whole,fullOutputLoop=i in loops,intrusiveRepetition=i in intrusive,contentBeyondBackchannel=(name=='native8' and i in {5,7}),explicitContextObjectReference=False,newInformation=False,reason=notes[name][i],prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
 report=dict(generationSha256=sha(gp),reviewer='Assistant actual complete reading of every terminal prefix and continuation; not independent blind human',actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=10000,wholeMeaning=len(whole),longLoopsPrimary=len(loops),eos=sum(x['eos'] for x in g['rows']),notNewTest=True,notUsedForSelection=True,contentBeyondBackchannel=sum(x['contentBeyondBackchannel'] for x in rows),explicitContextObjectReferences=0,newInformationResponses=0,rows=rows)
 report[f'all{n}FullPrefixesAndContinuationsActuallyRead']=True
 if name=='daily12':report.update(wholeMeaningSensitivityPermittingUnstatedOtherPersonDinnerQuestion=1,longLoopsSensitivityIncludingFiniteWeatherPeopleRepetition=8)
 elif name=='native8':report.update(minimalAcknowledgmentsOrOpinionActs=2,longLoopsSensitivityTreatingFiniteWalkingBackchannelAsNonloop=2)
 else:report.update(wholeMeaningSensitivityAllowingUnstatedRecommendation=1,wholeMeaningSensitivityAllowingAdditionalPlaceQuestion=1,wholeMeaningSensitivityAllowingImpliedMotivationQuestion=1,wholeMeaningSensitivityAllowingAllThreeWeakQuestions=3,independentSpeakerCombinationFamilies=1,distinctPublicSpeakerIds=3,notIndependentFiveSpeakers=True)
 (D/f'{name}-reading.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(name,'whole',len(whole),'loops',len(loops),'EOS',report['eos'])
