"""Read-only original-positive EOS exposure, no checkpoint/model/heldout read."""
import pathlib,json,sys,collections,numpy as np
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));from batching import sampler
read=lambda p:json.loads(p.read_text());info=read(R/'multiview/train.index.json');p=read(R/'policy.json');values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');strata,weights,masses=sampler(info['rows'],p['genreSampling']);sites=collections.defaultdict(lambda:dict(mass=0.,expectedTargetsPerWindow=0.,expectedEosPerWindow=0.));targets=eos=0.
for key,rows in strata.items():
 prob=weights[key]/len(rows)
 for row in rows:
  count=row['length']-row['prefixLength'];end=row['offset']+row['length'];has_eos=int(values[end-1])==2
  # Original-data preflight established no interior specials and complete target coverage.
  targets+=prob*count;eos+=prob*has_eos;d=sites[key[0]];d['mass']+=prob;d['expectedTargetsPerWindow']+=prob*count;d['expectedEosPerWindow']+=prob*has_eos
out=dict(positiveCorpus='byte-identical adopted Round25',expectedTargetsPerWindow=targets,expectedEosTargetsPerWindow=eos,expectedEosFractionOfPositiveTargets=eos/targets,expectedEosTargetsIn80000Windows=80000*eos,sites=dict(sites),exactSamplingMarginal=True,realizedCounts=False,wholeRawUnitsNotConversationalTurnEnds=True,notProofOfTerminationCause=True,additionalOptimizerUpdates=0,trainingNotChanged=True,noHeldoutRead=True)
(R/'execution/eos-exposure-diagnostic.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='sites'}))
