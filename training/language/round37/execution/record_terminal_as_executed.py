"""Explicit judgments after all42 terminal prefixes/full outputs actually read."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path('/workspace/4k29/training/language/round37');E=R/'execution';D=E/'terminal-state-diagnostic';P=R.parent/'round36/execution/terminal-state-diagnostic';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected={'original17':'b6361e9f15e398e446cf1fbac292b86d5d3121e843df6292fab5725253425331','daily12':'83d00d8150199fd7ef79df61fad13d3fc0b86b814dcfc242bca79bcd9ef1f51c','native8':'0948273391b3b62d40864327753ad5176d2577e378914da6086d6654c1d28b13','mrmp5':'8758a731a77ed5baa8a55883afdab5ca837ce009dd7a251c574a3944f3d35026'}
reasons={
'original17':[
'初文は自然。おじいちゃんの主格・所有句を長く反復し引用も閉じない。',
'寒さを防ぐために出て来たは従来の創作状況を許す初文9点。後続は夜の所有句とすかにかかるの崩れを長く循環。',
'いまえがいっぱいのがいっぱいのでしたという接続・語結合が崩れる。後続は母の主格・帰属と敬語の活用が崩れ長く反復。未知名そのものが失敗理由ではない。',
'AIのAIの高いシナジーシップという引用内の修飾が不明でprimary失敗。短いEOSの非loop。不透明なプロジェクト固有名と全体を許す既存の弱い解釈では成立も可能。実事業の正確性は認定しない。',
'市場規模の初文は自然。周波数の金額と同じMVNOの複数割合・括弧が崩れ説明にならない。値が変化する有限の数字列としてprimary非長期loop、値だけ変わる同一主体の意味的loopとする感度も保存。',
'同法・法律番号に基づきを長く反復して主節を閉じず、引用も崩れる。旧terminal全文同一の判定を維持。',
'初文を閉じず海洋ごみの所有句・輸出入を長く循環。旧terminal全文同一。',
'機関省略を許す同じ基準で初文9点。警報が警報・予報を発表する主体の循環と同じ防災対応の冗長な並列で全文失敗。有限で変化する警戒説明としてprimary非長期loop。全節で機関省略を許す弱い代替成立は残す。',
'短いEOSだが解析雨量と把握主体・速報版発表状況の関係が弱く、同一旧初文の弱さを維持してprimary不成立。解析雨量を用いてという手段の省略を補う解釈では成立もあり得る。後続の解説参照は自然で非loop。',
'初文からSVGプロパティの目的語を重複し、値と指定条件を長く循環。',
'初文のグローバル属性を定義するは言語として成立。要素を指定された要素に適用する同一節をEOS153まで長く反復して説明にならない。',
'初文のメソッドが別メソッドを返す文は成立し未知名/API真偽とは別。後続は配列の配列を返す等の短文を長く反復。',
'初文SVGリクエストを提供するSVGリクエストを提供しますの二重再帰で対象関係が弱く7点。以後送信する際とSVGリクエストの同語句を長く循環。',
'提供する方法を提供する際にデータを提供する際に提供するという再帰で何を説明するか不明。短い25tokensのEOSでprimary非長期loop。旧terminal全文同一。',
'統計調査を実施しを長く反復し初文の主節を閉じず、その結果を調査しの循環に移る。',
'表彰の施策を開催という目的語と述語が不自然。旧と大部分同じ法定型を反復する本文でprimaryloopを維持。変化する有限の政策列とみる非loop代替を保存するが全文意味は不成立。',
'施策を講じられていますは受動の目的格が不自然で同一初文7点。後続は文化観光推進法に基づきと推進計画の再帰を長く循環。'],
'daily12':[
'帰りに行ったらしかったの後、いつものの事を書いてと書物を書いてを長く循環し文意が崩れる。',
'冷蔵庫の卵とキャベツが残っていたため夕食は大丈夫だったという自然な一文でEOS。食事を用意できるという日常的な省略が文脈と自然につながりprimary全文成立。具体的な料理提案や広い対話理解の実証ではない。',
'友人との予定から日々の日が暮らしを守るという不成立へ進み、地震注意へ話題が飛ぶ。旧terminalの同型と同様、有限で変化する防災情報としてprimary非長期loop、強い意味反復の感度ではloop。',
'雨の行為を継がず降りの文字反復から雨が降っている場合の長い周期へ崩壊。',
'寝るのが寝るのかなから寝ると寝る・寝るを長く反復。',
'まずは何を書いているのかもしれないのでしょうかは疑問と可能性の接続が崩れ行為を自然に継がない。短いEOS。',
'待ち合わせ時刻を返さず何を食べる・食べたいという引用を長く循環。',
'疲れの話から今日は日曜日に暮らしていたのでを5回ほど繰り返し日曜日の所有句・外出節を長く再帰。',
'料理相談に自分は人間にかかるかと不明な問いを返し、いつもりでしたが等の活用・接続が崩れる。61tokensで有限の変化する節としてprimary非長期loop、局所反復は残す。',
'週末の出来事を返さずうんの引用からああ・あの文字列へ長く循環。',
'近況への応答にAIの社会社の社会実現という修飾が弱い第三者の期待説明へ逸れる。架空組織名だけを失敗理由にせず、話者の近況との接続不足で不成立。有限で非長期loop。',
'雨のため公園予定をどうするかに公園のを6回ほど再帰し、公園と共に行くという係りも不自然。EOS26tokensでも所有句の長い内部loop。'],
'native8':[
'歩く健康効果を受けた後に私も今日は何かの時間が多いですかという不明な自己への問いへ逸れる。selectedと同一全文判定。',
'バイクを復元して乗る話においしいですと返し、食べる対象を文脈から補えず意味が飛ぶ。短いEOSでも不成立。',
'挨拶の切替時刻の話から今日は何かお好きなんですかと好みの問いへ逸れ、自然な接続が弱い。',
'酸味を美味しく飲む方法においしいですねと相槌を6回ほど同じ周期で反復。EOS90でも長期loopで不成立。',
'暑さへの局所的なつながりはあるが、暑いですねと相槌を192tokensまで長く循環。',
'女優の演技・容姿への好意に私も好きです！と共有しEOS。actual1000で同一prefix・全文を成立とした基準を維持。省略対象は直前の女優への好意で自然だが、実在の知識や経験は認定せず、指示対象を明示する厳しい感度では不成立。',
'相手が収納物のメモを述べた直後にあなたは？だけでは再質問の対象が弱くprimary不成立。何をストックするかを問う省略として読む弱い代替は可能だが明示されない。',
'パスタへの味の同意からおいしいですよねという相槌を長く循環。'],
'mrmp5':[
'香りの話への驚きからおおを4回ほど繰り返し、お願いしますという対象のない依頼へ逸れて全文不成立。23tokensの有限反応としてprimary非長期loop、広い反復基準ではloop。',
'赤ちゃん連れに癒される話から子供の所有句を2つの長い鎖で再帰し、おさまにしておりますうちに等の接続も崩れる。EOS90でもloop。',
'ロープウェイと土産店の話に今日はお話ししますかと会話行為自体を問うのみで自然につながらない。',
'スカイダイビングの希望へ今日は何かのことが多いですかという不明な問いを返す。',
'洗面所問題を継がず今日は毎日を長く反復。selectedと同一全文判定。']}
meaning={'original17':set(),'daily12':{1},'native8':{5},'mrmp5':set()};nonloop={'original17':{3,4,7,8,13},'daily12':{1,2,5,8,10},'native8':{0,1,2,5,6},'mrmp5':{0,2,3}}
completion=[]
for group,n in [('original17',17),('daily12',12),('native8',8),('mrmp5',5)]:
 gp=D/f'{group}-python.json';assert sha(gp)==expected[group];g=read(gp);assert len(g['rows'])==n;rows=[]
 for i,(x,reason)in enumerate(zip(g['rows'],reasons[group],strict=True)):
  h=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();j=dict(id=x['id'],fullOutputMeaningful=i in meaning[group],fullOutputLoop=i not in nonloop[group],reason=reason,prefixAndTextSha256=h)
  if group=='original17':
   oldg=read(P/'original17-python.json')['rows'][i];oldm=read(P/'original17-manual.json')['rows'][i];keys=['grammar','meaning','connection','repetition','breaks','sentenceClosed'];j.update({k:oldm[k]for k in keys})
   changes={2:(0,0,1,1,0,True),3:(2,1,2,1,1,True),4:(2,2,2,2,2,True),12:(2,1,2,1,1,True),14:(0,0,1,0,0,False)}
   if i in changes:j.update(dict(zip(keys,changes[i])))
   if x['text'].split('。')[0]==oldg['text'].split('。')[0]:assert all(j[k]==oldm[k]for k in keys)
   if x['prefix']==oldg['prefix']and x['text']==oldg['text']:assert all(j[k]==oldm[k]for k in keys+['fullOutputMeaningful','fullOutputLoop'])
  else:j['intrusiveRepetition']=j['fullOutputLoop']or(group=='daily12'and i in [2,8])or(group=='mrmp5'and i==0)
  rows.append(j)
 mp=D/(f'{group}-manual.json'if group=='original17'else f'{group}-reading.json');out=dict(generationSha256=sha(gp),reviewer='Assistant actual complete reading of all42 terminal full outputs, not independent blind human evaluation',actualRetainedUpdates=10000,selectedStep=8000,evaluatedStep=10000,wholeMeaning=len(meaning[group]),longLoopsPrimary=n-len(nonloop[group]),eos=sum(x['eos']for x in g['rows']),notNewTest=True,notUsedForSelection=True,rows=rows);out[f'all{n}FullPrefixesAndContinuationsActuallyRead']=True
 if group=='original17':out.update(meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),nonloopSensitivityCountingNumericMvnoListAsLoop=4,nonloopSensitivityPermittingFiniteCulturalPolicyList=6,wholeMeaningSensitivityOpaqueProjectName=1,wholeMeaningSensitivityToolTopicOmission=1,wholeMeaningSensitivityOmittedWarningAgency=1,wholeMeaningSensitivityAllThreeWeakReadings=3)
 if group=='daily12':out.update(longLoopsSensitivityCountingFiniteEarthquakeNarrative=8,shortContextualProseSuccessId='daily-prose-dinner',notEvidenceOfRecipeOrBroadDialogueAbility=True)
 if group=='native8':out.update(wholeMeaningSensitivityRequiringContentBeyondBackchannels=1,wholeMeaningSensitivityRequiringExplicitReferentsAndContent=0,wholeMeaningSensitivityPermittingEllipticalYouQuestion=2,minimalContextCompatibleSpeechActsNotProofOfUnderstanding=True)
 if group=='mrmp5':out.update(independentCastFamilies=1,distinctPublicSpeakerIds=3,longLoopsSensitivityCountingShortExclamationRepeat=3,wholeMeaningSensitivityRequiringContentBeyondBackchannels=0)
 mp.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');completion.append(dict(group=group,inputs=n,generationSha256=sha(gp),manualSha256=sha(mp),wholeMeaning=len(meaning[group])))
 if group=='original17':subprocess.run(['python',str(R.parent/'round10/review.py'),'--generation',str(gp),'--manual',str(mp),'--out',str(D/'original17-review.json')],check=True,stdout=subprocess.DEVNULL)
(D/'full-reading-complete.json').write_text(json.dumps(dict(actualTrainingUpdates=10000,selectedEvaluatedStep=8000,terminalEvaluatedStep=10000,all42FullPrefixesAndContinuationsActuallyRead=True,groups=completion,notNewTest=True,noCombinedIndependentLanguageSuccessRate=True,strictGatePassed=False),indent=2)+'\n');print(json.dumps(dict(actualNewStateOutputsRead=84,terminalOriginal=dict(first=read(D/'original17-review.json')['passed'],nonloop=5,whole=0),terminalDailyWhole=1,terminalNativeMinimal=1,terminalSourceWhole=0)))
