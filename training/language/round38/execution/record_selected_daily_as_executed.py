"""Explicit SHA-bound judgments after complete unedited daily12 reading."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';p=E/'daily-new-python.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(p)=='baddc859c435125b035546df0e8943db9f8e9ae8b1bd27f5679a6a99866ffb24';g=json.loads(p.read_text());reasons=[
'帰りに行くのが出来るのが一番だったのでから行為・係りが不明。まだ行くのだろうと行くとを長く反復し語だけのloopへ崩れる。',
'卵とキャベツが残ったので夕食は何か食べるのでしょうかという独りの食事疑問は因果・主体が弱く、何をするかの自然な継続にならずprimary不成立。短いEOSの非loop。未提示の他者への食事確認と読む弱い代替は可能だが出力は補わない。',
'友達と会う予定を継がず日々の日が暮らす日の日から日本・大の文字の長いloopへ崩れる。',
'出かける前の準備・行動を継がず雨が降る同一節と活用崩壊を長く反復。',
'寝るのが寝るのが起きると主述が崩れ、寝ると寝ると寝るの長いloop。',
'趣味を始めるための行動を継がず行くのがの反復、その後・そのまま・道の文字へ長く崩壊。',
'何時にするという問いにおいしいと言うのですと答え、時刻や待ち合わせとの意味関係がない。短いEOSの非loop。',
'今日は今日はの局所反復、何を食べたのでの未完因果から昼食希望へ逸れ、仕事の疲れへの自然な応答が成立しない。有限35tokensでprimary非長期loop、侵入反復は別記。',
'卵で何を作るかの相談に自分はいやいという不明な引用・自己認識の問いが返り、意味・文脈がつながらない。短い有限2文。',
'週末の出来事を答えずおいしそうですかという言葉が思い出されるという受身の記憶へ逸れる。問いに対応する出来事が不明。短いEOS非loop。',
'近況への応答からAIがおいしそうという主述が不自然で、映画をご紹介しますへ転じる。映画紹介自体は文法的でも全体の話題・関係が成立しない。AIを等の文章修正はしない。短い有限2段落。',
'雨天に既定の公園予定をどうするかという相談に公園の所有句を5回重ね、行くことが必要とだけ述べる。21tokensのEOSでも所有句loopで意味不成立。']
loops={0,2,3,4,5,11};rows=[]
for i,(x,reason)in enumerate(zip(g['rows'],reasons,strict=True)):
 rows.append(dict(id=x['id'],fullOutputMeaningful=False,fullOutputLoop=i in loops,intrusiveRepetition=i in loops or i==7,reason=reason,prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
out=dict(generationSha256=sha(p),reviewer='Assistant actual complete reading of all12 selected daily outputs, not independent blind human evaluation',actualRetainedUpdates=10000,selectedStep=9500,evaluatedStep=9500,all12FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=0,wholeMeaningSensitivityPermittingUnstatedDinnerQuestionContext=1,longLoopsPrimary=6,eos=sum(x['eos']for x in g['rows']),notNewTest=True,notUsedForSelection=True,rows=rows);(E/'daily-new-reading.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='rows'}))
