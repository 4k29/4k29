"""Exact sampling marginal check, zero optimizer updates."""
import pathlib,sys,collections,json
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from train import read,write,sampler,sha
from batching import VIEWS
info=read(ROOT/'multiview/train.index.json');genres=read(ROOT/'policy.json')['genreSampling']
strata,weights,masses=sampler(info['rows'],genres);view=collections.defaultdict(float);site=collections.defaultdict(float)
for k,w in weights.items():view[k[1]]+=w;site[k[0]]+=w
assert all(abs(view[k]-v)<1e-12 for k,v in VIEWS.items())
assert all(abs(site[k]-v)<1e-12 for k,v in genres.items())
assert all(weights[k]>0 for k in strata)
assert all(m>0 for m in masses.values())
write(ROOT/'execution/sampling-marginals.json',dict(viewMasses=dict(view),genreMasses=dict(site),bucketMasses=masses,allThreeTrainingViewsActive=True,optimizerUpdates=0,trainIndexSha256=sha(ROOT/'multiview/train.index.json')))
print(json.dumps(dict(viewMasses=dict(view),genreAndViewMassesVerified=True)))
