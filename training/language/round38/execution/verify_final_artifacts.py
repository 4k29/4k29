"""Read-only final SHA/state/tracking closure; restore absent lossless raw files only."""
import pathlib,json,hashlib,sys,subprocess,random
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';REPO=R.parents[2];sys.path.insert(0,str(R));from checkpoint_chunks import restore
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();m=read(E/'artifact-manifest.json');assert m['actualCompletedUpdates']==10000 and m['semanticAssessmentComplete']and not m['adopted'];require_tracked='--require-tracked'in sys.argv;tracked=set(subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().split('\0'))if require_tracked else set()
def track(p):
 assert p.resolve().is_relative_to(REPO.resolve()),str(p)
 if require_tracked:assert str(p.resolve().relative_to(REPO.resolve()))in tracked,'Untracked required artifact: '+str(p)
def materialize(p,expected):
 adjacent=p.with_name(p.name+'.chunks.json')
 if not p.exists():
  if not adjacent.exists():raise ValueError('Missing artifact without lossless parts: '+str(p))
  restore(adjacent)
 assert sha(p)==expected,str(p)
 if require_tracked and str(p.resolve().relative_to(REPO.resolve()))not in tracked:
  assert adjacent.exists(),'Untracked raw input without tracked parts: '+str(p);a=read(adjacent);assert a['sha256']==expected;track(adjacent)
  for c in a['chunks']:q=adjacent.parent/c['path'];track(q);assert q.stat().st_size==c['bytes']and sha(q)==c['sha256']
for f in m['files']:
 p=R/f['path'];assert p.stat().st_size==f['bytes']and sha(p)==f['sha256'],f['path'];track(p)
for f in m['inputs']:materialize(R/f['path'],f['sha256']);assert (R/f['path']).stat().st_size==f['bytes']
for f in m['assembledCheckpoints']+m['assembledData']:
 p=R/f['path'];mp=R/f['chunksManifest'];a=read(mp);assert a['sha256']==f['sha256']and a['bytes']==f['bytes'];track(mp);h=hashlib.sha256();size=0
 for c in a['chunks']:
  q=mp.parent/c['path'];track(q);b=q.read_bytes();assert len(b)==c['bytes']and hashlib.sha256(b).hexdigest()==c['sha256'];h.update(b);size+=len(b)
 assert size==f['bytes']and h.hexdigest()==f['sha256'];materialize(p,f['sha256'])
import torch
torch.set_num_threads(1)
for f in m['assembledCheckpoints']:
 cp=torch.load(R/f['path'],map_location='cpu',weights_only=False);assert cp['step']==f['actualSnapshotUpdates'];assert sorted({int(v['step'])for v in cp['optimizer']['state'].values()})==[f['optimizerCounter']];assert all(torch.isfinite(v).all()for v in cp['model'].values());assert all(torch.isfinite(v[k]).all()for v in cp['optimizer']['state'].values()for k in ['exp_avg','exp_avg_sq']);rng=random.Random();rng.setstate(cp['pythonRng']);assert rng.getstate()==cp['pythonRng'];torch.set_rng_state(cp['torchRng']);assert torch.equal(torch.get_rng_state(),cp['torchRng'])
 if f['role']=='selected':assert cp['beststep']==cp['step']==9500 and all(torch.equal(v,cp['beststate'][k])for k,v in cp['model'].items())
 if f['role']=='latest':assert cp['step']==10000 and cp['beststep']==9500
policy=read(R/'policy.json')
for n in policy['codeHashes']:assert sha(R/n)==policy['codeHashes'][n]and(R/n).read_bytes()==(R.parent/'round37'/n).read_bytes()
assert sha(E/'final-assessment.json')==m['finalAssessmentSha256'];assert sha(E/'ALL_FOUR_STATE_GENERATIONS.md')==m['fullTextAssemblySha256'];assert read(E/'all-new-reading-consistency.json')['uniqueNewPrefixFullTextPairs']==79;assert read(E/'final-numerical-verification.json')['newPythonJavascriptFullSequenceMatches']==84
if require_tracked:
 track(E/'artifact-manifest.json');assert not subprocess.check_output(['git','diff','--name-only','--',str(R.relative_to(REPO))],cwd=REPO,text=True).strip(),'Unstaged tracked experiment changes remain'
print(json.dumps(dict(actualCompletedUpdates=10000,filesVerified=len(m['files']),frozenInputsVerified=len(m['inputs']),fullAlignedModelOptimizerRngStatesVerified=len(m['assembledCheckpoints']),allLosslessPartsVerified=True,trackingClosureVerified=require_tracked,publicChanged=False,testGenerated=False)))
