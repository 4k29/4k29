"""Explicit full-context native8 reading, not an automatic grader."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';p=E/'content-native-dev/new-python.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(p)=='13c2da31a5809bdcc4808e0cfc98250806fa53b493f20fd33118890931ec07e4';g=json.loads(p.read_text());reasons=[
'歩くことが健康によいという話に私もお好きですかと返す。自分も好きかという対象・話者と歩行の話題がつながらずprimary不成立。私も好きです等に修正しない。短いEOS非loop。',
'バイクを長く大切に乗る説明へのそうですね！は最小の相槌として自然。内容ある提案・新情報の成功とは数えない。旧R37同一prefix/textなら同一判定。',
'どんなにかなんかもしれないは語の接続・活用が崩れ、次のどんな感じかも挨拶の時刻境界に結び付かない。有限2文で非loop。',
'酸っぱさを補う飲み方探しに対応せず、おいしいですねとそうなんですねを192tokens長く循環。初めが意見でも後続崩壊を隠さず全文失敗。',
'高温で外出を避ける話への今日は何かのことですかは指示内容が不明な問い。相槌は自然でも全文の会話行為が成立しない。短いEOS非loop。',
'女優の好みを既に述べた相手へあなたは？とだけ聞き返し、何を尋ねるかが不明。旧R37と同じprimary不成立。好みの再確認として広く許す弱い代替のみ保存。',
'積み重なるストックとメモの話からどんな映画を見たいかへ無根拠に転じる。それが映画を指す根拠もなく、短くEOSでも文脈の意味が不成立。映画の問い自体の文法は自然。',
'簡単でおいしいパスタへの共感と明日の食欲の話にそうですね、おいしいですねと返し、パスタを暗黙の主題にした最小の自然な味の共感として成立。旧私もおいしいとは異なり自分が美味であるという主述の誤りはない。新情報や明示的な文脈語はない。']
rows=[]
for i,(x,reason)in enumerate(zip(g['rows'],reasons,strict=True)):
 rows.append(dict(id=x['id'],fullOutputMeaningful=i in {1,7},fullOutputLoop=i==3,intrusiveRepetition=i==3,contentBeyondBackchannel=i==7,explicitContextObjectReference=False,newInformation=False,reason=reason,prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
out=dict(generationSha256=sha(p),reviewer='Assistant actual complete reading of all8 selected native-human DEV outputs, not independent blind human evaluation',actualRetainedUpdates=10000,selectedStep=9500,evaluatedStep=9500,all8FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=2,contentBeyondBackchannel=1,explicitContextObjectReferences=0,newInformationResponses=0,longLoopsPrimary=1,eos=sum(x['eos']for x in g['rows']),wholeMeaningSensitivityPermittingVagueActressQuestion=3,notNewTest=True,notUsedForSelection=True,rows=rows);(E/'content-native-dev/new-reading.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='rows'}))
