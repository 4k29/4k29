"""Read-only TRAIN row draw coverage at a saved step; no model or optimizer execution."""
import pathlib,sys,json,random,collections,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';sys.path.insert(0,str(R));import train as t
t.torch.set_num_threads(1);step=int(sys.argv[1]);assert step in [1000,5000,10000]
p=R/'continue-10000/checkpoint.pt'if step==10000 else E/f'retained-snapshots/{step}/checkpoint.pt';cp=t.torch.load(p,map_location='cpu',weights_only=False);zero=t.torch.load(R/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);assert cp['step']==step
if step==10000:assert t.read(R/'continue-10000/result.json')['completedRun']
info,_=t.load_partition(R/'multiview','train');rows=info['rows'];key=lambda x:(x['offset'],x['length'],x['prefixLength'],x['variant'],x['site']);lookup={key(x):i for i,x in enumerate(rows)};assert len(lookup)==len(rows)
source=lambda x:'realpersona'if x['document'].startswith('realpersona:')else'jmrd'if x['document'].startswith('jmrd:')else'other'
group=lambda x:f"{source(x)}:view{x['variant']}"
strata,weights,masses=t.sampler(rows,cp['settings']['genreSampling']);rng=random.Random();rng.setstate(zero['pythonRng']);draws=collections.Counter();unique=set();documents=set()
for i in range(step):
 _,batch=t.draw(rng,cp['settings']['batch'],strata,weights,masses)
 for x in batch:draws[group(x)]+=1;unique.add(lookup[key(x)]);documents.add(x['document'])
assert rng.getstate()==cp['pythonRng'];assert sum(draws.values())==step*cp['settings']['batch']
counts=collections.Counter(group(x)for x in rows);u=collections.Counter(group(rows[i])for i in unique)
out=dict(actualSnapshotUpdates=step,actualRowDraws=sum(draws.values()),availableIndexRows=len(rows),distinctIndexRowsDrawn=len(unique),fractionIndexRowsDrawn=len(unique)/len(rows),documentsDrawn=len(documents),availableDocuments=len({x['document']for x in rows}),privateEndingRngExactlyMatchesCheckpoint=True,checkpointSha256=t.sha(p),trainIndexSha256=t.sha(R/'multiview/train.index.json'),bySourceView={g:dict(availableIndexRows=n,rowDraws=draws[g],distinctIndexRowsDrawn=u[g],fractionIndexRowsDrawn=u[g]/n)for g,n in sorted(counts.items())},posthocDescriptiveExposureAuditNotConditionOrCheckpointSelection=True,notHeldoutOrGeneralizationMetric=True,rowsAndViewsOverlapUnderlyingText=True,parentTrainingCoverageNotDetermined=True,noModelForwardBackwardOrOptimizer=True,additionalOptimizerUpdates=0,interpretation='Rows not drawn in this run are not necessarily unseen text: variants/windows overlap and parent training may contain them; coverage does not prove that more steps will improve meaning')
(E/f'sampling-coverage-{step}.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k!='bySourceView'}))
