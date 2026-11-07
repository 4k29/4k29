"""Summarize fixed TRAIN64 membership groups from completed read-only diagnostics."""
import pathlib,json,sys,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution'
read=lambda p:json.loads(p.read_text())
step=int(sys.argv[1]);assert step in [1000,5000]
H=E/f'paired-human-dev-{step}'
assert read(H/'complete.json')['actualUpdatesEach']==step
pool=read(E/'context-auxiliary-pool.json')['rows'];ks={(x['document'],x['turn'])for x in pool};plan=read(E/'context-plan.json')['rows'];mask=[(x['document'],x['turn'])in ks for x in plan];assert sum(mask)==7;models={}
for label in ['old','new']:
 j=read(H/f'{label}-context.json');groups={}
 for name,value in [('currentPoolPair',True),('notCurrentPoolPair',False)]:
  rr=[r for r,m in zip(j['rows'],mask,strict=True)if m==value];groups[name]=dict(pairs=len(rr),meanCorrectNll=sum(r['correctNllPerToken']for r in rr)/len(rr),meanContextGain=sum(r['contextGain']for r in rr)/len(rr))
 models[label]=groups
(H/'context-membership-subsets.json').write_text(json.dumps(dict(actualUpdatesEach=step,subgroupsPredeclaredBeforeTraining=True,currentPoolSize=1024,notHeldoutOrNewTest=True,membershipRelativeToIdentical1024PoolForBothModels=True,mainSamplingDifferenceIntrinsic=True,models=models),indent=2)+'\n')
