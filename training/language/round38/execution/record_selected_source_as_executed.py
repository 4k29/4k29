"""Explicit full five-source-DEV judgments; one speaker-combination family."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';p=E/'fixed-source-mrmp-dev/new-python.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(p)=='e4606aca215d4c369a309f45dfd47d9cd3377629953bc3f32e4cc900dac1dbaa';g=json.loads(p.read_text());reasons=[
'仕事から帰るとポップコーンの香りがしたという話への相槌は自然だが、おすすめの映画ですかという問いの対象が提示されていない。映画館の仕事を連想する余地はあってもおすすめ作品という対象は補われずprimary全文失敗。映画館ですか等へ修正しない。短いEOS非loop。',
'赤ちゃん連れの母親への共感からお母さんはお母さんの顔を見たいという自己参照的な人物関係へ逸れる。誰の顔をなぜ見たいのかがつながらずprimary失敗。2回の母親語は局所反復で有限22tokensの非長期loop。',
'旧R37selectedと同じそうですね、あとは？で、土産店やロープウェイの話から何を追加で尋ねるかが曖昧なため同じprimary不成立。追加の場所を尋ねる省略を広く許す弱い代替は成立可。短いEOS非loop。',
'人生で一度スカイダイビングをしたいという希望から何かの事件があったのかへ転じる。問い自体の統語・意味は通るが、事件を尋ねる根拠・動機との結び付きが弱くprimary不成立。事件をきっかけという広い意味で動機を尋ねると解釈すれば最小行為成立の弱い代替は残す。出力はきっかけへ修正しない。',
'洗面所の話に今日は毎日を192tokens長く反復し述語も成立しない。']
rows=[]
for i,(x,reason)in enumerate(zip(g['rows'],reasons,strict=True)):
 rows.append(dict(id=x['id'],fullOutputMeaningful=False,fullOutputLoop=i==4,intrusiveRepetition=i in {1,4},contentBeyondBackchannel=False,explicitContextObjectReference=False,reason=reason,prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
out=dict(generationSha256=sha(p),reviewer='Assistant actual complete reading of all5 selected source-DEV outputs; not independent blind human evaluation',actualRetainedUpdates=10000,selectedStep=9500,evaluatedStep=9500,all5FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=0,contentBeyondBackchannel=0,explicitContextObjectReferences=0,longLoopsPrimary=1,eos=sum(x['eos']for x in g['rows']),wholeMeaningSensitivityPermittingAdditionalPlaceQuestion=1,wholeMeaningSensitivityPermittingIncidentAsMotivationQuestion=1,wholeMeaningSensitivityPermittingBothWeakQuestions=2,independentSpeakerCombinationFamilies=1,distinctPublicSpeakerIds=3,notIndependentFiveSpeakers=True,notNewTest=True,notUsedForSelection=True,rows=rows);(E/'fixed-source-mrmp-dev/new-reading.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='rows'}))
