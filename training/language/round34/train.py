"""Reproducible raw causal pretraining only, with atomic optimizer checkpoints.
Never reads QA records/test text/teacher outputs or pretrained files.
"""
import argparse,copy,hashlib,json,math,pathlib,random,signal,time,shutil
import numpy as np
import torch
from torch.nn import functional as F
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from model import Decoder
from batching import sampler,draw
ROOT=pathlib.Path(__file__).resolve().parent
PARENT=ROOT.parent/'round10'
from initialization import initialize
from objective import causal_unlikelihood
from sequence_objective import rollout_unlikelihood
from rollout_trace import reconcile_trace, append_trace
from prefix_selection import load_selector

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def load_partition(directory,name):
    info=read(directory/f'{name}.index.json');path=directory/f'{name}.tokens.bin'
    if sha(path)!=info['tokensSha256']:raise ValueError('Source token stream changed')
    return info,np.memmap(path,dtype='<u4',mode='r')
def pack(rows,values,context):
    x=torch.zeros((len(rows),context),dtype=torch.long);y=torch.full_like(x,-100)
    for i,r in enumerate(rows):
        t=torch.from_numpy(np.array(values[r['offset']:r['offset']+r['length']],dtype=np.int64))
        x[i,:len(t)-1]=t[:-1];y[i,:len(t)-1]=t[1:];y[i,:r['prefixLength']-1]=-100
    return x,y
@torch.no_grad()
def measure(model,info,values,batch=8):
    model.eval();total=0.;targets=0;sites={}
    # Group by source site so totals remain interpretable across genres.
    for site in sorted({r['site'] for r in info['rows']}):
        rows=[r for r in info['rows'] if r['site']==site];loss=0.;count=0
        for start in range(0,len(rows),batch):
            x,y=pack(rows[start:start+batch],values,model.config['context'])
            loss+=F.cross_entropy(model(x).reshape(-1,model.config['vocabulary']),y.reshape(-1),reduction='sum').item();count+=int(y.ne(-100).sum())
        bytecount=sum(d['utf8Bytes'] for d in info['documents'] if d['site']==site)
        sites[site]=dict(lossSum=loss,tokens=count,utf8Bytes=bytecount,tokenLoss=loss/count,tokenPerplexity=math.exp(loss/count),nllPerUtf8Byte=loss/bytecount)
        total+=loss;targets+=count
    bytecount=sum(d['utf8Bytes'] for d in info['documents'])
    return dict(lossSum=total,tokens=targets,utf8Bytes=bytecount,tokenLoss=total/targets,tokenPerplexity=math.exp(total/targets),nllPerUtf8Byte=total/bytecount,sites=sites)
@torch.no_grad()
def measure_views(model,info,values,batch=8):
    views={}
    for variant in range(3):
        subset={key:[r for r in info[key] if r['variant']==variant] for key in ['rows','documents']}
        views[str(variant)]=measure(model,subset,values,batch)
    value=sum(weight*views[str(variant)]['nllPerUtf8Byte'] for variant,weight in [(0,.4),(1,.3),(2,.3)])
    return dict(nllPerUtf8Byte=value,views=views,metric='Weighted segmentation diagnostic; not probability of independent text')

def export_model(model,state,tokenizer,config,training,path):
    exported=dict(version='2026-10-08.raw-multiview-'+str(training['wordMerges'])+'-'+str(config['layers'])+'layers-'+str(training['parameters'])+'-'+str(training['completedSteps']),config=config,tokenizer=tokenizer,training=training,tensors={k:dict(shape=list(t.shape),data=[round(float(v),7) for v in t.flatten()]) for k,t in state.items()})
    path.write_text('export const dialogueModel='+json.dumps(exported,ensure_ascii=False,separators=(',',':'))+';\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--merges',type=int,required=True);parser.add_argument('--steps',type=int,required=True);parser.add_argument('--dim',type=int,default=128);parser.add_argument('--layers',type=int,default=3);parser.add_argument('--heads',type=int,default=4);parser.add_argument('--batch',type=int,default=8);parser.add_argument('--threads',type=int,default=2);parser.add_argument('--seed',type=int,default=429);parser.add_argument('--lr',type=float,default=.0005);parser.add_argument('--validation-every',type=int,default=500);parser.add_argument('--run',required=True);parser.add_argument('--compile',action='store_true');parser.add_argument('--resume',action='store_true');parser.add_argument('--ancestor');parser.add_argument('--pause-after',type=int);parser.add_argument('--precision',choices=['float32','bfloat16'],default='float32');args=parser.parse_args()
    if args.steps<1 or args.dim%args.heads:parser.error('Invalid updates/head dimensions')
    if args.pause_after is not None and not 0<args.pause_after<args.steps:parser.error('Invalid operational pause point')
    policy=read(ROOT/'policy.json')
    for row in read(ROOT/'source-manifest.json')['files']:
        if sha(ROOT/row['path'])!=row['sha256']:raise ValueError('Frozen experiment artifact changed: '+row['path'])
    if args.steps!=10000 or args.seed!=2049 or args.merges!=512 or args.dim!=192 or args.layers!=8 or args.heads!=4 or args.lr!=policy['learningRate'] or args.ancestor or args.batch!=8 or args.threads!=2 or args.validation_every!=500 or args.compile or args.precision!='float32':
        parser.error('Frozen multiview study differs')
    if pathlib.Path(args.run).name!=args.run:parser.error('Run must be a new local directory name')
    if (ROOT/args.run/'checkpoint.pt').exists() and not args.resume:parser.error('Existing checkpoints require an exact-identity resume')
    torch.set_num_threads(args.threads);torch.manual_seed(args.seed);torch.use_deterministic_algorithms(True);rng=random.Random(args.seed)
    directory=ROOT/'multiview';data=read(directory/'data.json');tok=read(directory/'tokenizer.json')
    for file, expected in policy['codeHashes'].items():
        if sha(ROOT/file)!=expected:raise ValueError('Frozen code changed: '+file)
    for file, expected in policy['sourceHashes'].items():
        if sha(PARENT/file)!=expected:raise ValueError('Frozen source changed: '+file)
    if sha(directory/'tokenizer.json')!=data['tokenizerSha256'] or policy['preparedPolicySha256']!=data['policySha256']:raise ValueError('Prepared data identity changed')
    config=dict(vocabulary=len(tok['bytes']),dim=args.dim,layers=args.layers,heads=args.heads,hidden=args.dim*4,context=256,dropout=.1,epsilon=1e-5)
    model=Decoder(config);initialization=initialize(model,tok,args.ancestor);optimizer=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=.05)
    parent_state=torch.load(ROOT.parent/'round28/continue-10000/checkpoint.pt',map_location='cpu',weights_only=False)
    optimizer.load_state_dict(parent_state['optimizer']);torch.set_rng_state(parent_state['torchRng']);rng.setstate(parent_state['pythonRng'])
    train,train_values=load_partition(directory,'train');valid,valid_values=load_partition(directory,'validation')
    prefix_selector=load_selector(ROOT/'human-turn-token-boundaries.json',tok,train,policy['humanNegativePrefix']['featureMapSha256'],sha(directory/'tokenizer.json'),sha(directory/'train.index.json'),sha(ROOT/'sources/documents.jsonl'),min_tokens=8,max_tokens=32)
    bysite={s:[r for r in train['rows'] if r['site']==s] for s in sorted({r['site'] for r in train['rows']})}
    out=ROOT/args.run;out.mkdir(exist_ok=True);checkpoint=out/'checkpoint.pt'
    settings=vars(args).copy();settings.pop('resume');settings.pop('pause_after');settings['sourceSha256']=data['sourceSha256'];settings['splitSha256']=data['splitSha256'];settings['tokenizerSha256']=data['tokenizerSha256'];settings['genreSampling']=policy['genreSampling']
    settings['newSourceManifestSha256']=policy['newSourceManifestSha256'];settings['newSourceDocumentsSha256']=policy['newSourceDocumentsSha256'];settings['rawUnitsSha256']=sha(PARENT/'units.json');settings['wordMerges']=args.merges
    settings['preparedDataSha256']=sha(directory/'data.json');settings['trainingViews']={'canonical':.4,'glyph':.3,'randomCharacterCuts':.3}
    settings['validationViews']={'canonical':.4,'glyph':.3,'randomCharacterCuts':.3}
    settings['objective']='CE + 0.1 self-generated repeated-fourgram UL every10updates + 1.0 causal repeated-fourgram completion unlikelihood within past64 completion positions on unique non-special candidates excluding the true next token; same raw targets'
    settings['unlikelihood']=policy['unlikelihood']
    settings['sequenceUnlikelihood']=policy['sequenceUnlikelihood']
    settings['externalWeights']=False;settings['externalTokenizer']=False;settings['externalInferenceAPI']=False;settings.update(initialization)
    settings['experimentPolicySha256']=sha(ROOT/'policy.json');settings['savedComparisonSnapshotStep']=0;settings['schedule']='Continue exact Round28 terminal LR throughout additional10000; preserve latest aligned model, moments and RNG, no restart'
    settings['validationStatus']='Previously exposed development sources; not independent unseen validation'
    strata,stratum_weights,bucket_masses=sampler(train['rows'],settings['genreSampling'])
    settings['lengthBucketMasses']={str(k):v for k,v in bucket_masses.items()};settings['batching']='Conditional length buckets64/128/256; same marginal row probabilities, correlated batch lengths; no target truncation. Different update trajectory from unbucketed pilots.'
    settings['trainerSourceSha256']=sha(pathlib.Path(__file__))
    startstep=0;history=[];bestloss=float('inf');beststep=0;beststate=None;elapsed_offset=0.;seen_tokens=0;seen_bytes=0;rollout_calls=0;rollout_generated=0;rollout_negative=0
    if args.resume:
        saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
        if saved['settings']!=settings or saved['config']!=config:raise ValueError('Resume identity mismatch')
        model.load_state_dict(saved['model']);optimizer.load_state_dict(saved['optimizer']);torch.set_rng_state(saved['torchRng']);rng.setstate(saved['pythonRng']);startstep=saved['step'];history=saved['history'];bestloss=saved['bestloss'];beststep=saved['beststep'];beststate=saved['beststate'];elapsed_offset=saved['elapsed'];seen_tokens=saved['seen_tokens'];seen_bytes=saved['seen_bytes'];rollout_calls=saved['rolloutCalls'];rollout_generated=saved['rolloutGeneratedTokens'];rollout_negative=saved['rolloutNegativePositions']
    reconcile_trace(out/'training-rollouts.jsonl',startstep,rollout_calls,rollout_generated,rollout_negative)
    write(out/'config.json',dict(config=config,settings=settings,parameters=sum(p.numel() for p in model.parameters()),selection='Lowest predeclared weighted development segmentation NLL/byte; test not read'))
    interrupted=[False]
    def stop(signum,frame):interrupted[0]=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    begun=time.monotonic()
    def elapsed():return elapsed_offset+time.monotonic()-begun
    def save(step):
        temporary=checkpoint.with_suffix('.tmp')
        torch.save(dict(schemaVersion=1,settings=settings,config=config,step=step,model=model.state_dict(),optimizer=optimizer.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate(),history=history,bestloss=bestloss,beststep=beststep,beststate=beststate,elapsed=elapsed(),seen_tokens=seen_tokens,seen_bytes=seen_bytes,rolloutCalls=rollout_calls,rolloutGeneratedTokens=rollout_generated,rolloutNegativePositions=rollout_negative),temporary);temporary.replace(checkpoint)
        if step==0:
            snapshot=out/'checkpoint-0.pt';temporary=out/'checkpoint-0.tmp';shutil.copyfile(checkpoint,temporary);temporary.replace(snapshot)
    def report(row):history.append(row);print(json.dumps(row),flush=True);write(out/'metrics.json',dict(config=config,settings=settings,history=history,bestStep=beststep,bestValidationNllPerByte=bestloss))
    if not args.resume:
        initial=measure_views(model,valid,valid_values,args.batch);bestloss=initial['nllPerUtf8Byte'];beststate=copy.deepcopy(model.state_dict());report(dict(step=0,validation=initial,elapsedSeconds=round(elapsed(),2)));save(0)
    def objective(x,y):
        with torch.autocast('cpu',dtype=torch.bfloat16,enabled=args.precision=='bfloat16'):
            logits=model(x)
            ce=F.cross_entropy(logits.reshape(-1,config['vocabulary']),y.reshape(-1))
            ul,count=causal_unlikelihood(logits,x,y,window=64)
            return ce+1.0*ul,ce.detach(),ul.detach(),count
    train_objective=torch.compile(objective,dynamic=False) if args.compile else objective
    byte_lengths=torch.tensor([len(bytes.fromhex(p)) for p in tok['bytes']],dtype=torch.long)
    lastloss=None;laststep=startstep
    for step in range(startstep+1,args.steps+1):
        width,rows=draw(rng,args.batch,strata,stratum_weights,bucket_masses)
        x,y=pack(rows,train_values,width);model.train();optimizer.zero_grad(set_to_none=True)
        for group in optimizer.param_groups:group['lr']=args.lr
        loss,ce_loss,ul_loss,negative_count=train_objective(x,y)
        sequence_loss=loss.detach().new_zeros(());sequence_record=None
        if step%policy['sequenceUnlikelihood']['everyUpdates']==0:
            prefix_length=prefix_selector.length(rows[0],int(x[0,0]))
            prefix=x[:1,:prefix_length]
            sequence_loss,sequence_record=rollout_unlikelihood(model,prefix,max_new_tokens=64,eos=2,window=64)
            loss=loss+policy['sequenceUnlikelihood']['coefficient']*sequence_loss
        if not torch.isfinite(loss):raise ValueError('Non-finite objective')
        loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step();laststep=step;lastloss=float(loss.detach())
        if sequence_record is not None:
            rollout_calls+=1;rollout_generated+=sequence_record['generatedTokens'];rollout_negative+=sequence_record['negativePositions']
            append_trace(out/'training-rollouts.jsonl',step,rows[0],sequence_loss,sequence_record)
        targets=y[y!=-100];seen_tokens+=len(targets);seen_bytes+=int(byte_lengths[targets].sum())
        if step%args.validation_every==0 or step==args.steps:
            metric=measure_views(model,valid,valid_values,args.batch)
            if metric['nllPerUtf8Byte']<bestloss:bestloss=metric['nllPerUtf8Byte'];beststep=step;beststate=copy.deepcopy(model.state_dict())
            report(dict(step=step,trainingLoss=lastloss,crossEntropyLoss=float(ce_loss),unlikelihoodLoss=float(ul_loss),negativeCandidates=negative_count,sequenceUnlikelihoodLoss=float(sequence_loss.detach()),rolloutCalls=rollout_calls,rolloutGeneratedTokens=rollout_generated,rolloutNegativePositions=rollout_negative,validation=metric,seenTargetTokens=seen_tokens,seenTargetUtf8Bytes=seen_bytes,elapsedSeconds=round(elapsed(),2),learningRate=optimizer.param_groups[0]['lr']));save(step)
        elif step%100==0:
            save(step)
            print(json.dumps(dict(event='updates',step=step,trainingLoss=lastloss,crossEntropyLoss=float(ce_loss),unlikelihoodLoss=float(ul_loss),negativeCandidates=negative_count,sequenceUnlikelihoodLoss=float(sequence_loss.detach()),rolloutCalls=rollout_calls,rolloutGeneratedTokens=rollout_generated,rolloutNegativePositions=rollout_negative,elapsedSeconds=round(elapsed(),2))),flush=True)
        if interrupted[0] or (args.pause_after is not None and step>=args.pause_after):save(step);print(json.dumps(dict(event='interrupted' if interrupted[0] else 'planned-pause',confirmedUpdates=step)),flush=True);break
    save(laststep)
    training=dict(**settings,completedRun=laststep==args.steps,completedSteps=laststep,requestedSteps=args.steps,bestStep=beststep,parameters=sum(p.numel() for p in model.parameters()),seenTargetTokens=seen_tokens,seenTargetUtf8Bytes=seen_bytes,rolloutCalls=rollout_calls,rolloutGeneratedTokens=rollout_generated,rolloutNegativePositions=rollout_negative,checkpointSha256=sha(checkpoint),selection='Lowest weighted development segmentation NLL/byte; test untouched',history=history)
    export_model(model,beststate,tok,config,training,out/'model.js');write(out/'result.json',training)
    print(json.dumps(dict(event='finished' if laststep==args.steps else 'suspended',completedUpdates=laststep,bestStep=beststep,bestValidationNllPerByte=bestloss,parameters=training['parameters'],elapsedSeconds=round(elapsed(),2))),flush=True)
if __name__=='__main__':main()
