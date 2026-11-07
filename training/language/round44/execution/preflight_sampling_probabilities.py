"""Analytic marginal source/view/row probability audit on every TRAIN stratum."""
import pathlib,json,hashlib,sys,collections,math
R=pathlib.Path(__file__).resolve().parents[1];P=R.parent/'round43';sys.path.insert(0,str(R));from train import load_partition
from batching import sampler,VIEWS
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();policy=read(R/'policy.json');info,_=load_partition(R/'multiview','train');rows=info['rows'];assert all(r['site']!='human-chat'or r['document'].startswith(('realpersona:','jmrd:'))for r in rows)
strata,weights,masses=sampler(rows,policy['genreSampling']);view=collections.defaultdict(float);sources=collections.defaultdict(float);genres=collections.defaultdict(float);expected_counts=collections.Counter((r['site'],r['variant'],'jmrd'if r['document'].startswith('jmrd:')else'realpersona'if r['site']=='human-chat'else'other')for r in rows)
for (site,v,width,src),rs in strata.items():
 actual=weights[(site,v,width,src)];view[v]+=actual;genres[site]+=actual;sources[src]+=actual
 mass=policy['humanSourceSampling'][src]if site=='human-chat'else policy['genreSampling'][site];expected_row_probability=mass*{0:.4,1:.3,2:.3}[v]/expected_counts[(site,v,src)]
 # Independent conditional-probability factorization: P(width)*P(stratum|width)*P(row|stratum).
 row_probability=masses[width]*(actual/masses[width])*(1/len(rs));assert math.isclose(row_probability,expected_row_probability,rel_tol=1e-12,abs_tol=1e-18)
for v,p in {0:.4,1:.3,2:.3}.items():assert math.isclose(view[v],p,abs_tol=1e-12)
assert math.isclose(sources['realpersona'],.4,abs_tol=1e-12)and math.isclose(sources['jmrd'],.05,abs_tol=1e-12)and math.isclose(sources['other'],.55,abs_tol=1e-12)
old=read(P/'policy.json')['genreSampling']
for g,p in policy['genreSampling'].items():assert math.isclose(genres[g],p,abs_tol=1e-12);assert g=='human-chat'or math.isclose(p/old[g],.55/.7,abs_tol=1e-12)
assert (R/'batching.py').read_bytes().replace(b"'realpersona':.40",b"'realpersona':.25")==(P/'batching.py').read_bytes()
for n in policy['codeHashes']:
 if n!='batching.py':assert (R/n).read_bytes()==(P/n).read_bytes(),n
assert sha(R/'execution/context-auxiliary-pool.json')==sha(P/'execution/context-auxiliary-pool.json')
out=dict(actualOptimizerUpdates=0,everyTrainRowProbabilityVerified=True,trainRows=len(rows),strata=len(strata),viewMarginals=dict(view),sourceMarginals=dict(sources),genreMarginals=dict(genres),widthMarginals=masses,otherGenreRelativeProportionsPreserved=True,onlyOneBatchingSourceMassLiteralChanged=True,otherNineLearningFilesByteIdentical=True,pool1024ByteIdentical=True,noRngOrOptimizerUsed=True,notLanguageEvidence=True)
(R/'execution/sampling-probability-preflight.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
