"""SHA-bound historical actual1000 reading only; NOT a future grader."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';O=E/'paired-daily-generation-1000';P=R.parent/'round40';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());assert sha(O/'round40.json')=='0fbb6a33d3864e2f8b0ec7ea012490e8a0a430ec17d808f96f6ad9b17d329fd6' and sha(O/'round41.json')=='fbe8722510537f1f2919cd32247d0efa81db1a19bfc7580ff7d327b4f2d5f4a4';a=read(O/'round40.json');b=read(O/'round41.json');hist=P/'execution/paired-daily-generation-1000';prior=read(hist/'round40.json');pm=read(hist/'round40-reading.json');bound={r['path']:r for r in read(P/'execution/artifact-manifest.json')['files']}
for p in [hist/'round40.json',hist/'round40-reading.json']:assert sha(p)==bound[str(p.relative_to(P))]['sha256']
assert pm['generationSha256']==sha(hist/'round40.json');core=['id','prefix','text','tokens','eos','validUtf8','validTokens','inputTokens']
for x,y in zip(a['rows'],prior['rows'],strict=True):assert all(x[k]==y[k]for k in core)
old=dict(pm,generationSha256=sha(O/'round40.json'),priorGenerationSha256=sha(hist/'round40.json'),priorReadingSha256=sha(hist/'round40-reading.json'),sameRawCoresAsHistorical=True,oldReadingProvenance='Actual R40 reading reused after manifest and exact raw-core verification; not a new blind reading')
changed={
2:(False,True,'友達と会う予定から、日常生活における/にあるを重ねた不成立な一般説明へ逸れる。意味しています・期待するためには・お知らせするの主述と因果がつながらない。90tokens有限EOSは旧73tokensの同種説明と同じprimary非長期loopだが、強い侵入反復。広いloop解釈では1件追加する。'),
3:(True,True,'雨が降ると雨が降ってきますの同語循環から、降り降り・雲が降る・不成立な降水量の述語を192tokens反復して切れる。外出準備を継げない。'),
7:(False,True,'今日はを四度連ねて何を食べたいかと質問し、仕事の疲れへの自然な接続を示さない。20tokens有限EOSで旧83tokensの長い停滞連打は短縮した。primaryでは短い侵入反復を長期loopと分け、広いloop感度では1件追加する。'),
9:(False,False,'週末の体験を答えず、おいしそうですかという言葉は何か言われるのでしょうかという対象と述語の弱いメタ質問へ逸れる。23tokens有限EOSで、旧87tokensの日曜日の入れ子反復はないが意味の自然さは未成立。'),
10:(False,False,'近況への応答がAIがおいしくお米が多いかもしれないのでしょうかとなり、主語の連結と副詞・述語の意味関係が成立しない。22tokens有限EOS非loop。'),
11:(False,False,'既に公園に行く予定と雨で迷うことを聞いた後、公園とか行くのですかと予定を再質問する。primaryでは前発話への自然な接続が弱くwhole0。予定通り今も行くかの省略された確認質問と読むなら短い自然な返答whole1であり、その代替を残す。10tokensEOS非loop。')}
rows=[];same=0
for i,(x,y,z) in enumerate(zip(a['rows'],b['rows'],pm['rows'],strict=True)):
 exact=all(x[k]==y[k]for k in core)
 if exact:r=dict(z,exactOldCurrentRawCore=True);same+=1
 else:
  loop,intrusive,reason=changed[i];r=dict(id=y['id'],fullOutputMeaningful=False,fullOutputLoop=loop,intrusiveRepetition=intrusive,reason=reason,exactOldCurrentRawCore=False)
 assert y['validUtf8']and y['validTokens'];r['prefixAndTextSha256']=hashlib.sha256(json.dumps(dict(prefix=y['prefix'],text=y['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();rows.append(r)
new=dict(generationSha256=sha(O/'round41.json'),actualEvaluatedUpdates=1000,all12FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=sum(r['fullOutputMeaningful']for r in rows),longLoopsPrimary=sum(r['fullOutputLoop']for r in rows),eos=sum(r['eos']for r in b['rows']),notIndependentBlindHuman=True,notNewTest=True,notUsedForSelection=True,final10000AssessmentStillPending=True,rawFp32PythonOnly=True,wholeMeaningSensitivityAllowingParkDecisionConfirmation=1,loopSensitivityAlsoCountingFiniteProseWeekendAndShortTodayStutter=4,rows=rows)
assert same==6 and new['wholeMeaning']==0 and new['longLoopsPrimary']==2 and new['eos']==10
for n,x in [('round40-reading.json',old),('round41-reading.json',new)]:(O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
report=dict(actualUpdatesEach=1000,all12NewFullPrefixesAndContinuationsActuallyRead=True,old12ReadingVerifiedByExactCoreAndManifest=True,all24OutputsCoveredByActualReadingOrVerifiedHistory=True,identicalRawCorePairs=same,oldWholeMeaning=0,newWholeMeaning=0,oldLongLoopsPrimary=4,newLongLoopsPrimary=2,oldEos=10,newEos=10,meaningImprovementEstablished=False,interpretation='Human DEV99 and TRAIN64 correct-context NLL improve while common DEV slightly worsens; some primary loops shorten, but all12 full continuations fail primary meaning. Context gain decreases because mismatched NLL also improves. Not proof of context understanding or final success.',sensitivities={'parkDecisionConfirmation':'new whole1 if unstated still/planned confirmation is accepted; primary0 and no strict gate relaxation','sameDinnerQuestion':'weak alternative whole1 in both identical texts','broaderFiniteWeekendAndTodayLoops':'new loops4 instead of2; shortness alone is not a semantic improvement'},notNewTest=True,notUsedForSelection=True,publicModelChanged=False,additionalOptimizerUpdates=0,fullTextSha256=sha(O/'FULL_GENERATIONS.md'),newReadingSha256=sha(O/'round41-reading.json'),oldReadingSha256=sha(O/'round40-reading.json'))
(O/'reading-complete.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
