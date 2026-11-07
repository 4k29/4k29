"""SHA-bound actual reading of these17 selected outputs; NOT a future grader."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round39';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();gp=E/'new-validation.json';assert sha(gp)=='be21316e726f8764390a21e670fd38bfeb95cc5d72e0c24c60a13620547d6987';g=read(gp);assert len(g['rows'])==17
refs={};bindings=[];bound={x['path']:x for x in read(P/'execution/artifact-manifest.json')['files']};keys=['grammar','meaning','connection','repetition','breaks','sentenceClosed']
for state,a,b in [('selected','new-validation.json','new-manual.json'),('terminal','terminal-state-diagnostic/original17-python.json','terminal-state-diagnostic/original17-manual.json')]:
 ap=P/'execution'/a;bp=P/'execution'/b;assert sha(ap)==bound[str(ap.relative_to(P))]['sha256'] and sha(bp)==bound[str(bp.relative_to(P))]['sha256'];old=read(ap);manual=read(bp);assert manual['generationSha256']==sha(ap)
 for x,y in zip(old['rows'],manual['rows'],strict=True):
  if '。' in x['text']:
   first=x['prefix']+x['text'].split('。')[0]+'。';v={k:y[k] for k in keys}
   if first in refs:assert refs[first][0]==v
   else:refs[first]=(v,state,x['id'])
 bindings.append(dict(state=state,generationSha256=sha(ap),manualSha256=sha(bp)))
reasons=[
'初文したはprefixを自然に完成する。以後おじさん・おじいちゃん・おかあさんの呼称と所有句を長く反復し、引用と主述が崩れて192tokensで切れる。',
'寒さを防ぐために出るという因果は弱い。以後夜の夜を多数連打し、がすかにかく等の崩れた活用へ進む。寒い場所からの退出を補う初文解釈は感度として別記。',
'風のなかにかけていて・おりかげと行為と語の結合が弱く、以後お母様の所有句とおおお等を長く反復する。擬人化そのものや創作の真偽を失格理由にしない。',
'eシールの導入からAI flex/Internation/Interationの長いLatin断片反復になり、引用も日本語文も閉じず192tokensで切れる。',
'初文の市場規模は自然に閉じるが、内訳は情報端末の主要202億円という分類・修飾関係が成立しにくい。携帯電話・PHAPSの名称の真偽だけで失格にはしない。有限63tokensEOS非loop、全文意味は不成立。',
'法律に基づく法律・同法の参照を重ね、再生可能エネルギーの活性化を図るとともにを何度も反復する。法番号の外部真偽ではなく、同じ活動の停滞反復と参照の弱さで全文不成立。',
'初文は海岸整備と海洋ごみ対策をつなぐ理解可能な継続。以後海域の海域を長く反復し、発発発・30～300年の大きな増加等へ崩れる。初文の外部法解釈を正しいと認定はしない。',
'対象地域を連打し、速報・協議会・地元の判断基準・解説の修飾と役割が崩れる。後半もそのときや発表されたときにを反復し、避難の説明が持続しない。',
'解析雨量が発表状況等を把握するという主述・役割関係が弱い。二文31tokensの有限EOS非loopだがprimarywhole0。解析雨量を使えばという道具の省略を許せばwhole1の感度を残す。',
'初文からSVGプロパティをの目的語重複。以後要素を指定するを入れ子で多数反復し、path関数の説明が進まない。',
'初文のHTMLグローバル属性指定は自然。以後CSS要素・要素を指定するを長く反復し、関係が進展しない。',
'初文は架空識別子Internationを含むがメソッドがメソッドを返すという文として理解可能で、外部API事実だけで失格にしない。以後comportype等の識別子成分を反復し、文と意味が崩れる。',
'SVGリクエストを提供するSVGリクエストという冗長な修飾から、送信するを何度も入れ子反復して説明が進まない。',
'情報を提供する方法を提供する方法という自己参照の後、WebGLのWebGLを多数反復し、企業サイトの説明が崩れる。',
'データなどの客観的な取組はカテゴリ関係に解釈差があるが、同じ初文の従来primary成分を維持する。以後統計調査の基準を設置し等を長く反復し、統計計計計等へ崩れる。',
'文化大臣の表現のために発展したという未完の修飾からアジアを多数連打し、引用・文が閉じない。',
'施策を講じられていますはprimaryでは格・受身の関係が弱く、尊敬表現として補う初文解釈は別の感度。以後文化観光推進法と地域計画の整備を反復し、所有句・参照関係も崩れる。']
rows=[];reused=0
for i,x in enumerate(g['rows']):
 first=x.get('observedFirstSentence');r=dict(id=x['id'],fullOutputMeaningful=False,fullOutputLoop=i not in [4,8],intrusiveRepetition=i not in [4,8],reason=reasons[i],prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
 if first in refs:
  v,state,id=refs[first];r.update(v);r['firstSentenceScoreProvenance']='Exact prefix+observed first sentence matches R39/'+state+'/'+id+'; same components after actual full reading';reused+=1
 elif i==5:r.update(zip(keys,[2,1,2,0,2,True]));r['firstSentenceScoreProvenance']='Fresh actual reading: formed legal-action sentence, but opaque references and repeated action clause; no factual accuracy certification'
 else:
  assert i in [3,15];r.update(zip(keys,[0,0,0,0,0,False]));r['firstSentenceScoreProvenance']='Fresh actual reading: no closed intelligible first sentence, long broken repetition'
 rows.append(r)
assert reused==14
m=dict(generationSha256=sha(gp),meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant actual complete reading of all17 new selected prefixes and continuations; not blind independent human',actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=9000,all17FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=0,longLoopsPrimary=15,eos=sum(x['eos'] for x in g['rows']),notNewTest=True,notUsedForSelection=True,wholeMeaningSensitivityPermittingInstrumentEllipsis=1,nonloopSensitivityTreatingFiniteWarningsAsNonloop=3,firstSentenceSensitivityStrictDataInitiativeCategory=5,firstSentenceSensitivityPermittingColdEscapeAndPassiveHonorific=8,firstSentenceHistoricalBindings=bindings,rows=rows)
(E/'new-manual.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print('Recorded actual17 full readings; whole0,loops15,eos',m['eos'])
