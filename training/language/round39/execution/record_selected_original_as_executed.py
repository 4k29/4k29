"""SHA-bound human-style judgments after all17 full selected outputs were read."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());gp=E/'new-validation.json';assert sha(gp)=='5a9aa212f63d90db949a6353a92f95307fc81143ee04394aeed411c654fb23e6';g=read(gp);result=read(R/'continue-10000/result.json');assert result['completedSteps']==10000 and result['bestStep']==9000
reasons=[
'初文したはprefixを自然に完成。以後おじさん・おかあさん・おじいさんの呼称と所有句を長く反復し、引用と主述が崩れ192tokensで切れる。',
'寒さを防ぐために出て来たは動機との関係が弱く初文は従来と同じ8点。以後夜の夜の長いloopとすかにかくという活用崩壊。寒さから逃れて出たという弱い初文代替は感度だけで保存。',
'葦が風のなかにかけていて、おりかげになってしまったは行為・係りと述語の関係が成立しにくい。未提示の掛ける対象や語を補わない。以後お母様の所有句とおおおの文字loop。未知語の存在だけを失敗理由にはしない。',
'未完の引用内でInter等の字列を長く反復し、初文も全体も閉じず192tokensで切れる。',
'初文るは自然。後続の内訳は情報端末の主要202億円という名詞・数量の係りが不明で、全文はprimary不成立。PHAPSという未知名や数値の事実未確認だけで失敗にはしない。有限3文EOSの非loop。',
'経済活動に関する法律を改正する構文から、同法に基づきと再生可能エネルギーの創出を図るとともに・促進の入れ子反復が初文内から増える。後続も同じ創出句を長く反復して切断。法番号の真偽を失敗理由にしない。',
'目標及び改正法に基づき海洋ごとに対策を図った初文は言語として成立し事実は認定しない。以後海域の所有句、及び、発生の長い反復と異常して等の語法崩壊。EOSでも全文loop。',
'噴火速報の初文から対象地域の所有句を4回重ね対象・設定・判断の説明が崩れる。以後そのときを5回重ねどきらかじめへ崩れ、警戒レベル句も再帰して切断。primaryloop。有限の警報説明内の侵入反復として非loopに寄せる代替を別記。',
'解析雨量は発表状況や少雨の状況を把握できるという道具・主体の関係が不自然。詳しくはの文は自然でも全体primary不成立。従来同一prefix/textと同じ非loop・初文6点。解析雨量を用いればという道具省略を許す弱い全文代替は別記。',
'初文からSVGプロパティをを重複し目的語の係りが崩れる。以後指定するSVG要素を指定するを長く反復。APIの事実未確認ではなく出力内の構文と反復を理由にする。',
'グローバル属性を指定できる初文は自然。以後要素を指定する要素をの自己参照を192tokens反復し全文崩壊。',
'他オブジェクトのメソッドを返す初文は従来同一文と同じ10点。未知のInternationやNode.conssourceという名だけで失敗にはしない。後続のcomportype/prototypeの長い入れ子・未完呼出しで全文loop。',
'SVGリクエストを提供するSVGリクエストを提供する初文は従来同一文と同じ7点。以後送信するSVGリクエストを送信するを長く反復して切断。',
'情報提供の方法を提供する方法を提供する方法という初文の入れ子で目的が不明。以後WebGLの所有句を長く反復。未知のWebRAPIという字列自体を失敗理由にしない。',
'データなどの客観的な取組が必要という初文は、データと取組のカテゴリーの弱さをmeaning1で記録し、語順・活用と品質管理への接続は2とする。合計9点という既存規則でprimary初文合格。カテゴリー不整合をgrammar1にする厳しい代替では初文不合格。以後統計調査の基準を満たす・基準を設置・統計計の長いloopで全文失敗。',
'文化大臣の表現のために発展したという未完修飾からアジアを192tokens反復し引用も述語も閉じない。',
'必要な施策を講じられていますは従来同一初文と同じ7点。をと受身・主体の係りが不自然。後続の文化観光法・地方公共団体・地域計画の所有句を長く反復して切断。尊敬・可能として初文を許す弱い代替は別記。']
scores=[[2,2,2,2,2,True],[2,1,1,2,2,True],[1,1,1,2,1,True],[0,0,1,0,0,False],[2,2,2,2,2,True],[2,1,2,0,1,True],[2,2,2,2,2,True],[2,0,1,0,1,True],[1,1,1,2,1,True],[1,1,2,1,1,True],[2,2,2,2,2,True],[2,2,2,2,2,True],[2,1,2,1,1,True],[2,1,2,0,1,True],[2,1,2,2,2,True],[0,0,0,0,0,False],[1,1,2,2,1,True]];keys=['grammar','meaning','connection','repetition','breaks','sentenceClosed'];oldg=read(R.parent/'round38/execution/new-validation.json');oldm=read(R.parent/'round38/execution/new-manual.json');rows=[]
for i,(x,reason,values,y,z)in enumerate(zip(g['rows'],reasons,scores,oldg['rows'],oldm['rows'],strict=True)):
 j=dict(id=x['id'],fullOutputMeaningful=False,fullOutputLoop=i not in {4,8},intrusiveRepetition=i not in {4,8},reason=reason,prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),**dict(zip(keys,values,strict=True)))
 if x['observedFirstSentence']==y['observedFirstSentence'] and x['observedFirstSentence']is not None:
  assert all(j[k]==z[k]for k in keys);j['firstSentenceScoreProvenance']='Same prefix and exact observed first sentence as R38; same components after actual full new reading'
 else:j['firstSentenceScoreProvenance']='Changed first sentence actually read under unchanged rubric, independently of whole-output judgment'
 rows.append(j)
a=dict(generationSha256=sha(gp),meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant actual complete reading of all17 new selected prefixes and continuations; not blind independent human',actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=9000,all17FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=0,longLoopsPrimary=15,eos=sum(x['eos']for x in g['rows']),notNewTest=True,notUsedForSelection=True,wholeMeaningSensitivityPermittingInstrumentEllipsis=1,nonloopSensitivityTreatingFiniteWarningsAsNonloop=3,firstSentenceSensitivityStrictDataInitiativeCategory=5,firstSentenceSensitivityPermittingColdEscapeAndPassiveHonorific=8,rows=rows);(E/'new-manual.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');subprocess.run(['python',str(R.parent/'round10/review.py'),'--generation',str(gp),'--manual',str(E/'new-manual.json'),'--out',str(E/'new-review.json')],check=True)
