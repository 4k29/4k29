import pathlib,json,hashlib,re,datetime
R=pathlib.Path(__file__).resolve().parents[2];E=R/'execution';O=E/'interim-daily-2100';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();g=read(O/'daily-python.json');snap=read(O/'snapshot.json');assert g['modelFileSha256']==sha(O/'model.js');assert g['probeSha256']==sha(E/'daily-probes.json');assert len(g['rows'])==12
reasons=['帰りに行くのは何かの事でしたという曖昧な接続から、そうですね・そうなんですねを長く反復する。','夕食は食べ物を食べたかもしれないので食べるのであると時制と因果が曖昧で、食べるので・食べ物・食品の長い反復へ崩れる。','友達に会う予定から日本の日記録・大学・学校へ話題が飛び、学校の学校の再帰が続く。','雨が降り始めに降り続けていますという不自然な接続から、雨が降り続くとの長い反復になる。','寝床を下げるなど語の関係が崩れ、今夜の方針が展開せず相槌の長い反復になる。','まだまってしまいましたという不成立な続きから、そうですねを長く繰り返し趣味を始める方針が進まない。','待ち合わせ時刻の問いに天気の毒がるのかと続き、天気予報の説明とご利用くださいを長く反復する。','疲れへの応答にならず時分・時間の話へ飛び、その時間が経っているのはの節を長く反復する。','卵の料理の相談に統計という言葉の説明へ飛び、同じ引用と語る節を長く反復する。','週末の行動を答えず天気の毒がるのかから疑問とそうですねの長い反復へ流れる。','近況に天井の家と続き、時計の所有句や計算する節が長く再帰して出来事が進まない。','雨の日の予定への相談から公園の公園の長い所有句を反復し、地域の公園・保全へ飛ぶ。']
rows=[]
for r,reason in zip(g['rows'],reasons,strict=True):
 assert r['validTokens'] and r['validUtf8'] and not r['eos'] and len(r['tokens'])==192
 rows.append(dict(id=r['id'],group=r['group'],fullContinuationCoherent=False,longLoopObserved=True,eos=r['eos'],generatedTokens=len(r['tokens']),reason=reason))
review=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reader='Assistant actually read all12 complete prefixes and unedited full continuations; not independent human review',generationSha256=sha(O/'daily-python.json'),probeSha256=g['probeSha256'],actualRetainedUpdatesAtSnapshot=snap['actualRetainedUpdatesAtSnapshot'],selectedStep=snap['selectedStep'],interimOnly=True,finalRoundJudgment=False,developmentOnly=True,newTestUsed=False,originalStrictGateChanged=False,usedForCheckpointSelection=False,rows=rows,totals=dict(fullCoherent=0,longLoops=12,eos=0))
(O/'daily-reading.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n')
old=read(R.parent/'round28/execution/daily-old-python.json');prior=read(R.parent/'round28/execution/daily-new-python.json');lines=['# Interim daily generation: unabridged comparisons','','Round29 retained2100 / selected2000. This is an incomplete-run diagnostic, not final adoption or a new TEST. R25 and R28 comparators finished10000 updates. Inputs and decoding match; training progress differs. No output repair or penalty.','']
for a,b,c in zip(old['rows'],prior['rows'],g['rows'],strict=True):
 assert all(a[k]==b[k]==c[k] for k in ['id','prefix','inputTokens'])
 fence='`'*max(3,1+max((len(x) for x in re.findall(r'`+',a['prefix']+a['text']+b['text']+c['text'])),default=0));lines.extend(['## '+c['id'],'','Prefix:',fence+'text',c['prefix'],fence])
 for label,row in [('AdoptedR25 / completed10000 / selected9500',a),('R28 mass30% / completed10000 / selected10000',b),('InterimR29 mass10% / retained2100 / selected2000',c)]:lines.extend(['',label+':',fence+'text',row['text'],fence])
(O/'FULL_GENERATIONS.md').write_text('\n'.join(lines)+'\n')
# The aborted first evaluation is retained; every complete raw row must match this rerun exactly.
partial=[json.loads(l) for l in (O/'daily-generation-first-incomplete.log').read_text().splitlines()];assert len(partial)==4
for a,b in zip(partial,g['rows']):assert all(a[k]==b[k] for k in ['id','text','tokens','eos','validUtf8','validTokens','inputTokens'])
(O/'evaluation-execution.json').write_text(json.dumps(dict(firstInvocationEndedBeforeFullReport=True,firstCompleteRawRows=4,firstLogSha256=sha(O/'daily-generation-first-incomplete.log'),rerunSameSnapshotAndConditions=True,allFirstFourRawOutputsExactlyReproduced=True,rerunCompletedRows=12,trainingProcessNotInterrupted=True,noLearningInputOrPolicyChanges=True,reportSha256=sha(O/'daily-python.json')),indent=2)+'\n')
print('All12 full outputs reviewed;0coherent/12loops/0EOS; partial first4 outputs bitexact on rerun')
