"""Fixed judgments after actual complete reading; not an automatic grader."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();gp=E/'new-validation.json';assert sha(gp)=='ea6fc1ee0d5bf34c111152f337da944c85a08ea8163064f2c36dd57957eaeabf';g=read(gp);old=read(R.parent/'round37/execution/new-validation.json');oldm=read(R.parent/'round37/execution/new-manual.json')
reasons=[
'初文したは自然。以後おじいちゃんの呼称・所有句を長く反復し、よの前に述語がなく引用も崩れる。',
'寒さを防ぐために出て来たは統語的に閉じるが、疲れと防寒から外へ出る接続は説明がなく弱い。後続なかにかく・寝て来たから夜の所有句を長く反復。暖かい場所へ出たという未提示の状況を補う初文成立の弱い感度を別記。',
'葦を擬人化した来訪の初文は創作として自然。もう一度もあってもらったり・いつもり等の活用と指示が崩れ、なくなったの同一文とまだを長く反復。',
'開始した引用を閉じずAIのAIという修飾、社会実装に向けたの重複へ崩れる。AIの進展に取り組む・今後AIの活用が進展の循環が続くためprimary長期loop。変化する有限の政策列とみる非loop感度も残す。',
'市場規模の初文は自然。内訳から周波数・輸出額へ逸れ、契約数は移行が行われるという主述、数値の係りも崩れる。PHAPS3回の局所反復があるが数値・対象が変わる有限列をR37terminalと同様primary非長期loop、広い意味反復のloop感度あり。',
'経済活動に必要な資源を創出する取組を推進します、で文法・修飾・目的が自然に閉じEOS。循環分野・金融機関という書き出しとの接続も持続する短い政策文として全文成立。実政策の真偽は認定しない。',
'法の目標と基準を設け対策を講じる初文は成立。後続の基準を設置・達成を実施という語結合が弱く、生態系の保全を7回以上長く反復。',
'初文は従来の機関省略許容で9点。警報・予報の局所並列、レベルを付した火山ではレベルを付す循環と主体の欠落で全文失敗。旧selectedの同一節5回loopより変化する有限の警戒説明へ進むためR37terminalの基準でprimary非長期loop。警戒句の循環を重くみるloop感度も保存。',
'旧selectedと同じ初文で、解析雨量という手段と把握主体・速報版発表状況の関係が弱く6点を維持。短い解説参照は自然で非loopだがprimary全文失敗。解析雨量を用いてと補えば成立する弱い代替を保存し、出力自体は補修しない。',
'CSS関数からプロパティ指定の初文は言語として成立しAPI事実は認定しない。後続はプロパティの値がそれを指定する循環を長く反復。',
'グローバル属性を指定できる初文は成立。要素を指定する要素を定義するという自己参照の長い周期で全文崩壊。',
'旧と同一のメソッドが別オブジェクトのメソッドを返す初文は同じ10点。今回はEOSで終わらずメソッド・配列の所有句へ長く循環し全文失敗。未知のInternationという名前だけで失格にはしていない。',
'SVGリクエストを提供するSVGリクエストを提供するという初文の再帰は旧terminal類似例と同じ7点。以後提供・送信の同一節を長く循環し切断。',
'ウェブサイトのウェブサイトを提供するという初文の修飾と目的が不明。以後ほぼ同じこの例では参照してくださいを4回以上循環し70tokensでEOSでもprimaryloop。',
'客観的手段として調査対象者が調査対象者を実施するという対象・動作の関係が崩れる。調査票を得る方法を調査する同一節を長く反復。',
'表現件の共同声明が認められたという初文は主題と主語の係り・表現件が不明。覚書を開催、日中韓国の日米国等も崩れる。日付と会合が変化する有限列でprimary非長期loop、アジアの局所4回・協力を強化の3回は侵入反復として記録し広いloop感度も保存。',
'必要な施策を講じられていますはこの法規文脈でをと受身・主体の係りが不自然。後続観光推進法人から法人・法の文字を長く反復。尊敬・可能として初文を許す弱い解釈は感度のみで保存。']
scores=[[2,2,2,2,2,True],[2,1,1,2,2,True],[2,2,2,2,2,True],[0,0,1,0,0,False],[2,2,2,2,2,True],[2,2,2,2,2,True],[2,2,2,2,2,True],[2,1,2,2,2,True],[1,1,1,2,1,True],[2,2,2,2,2,True],[2,2,2,2,2,True],[2,2,2,2,2,True],[2,1,2,1,1,True],[1,0,1,0,0,True],[2,0,1,1,0,True],[1,0,0,2,0,True],[1,1,2,2,1,True]]
keys=['grammar','meaning','connection','repetition','breaks','sentenceClosed'];nonloop={4,5,7,8,15};rows=[]
for i,(x,reason,values,y,z)in enumerate(zip(g['rows'],reasons,scores,old['rows'],oldm['rows'],strict=True)):
 j=dict(id=x['id'],fullOutputMeaningful=i==5,fullOutputLoop=i not in nonloop,intrusiveRepetition=i not in {5,8},reason=reason,prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),**dict(zip(keys,values,strict=True)))
 if x['observedFirstSentence']==y['observedFirstSentence']:
  assert all(j[k]==z[k]for k in keys);j['firstSentenceScoreProvenance']='Exact observed first sentence matches prior R37; same component scores after full new reading'
 else:j['firstSentenceScoreProvenance']='Changed first sentence actually read under unchanged rubric; whole continuation independently assessed'
 rows.append(j)
out=dict(generationSha256=sha(gp),meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),reviewer='Assistant actual complete reading of selected original17, not independent blind human evaluation',actualRetainedUpdates=10000,selectedStep=9500,evaluatedStep=9500,all17FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=1,longLoopsPrimary=12,eos=sum(x['eos']for x in g['rows']),notNewTest=True,notUsedForSelection=True,wholeMeaningSensitivityPermittingInstrumentEllipsis=2,nonloopSensitivityTreatingFiniteAiListAsNonloop=6,nonloopSensitivityCountingAllThreeFiniteListsAsLoops=2,firstSentenceSensitivityPermittingColdEscapeAndPassiveHonorific=11,rows=rows)
(E/'new-manual.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');subprocess.run(['python',str(R.parent/'round10/review.py'),'--generation',str(gp),'--manual',str(E/'new-manual.json'),'--out',str(E/'new-review.json')],check=True)
