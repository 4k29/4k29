"""Exposed human DEV context sensitivity, no generated answers/learning/TEST.
Prepare and commit reference/protocol before measuring. No inference output changes.
"""
import argparse,gzip,hashlib,json,pathlib,sys
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';read=lambda p:json.loads(p.read_text());sha=lambda b:hashlib.sha256(b).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--after',action='store_true');a=p.parse_args()
sys.path.insert(0,str(R.parent/'round10'));import evaluate as ev
ev.torch.set_num_threads(1);probes=read(E/'content-native-dev/probes.json');tok=read(R/'multiview/tokenizer.json');meta=json.loads(gzip.decompress((R.parent/'round28/prospective-daily-source/human-source-acquisition.json.gz').read_bytes()));dev={d['sourcePath']:d for d in meta['records'] if d['fold']=='development'};samples=[]
for row in probes['probes']:
 assert row['sourcePath'] in dev and row['sourceSha256']==dev[row['sourcePath']]['sha256']
 raw=(pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw/development')/pathlib.PurePosixPath(row['sourcePath']).name).read_bytes();assert sha(raw)==row['sourceSha256'];dialogue=json.loads(raw);turns=dialogue['utterances'];end=row['utteranceEndInclusive'];prefix='\n'.join(u['text'] for u in turns[row['utteranceStart']:end+1])+'\n';assert prefix==row['prefix']
 assert end+1<len(turns),'No resampling allowed: frozen source has no next utterance'
 target=turns[end+1]['text'];ids=ev.encode_stream(target,tok)[:64];x=[ev.SPECIALS['bos']]+ev.encode_stream(prefix,tok);assert len(x)==row['prefixTokens'] and ids
 samples.append(dict(id=row['id'],sourcePath=row['sourcePath'],sourceSha256=row['sourceSha256'],prefix=prefix,prefixTokens=x,targetUtteranceIndex=end+1,targetText=target,targetTextSha256=sha(target.encode()),targetTokens=ids,targetTruncatedTo64=len(ev.encode_stream(target,tok))>64))
assert len(samples)==8
plan=dict(scope='Previously exposed original human DEV only; no fresh TEST',selection='Same8 native source contexts without resampling; actual next original human utterance, first at most64 own canonical tokens. Cyclic next context in frozen ID order is donor. No EOS target.',tokenizerSha256=sha((R/'multiview/tokenizer.json').read_bytes()),probeSha256=sha((E/'content-native-dev/probes.json').read_bytes()),prefixAndTargetEncoding='Own encode_stream separately, same raw input tokenization as free generation. This forces a boundary and may differ from joint-source BPE; both true/swapped arms use identical target token IDs.',donorMapping={s['id']:samples[(j+1)%8]['id'] for j,s in enumerate(samples)},metrics=['firstToken','first8','laterThan8IfAny','allTargets'],notUsedForCheckpointSelection=True,additionalOptimizerUpdates=0,originalStrictGatesUnchanged=True,sourceLicense='CC-BY-SA-4.0; same original sources/attribution/license as content-native-dev/README.md',limits='Different donor lengths/lexicon/topic and artificial context joins confound lexical/syntactic/style versus discourse meaning. Small exposed DEV; teacher forcing is not autoregressive meaning or unseen generalization.',samples=samples)
f=E/'daily-conditioning-plan.json'
if a.prepare:
 assert not f.exists();f.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n');print('Plan prepared; commit before measuring. No model instantiated.');raise SystemExit
assert read(f)==plan
sys.path.insert(0,str(R));import train as t
models=[('initialOwnParent',R.parent/'round11/continue-10000/checkpoint.pt','model'),('round25',R.parent/'round25/continue-10000/checkpoint.pt','beststate'),('round29',R.parent/'round29/continue-10000/checkpoint.pt','beststate'),('round31',R.parent/'round31/continue-10000/checkpoint.pt','beststate')]
if a.after:models.append(('round32',R/'continue-10000/checkpoint.pt','beststate'))
out={}
for name,path,key in models:
 cp=ev.torch.load(path,map_location='cpu',weights_only=False)
 if name=='round32':assert cp['step']==10000
 m=t.Decoder(cp['config']);m.load_state_dict(cp[key]);m.eval();rows=[]
 for j,sample in enumerate(samples):
  target=sample['targetTokens'];scores={}
  for label,prefix in [('trueContext',sample['prefixTokens']),('otherDialogueContext',samples[(j+1)%8]['prefixTokens'])]:
   seq=prefix+target;assert len(seq)<=256
   with ev.torch.no_grad():z=m(ev.torch.tensor([seq[:-1]]))[0,len(prefix)-1:];loss=ev.torch.nn.functional.cross_entropy(z,ev.torch.tensor(target),reduction='none')
   scores[label]=dict(firstToken=float(loss[0]),first8=float(loss[:8].mean()),laterThan8IfAny=float(loss[8:].mean()) if len(loss)>8 else None,allTargets=float(loss.mean()))
  rows.append(dict(id=sample['id'],targetTokens=len(target),**scores))
 summary={label:{metric:sum(r[label][metric] for r in rows if r[label][metric] is not None)/sum(r[label][metric] is not None for r in rows) for metric in plan['metrics']}for label in ['trueContext','otherDialogueContext']}
 out[name]=dict(checkpointSha256=sha(path.read_bytes()),actualStep=cp['step'],selectedStep=cp['beststep'] if key=='beststate' else cp['step'],rows=rows,unweightedMeanOfPerResponseTokenNll=summary);del m,cp
record=dict(planSha256=sha(f.read_bytes()),auditorSha256=sha(pathlib.Path(__file__).read_bytes()),models=out,additionalOptimizerUpdates=0,noTestRead=True,notUsedForSelection=True,noSemanticClaim=True)
(E/'daily-conditioning-results.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v['unweightedMeanOfPerResponseTokenNll'] for k,v in out.items()}))
