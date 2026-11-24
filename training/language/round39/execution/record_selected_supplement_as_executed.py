"""Explicit full-read native/source selected judgments, never a future-model grader."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
native=[
'歩く健康の話への相槌は自然だが私もお好きですかという自分への好意確認・話者と対象の関係は歩行の話題につながらない。短いEOS非loop。',
'バイクの保管・レストアの説明へのそうですねという自然な最小相槌。具体的な対象への新情報はない。',
'挨拶の切替時刻の話にそれはどうしてもおいしいを何度も返し115tokens反復。EOSでも話題不成立のloop。',
'酸っぱい飲料を飲む方法の話においしいですね等の同じ相槌を8回ほど重ね73tokensで閉じる。primaryloopで全文不成立。EOSだけで非loopにしない。',
'暑さと外出回避への相槌の後、今日は何かのことですかという対象・主題の不明な問いになり接続が成立しない。短いEOS非loop。',
'女優の芝居・容姿が好きという発話への私も好きですという自然な共有の好み。普通の対象省略を認める最小の意味成立。実在人物の事実やモデルの実在嗜好は認定しない。対象名の明示・新情報はない。',
'積み重ねとメモについて既に説明された後、それはどんなことですかと問う対象・どの点を尋ねるかが曖昧でprimary接続不十分。ストックの層という呼称の具体化要求と読む弱い自然な代替は認め感度4件で別記。単に新情報がないことだけを失敗理由にはしない。',
'パスタがおいしいという直前発話へのおいしいですねという自然な同意・味の意見。具体的対象名や新情報はない。']
source=[
'仕事の内容と帰宅時のポップコーンの香りの話におすすめですかと返すが、何を勧めるかが提示されず主題が不明。短いEOS非loop。ポップコーン等への勧め確認を許す弱い代替のみ感度へ保存。',
'母親の子供の子供の子供という世代所有句を二つの有限の主語・目的語に重ね、子をお出でになってと述語の項・活用も崩れる。41tokensの一文EOSでprimary非長期loopだが強い侵入反復。二つの三段所有句をloopと数える広い代替は2loopsで保存し、意味成立とはしない。',
'土産店とロープウェイの話にあなたはお話しますかと問い、話す対象と文脈がつながらない。短いEOS非loop。',
'スカイダイビングを一度したいという発話にあなたは何かのことですかという不成立な主述を返す。短いEOS非loop。',
'洗面所の問題の話から今日は毎日を192tokens反復し述語も閉じない。']
specs=[('native8','content-native-dev/new-python.json','9d777ee9b0bb7fc47e5fb20975cceb87014e5a37af57f9c39b043201b91855d1',native,{1,5,7},{2,3},{5,7}),('mrmp5','fixed-source-mrmp-dev/new-python.json','603bed001f478ff74a020ff7cbcccdd735cb4b9ebfeba5dc613743842424cf4c',source,set(),{4},set())]
for group,path,expected,reasons,meaning,loops,content in specs:
 p=E/path;assert sha(p)==expected;g=read(p);rows=[]
 for i,(x,reason)in enumerate(zip(g['rows'],reasons,strict=True)):
  rows.append(dict(id=x['id'],fullOutputMeaningful=i in meaning,fullOutputLoop=i in loops,intrusiveRepetition=i in loops or(group=='mrmp5'and i==1),contentBeyondBackchannel=i in content,explicitContextObjectReference=False,newInformation=False,reason=reason,prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
 a=dict(generationSha256=sha(p),reviewer='Assistant actual complete reading of every selected full prefix and continuation, not independent blind human',actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=9000,wholeMeaning=len(meaning),contentBeyondBackchannel=len(content),explicitContextObjectReferences=0,newInformationResponses=0,longLoopsPrimary=len(loops),eos=sum(x['eos']for x in g['rows']),notNewTest=True,notUsedForSelection=True,rows=rows);a[f'all{len(rows)}FullPrefixesAndContinuationsActuallyRead']=True
 if group=='native8':a.update(wholeMeaningSensitivityAllowingVagueClarification=4,minimalAcknowledgmentsOrOpinionActs=3)
 else:a.update(wholeMeaningSensitivityAllowingUnstatedRecommendation=1,longLoopsSensitivityIncludingFiniteFamilyRecursion=2,independentSpeakerCombinationFamilies=1,distinctPublicSpeakerIds=3,notIndependentFiveSpeakers=True)
 p.with_name('new-reading.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in a.items()if k!='rows'}))
