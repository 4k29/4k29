"""Independent sampler-only replay of the retained midpoint, no learning or generation."""
import pathlib,json,sys,hashlib,struct,collections
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from train import torch,random,np,load_partition,sampler,draw,read,write,sha
from utterance_end_objective import eligible_mask
from train import pack
torch.set_num_threads(1);cp_path=R/'execution/retained-snapshots/5000/checkpoint.pt';cp=torch.load(cp_path,map_location='cpu',weights_only=False);zero=torch.load(R/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);assert cp['step']==5000 and zero['step']==0;assert sorted({int(s['step'])for s in cp['optimizer']['state'].values()})==[25000]
info,values=load_partition(R/'multiview','train');strata,weights,masses=sampler(info['rows'],read(R/'policy.json')['genreSampling']);rng=random.Random();rng.setstate(zero['pythonRng']);vocab=read(R/'multiview/tokenizer.json')['bytes'];byte_lengths=np.array([len(bytes.fromhex(t))for t in vocab],dtype=np.int64);ends=read(R/'human-turn-token-boundaries.json')['boundariesByUnit'];counts=collections.Counter();seen_tokens=seen_bytes=eos_positions=eos_batches=0;trace=hashlib.sha256()
for step in range(1,5001):
 width,rows=draw(rng,8,strata,weights,masses);x,y=pack(rows,values,width);mask=eligible_mask(rows,y,ends);eos_positions+=int(mask.sum());eos_batches+=int(mask.any())
 for row in rows:
  targets=values[row['offset']+row['prefixLength']:row['offset']+row['length']];seen_tokens+=len(targets);seen_bytes+=int(byte_lengths[targets].sum());source='jmrd'if row['document'].startswith('jmrd:')else'realpersona'if row['document'].startswith('realpersona:')else row['site'];counts[source]+=1;trace.update(struct.pack('<QQQQQ',width,row['offset'],row['length'],row['prefixLength'],row['variant']))
assert rng.getstate()==cp['pythonRng'];assert seen_tokens==cp['seen_tokens']and seen_bytes==cp['seen_bytes'];assert eos_positions==cp['endEosPositions']and eos_batches==cp['endEosBatches'];assert sum(counts.values())==40000
report=dict(actualRetainedUpdates=5000,checkpointSha256=sha(cp_path),privatePythonRngExactlyReplayed=True,seenTargetTokens=seen_tokens,seenTargetUtf8Bytes=seen_bytes,ownPositiveCountsExactlyMatchCheckpoint=True,eligibleEosPositions=eos_positions,eligibleEosBatches=eos_batches,eosCountersExactlyMatchOwnReplay=True,bySourceSampledRows=dict(counts),sampledRows=40000,drawTraceSha256=trace.hexdigest(),controlDrawEqualityNotRequiredForCorpusAddition=True,additionalOptimizerUpdates=0,noModelForwardOrGeneration=True,codeSha256=sha(pathlib.Path(__file__)))
write(R/'execution/retained5000-sampler-replay.json',report);print(json.dumps(report))
