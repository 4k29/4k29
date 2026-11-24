"""Post-training TRAIN-source exposure and literal film-word diagnostic, no model."""
import pathlib,json,hashlib,collections,sys,statistics
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round37';sys.path.insert(0,str(R));from train import torch,np,random,load_partition,sampler,draw,read,write,sha
torch.set_num_threads(1);cp=torch.load(R/'continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);zero=torch.load(R/'continue-10000/checkpoint-0.pt',map_location='cpu',weights_only=False);assert cp['step']==10000;info,v=load_partition(R/'multiview','train');strata,weights,masses=sampler(info['rows'],read(R/'policy.json')['genreSampling']);rng=random.Random();rng.setstate(zero['pythonRng']);lengths=np.array([len(bytes.fromhex(s))for s in read(R/'multiview/tokenizer.json')['bytes']],dtype=np.int64);counts=collections.defaultdict(collections.Counter);units=collections.defaultdict(set);windows=collections.defaultdict(set)
for step in range(1,10001):
 _,rows=draw(rng,8,strata,weights,masses)
 for row in rows:
  source='jmrd'if row['document'].startswith('jmrd:')else'realpersona'if row['document'].startswith('realpersona:')else row['site'];targets=v[row['offset']+row['prefixLength']:row['offset']+row['length']];counts[source]['sampledRows']+=1;counts[source]['targetTokens']+=len(targets);counts[source]['targetUtf8Bytes']+=int(lengths[targets].sum());units[source].add(row['document']);windows[source].add((row['unit'],row['start']))
assert rng.getstate()==cp['pythonRng'];assert sum(x['targetTokens']for x in counts.values())==cp['seen_tokens'];assert sum(x['targetUtf8Bytes']for x in counts.values())==cp['seen_bytes']
for s,c in counts.items():c['uniqueSourceUnitsTouched']=len(units[s]);c['uniqueVariantWindowsTouched']=len(windows[s])
paths={'daily12':'daily-new-python.json','native8':'content-native-dev/new-python.json','mrmp5':'fixed-source-mrmp-dev/new-python.json'};film=[];film_counts={}
for round_name,root in [('round37',P),('round38',R)]:
 for state in ['selected','terminal']:
  n=0
  for group,p in paths.items():
   gp=root/'execution'/p if state=='selected'else root/'execution/terminal-state-diagnostic'/f'{group}-python.json'
   for row in read(gp)['rows']:
    if '映画'in row['text']:
     n+=1;film.append(dict(round=round_name,state=state,group=group,id=row['id'],prefix=row['prefix'],fullText=row['text'],generationSha256=sha(gp)))
  film_counts[f'{round_name}/{state}']=n
paired=read(E/'daily-human-likelihood-comparison.json')['rows'];deltas=[r['newMinusOldLossSum']/r['serializedUtf8Bytes']for r in paired]
report=dict(actualCompletedUpdates=10000,privateSamplerRngAndPositiveCountsVerified=True,bySource={s:dict(c)for s,c in counts.items()},allSampledRows=80000,corpusAdditionNaturallyDilutesExistingRealPersonaExposure=True,uniqueTouchedDoesNotMeanAllTargetsWithinUnitSeen=True,literalFilmWordScope='Posthoc descriptive literal 映画 in generated text of25 fixed daily/native/source inputs per state; not a gate or complete topic/error classifier',literalFilmWordCounts=film_counts,literalFilmWordCases=film,humanDev99DescriptivePaired=dict(documents=99,newNllHigher=sum(d>0 for d in deltas),newNllLower=sum(d<0 for d in deltas),medianPerDocumentNllDelta=statistics.median(deltas),oneExactDuplicatePairAndRepeatedSpeakerTopicsNotIndependent=True,noPopulationSignificanceClaim=True),noGenerationOrOptimizer=True,additionalOptimizerUpdates=0,codeSha256=sha(pathlib.Path(__file__)))
write(E/'added-source-exposure-and-topic.json',report);print(json.dumps({k:v for k,v in report.items()if k not in ['literalFilmWordCases','bySource']}));print(json.dumps({k:dict(counts[k])for k in ['realpersona','jmrd']}))
