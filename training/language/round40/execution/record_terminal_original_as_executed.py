"""SHA-bound actual complete reading of terminal17; not a future grader."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();gp=D/'original17-python.json';assert sha(gp)=='f29afb001ce3d0fbaef13e1b9a550425df45e28362ae6533565e8ec10f769399';g=read(gp);keys=['grammar','meaning','connection','repetition','breaks','sentenceClosed'];refs={}
for rn,state,a,b in [('round39','selected','new-validation.json','new-manual.json'),('round39','terminal','terminal-state-diagnostic/original17-python.json','terminal-state-diagnostic/original17-manual.json'),('round40','selected','new-validation.json','new-manual.json')]:
 root=R.parent/rn/'execution';ap=root/a;bp=root/b;old=read(ap);m=read(bp);assert m['generationSha256']==sha(ap)
 for x,y in zip(old['rows'],m['rows'],strict=True):
  if '。' in x['text']:
   f=x['prefix']+x['text'].split('。')[0]+'。';v={k:y[k] for k in keys}
   if f in refs:assert refs[f][0]==v
   else:refs[f]=(v,rn+'/'+state+'/'+x['id'])
reasons=[
'初文したは自然。以後おじいちゃんの呼称と所有句を多数連打し、主述・引用が崩れて192tokensで切れる。',
'寒さを防ぐために出るという接続は従来primaryでは弱い。以後夜の夜・夜夜等を長く反復し、暮れ・夜明け等の文中意味も崩れる。',
'風のなかにかきらがあって行くという主述・語結合が成立せず、ぼんやり・ぼくのぼく等を192tokens反復して閉じない。擬人化そのものを失敗理由にはしない。',
'eシールからAI for formation/Internation等のLatin断片を多数反復し、引用も文も閉じない。',
'市場規模の初文は自然だが、情報端末の主要2億円という修飾・分類が弱く、同じ音声系ソフトへ別の内訳を並べて区別が不明。61tokens有限EOS非loop。外部数値の真偽だけで全文falseにはしない。',
'初文の法に基づく活動促進・温暖化対策は冗長だが理解可能で、同じ初文の従来9点を維持。後続の国会議・COP・日中韓国等の参照と引用が崩れる。変化する有限の会合・日付列挙でprimary非長期loop、侵入反復はあり。',
'初文中から海域の所有句を多数重ねて海域を推進という対象が崩れる。以後及び海域・約30年を多数反復し、単位と主述も壊れる。',
'速報が協議会で共同検討を実施しレベルを運用するという主体・役割が弱く、括弧・引用も不整合。後続は噴火警戒レベルを付して発表しますを何度も同文反復する。旧terminalの変化する警報説明とは区別してprimaryloop。',
'解析雨量が発表状況等を把握するという主述・役割がprimaryでは弱い。二文33tokensEOSで非loop。解析雨量を使えばという道具の省略を許すwhole1の感度は保持。',
'初文からSVGプロパティをを重複し、以後値の値・この値はSVGプロパティの値という自己参照を多数反復する。',
'初文のグローバル属性設定は自然。以後要素に設定される要素を指定する等の自己参照を長く反復して切れる。',
'初文は架空識別子を含むがメソッドがメソッドを返す文として自然でAPI事実は認定しない。以後文字列・配列の配列を多数反復し、配列配列等へ崩れる。',
'ポリシーを使用してSVGリクエストを提供する初文は理解可能。後続で送信するリクエストを送信する等の入れ子を多数重ね71tokensEOS。R39terminalと完全同一の全文で同じprimaryloop/whole0。',
'情報提供の方法を提供する方法という初文は従来8点。以後WebGLのWebGLを多数反復して切れる。R39terminal同一全文と同じloop/whole0。',
'初文のデータなどの客観的な取組は従来primary意味1・合計9点を維持。以後管理の文字と語を多数連打し、法律・管理体制の説明も意味を維持しない。',
'文化大臣の表現のための会合という係り、閉じない括弧、アジア5回の連打が初文を崩す。後続は異なる日付・会合の有限列挙でprimary非長期loop。開催と発展の項や時間の接続は弱い。未知の会合の存在だけで失格にはしない。',
'施策を講じられていますは格・受身の関係が弱い従来7点。以後地方公共団体を11回ほど連打し、地域計画と計画計画も反復して切れる。']
fresh={2:[0,0,0,0,0,False],3:[0,0,0,0,0,False],6:[1,0,1,0,1,True],7:[1,1,1,2,1,True],15:[1,0,1,0,0,True]};rows=[];reused=0
for i,x in enumerate(g['rows']):
 f=x['prefix']+x['text'].split('。')[0]+'。' if '。' in x['text'] else None;r=dict(id=x['id'],fullOutputMeaningful=False,fullOutputLoop=i not in [4,5,8,15],intrusiveRepetition=i!=8,reason=reasons[i],prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
 if f in refs:r.update(refs[f][0]);r['firstSentenceScoreProvenance']='Exact prefix+first sentence matches '+refs[f][1]+'; same components after actual whole reading';reused+=1
 else:r.update(zip(keys,fresh[i]));r['firstSentenceScoreProvenance']='Fresh actual terminal full reading under unchanged rubric'
 rows.append(r)
assert reused==12
m=dict(generationSha256=sha(gp),meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant actual complete reading of all17 terminal prefixes and continuations; not independent blind human',actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=10000,all17FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=0,longLoopsPrimary=13,eos=sum(x['eos'] for x in g['rows']),notNewTest=True,notUsedForSelection=True,wholeMeaningSensitivityPermittingInstrumentEllipsis=1,nonloopSensitivityIncludingFiniteConferenceAndLegalRepetitionsAsLoops=15,firstSentenceSensitivityStrictDataInitiativeCategory=6,rows=rows);assert m['eos']==3;(D/'original17-manual.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');print('Terminal17 actual full reading saved: whole0,loops13,EOS3')
