import pathlib,json,hashlib,re,shutil
R=pathlib.Path('/workspace/4k29/training/language/round45');E=R/'execution';P=R.parent/'round44';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
assert not(R/'source-manifest.json').exists()and not(R/'continue-10000/checkpoint.pt').exists()
raw=P/'execution/context-original-candidates.json';assert sha(raw)=='c0f368c35e78c0f0d9a47181926b3eb51a0377f8ffe9e8e59a1ad17fd5622b7f';j=read(raw);old=read(P/'execution/context-auxiliary-pool.json');assert len(j['rows'])==1616
rows=[]
for x in j['rows'][:1024]:
 x=dict(x);x['anchors']=sorted((set(re.findall('[一-龯]{3,}',x['prefix']))&set(re.findall('[一-龯]{3,}',x['target'])))-{'大丈夫','気分的'});assert not any(a in x['wrongPrefix']for a in x['anchors']);rows.append(x)
assert rows[:256]==old['rows']
new=dict(old);new.update(rows=rows,selection='Original frozen1616 >=2-kanji candidate pairs and donors/SHA order unchanged; increase ONLY prefix pool size256 to1024, keep no mandatory3-kanji condition; no balancing/filter/model score',initialCandidateCount=1616,initialCandidatePoolSha256=sha(raw));dest=E/'context-auxiliary-pool.json';write(dest,new);shutil.copy2(raw,E/raw.name)
key=lambda x:(x['document'],x['turn']);ks={key(x)for x in rows};diag=read(E/'context-plan.json')['rows'];overlap=[dict(document=x['document'],turn=x['turn'])for x in diag if key(x)in ks];proof=dict(actualOptimizerUpdates=0,onlyChangedLearningFactor='auxiliary pool size256 to1024',originalCandidateSha256=sha(raw),originalCandidateCount=1616,old256RowsExactPrefixOfNew1024=True,selectedPairs=1024,selectedOriginalCandidateRanks=list(range(1024)),positiveDocuments=len({x['document']for x in rows}),donorDocuments=len({x['wrongDocument']for x in rows}),train64ExactPositivePairOverlap=len(overlap),train64OverlappingPairs=overlap,diagnostic64NotHeldout=True,noNewSourceOrTestRead=True,poolSha256=sha(dest),totalAuxiliaryPairExposuresUnchanged=2000)
write(E/'pool-selection-proof.json',proof)
p=read(R/'policy.json');p['contextPreference'].update(poolSha256=sha(dest),eligibility=new['selection'],poolPairs=1024);write(R/'policy.json',p)
for f in ['prospective-evaluation-plan.json','interim-plan.json','diagnostic-plan-reuse.json']:
 x=read(E/f);x.update(currentAuxiliaryPoolSize=1024,train64ExactCurrentPoolOverlap=len(overlap),train64NotHeldout=True,subgroups='currentPoolPair and notCurrentPoolPair on same frozen64, bothTRAIN; membership relative to new1024 for both models; no diagnostic reselection');write(E/f,x)
(R/'README.md').write_text('# R45 — auxiliary pool size only\n\n実更新0、開始前監査中。元1616候補の同じSHA順先頭256→1024のみ変更。旧256は新poolの完全prefix。CE係数.1/every10/batch2、総10000更新/2000auxpairs、全main/モデル/LR/seed/R28fullstate/selector/gateを保持。固定TRAIN64の現pool重複は'+str(len(overlap))+'組で別集計し未見評価とはしない。意味改善は未測定、公開/R25anchor維持。\n')
(R/'REPRODUCTION.md').write_text('# R45 reproduction\n\n実更新0。原典/token/境界/勾配/初期stateを開始前検証してfreeze。完了/稼働中の再起動は禁止。部分checkpointだけ同一条件--resume。最新実step・model/Adam/RNGを保存し、意味は全文読解後に判定する。\n')
shutil.copy2(pathlib.Path(__file__),E/'select_pool_as_executed.py');print(json.dumps({k:v for k,v in proof.items()if k not in ['selectedOriginalCandidateRanks','train64OverlappingPairs']}))
