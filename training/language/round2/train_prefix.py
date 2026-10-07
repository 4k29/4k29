"""Reproducible raw causal pretraining only, with atomic optimizer checkpoints.
Never reads QA records/test text/teacher outputs or pretrained files.
"""
import argparse,copy,hashlib,json,math,pathlib,random,signal,time
import numpy as np
import torch
from torch.nn import functional as F
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from model import Decoder
from prefix_batching import sampler,draw
ROOT=pathlib.Path(__file__).resolve().parent

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
def export_model(model,state,tokenizer,config,training,path):
    exported=dict(version='2026-10-07.raw-prefix-japanese-'+str(training['parameters'])+'-'+str(training['completedSteps']),config=config,tokenizer=tokenizer,training=training,tensors={k:dict(shape=list(t.shape),data=[round(float(v),7) for v in t.flatten()]) for k,t in state.items()})
    path.write_text('export const dialogueModel='+json.dumps(exported,ensure_ascii=False,separators=(',',':'))+';\n')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--merges',type=int,required=True);parser.add_argument('--steps',type=int,required=True);parser.add_argument('--dim',type=int,default=128);parser.add_argument('--layers',type=int,default=3);parser.add_argument('--heads',type=int,default=4);parser.add_argument('--batch',type=int,default=8);parser.add_argument('--threads',type=int,default=2);parser.add_argument('--seed',type=int,default=429);parser.add_argument('--lr',type=float,default=.0005);parser.add_argument('--validation-every',type=int,default=500);parser.add_argument('--run',required=True);parser.add_argument('--compile',action='store_true');parser.add_argument('--resume',action='store_true');parser.add_argument('--parent',type=pathlib.Path,required=True);parser.add_argument('--precision',choices=['float32','bfloat16'],default='float32');args=parser.parse_args()
    if args.steps<1 or args.dim%args.heads:parser.error('Invalid updates/head dimensions')
    torch.set_num_threads(args.threads);torch.manual_seed(args.seed);torch.use_deterministic_algorithms(True);rng=random.Random(args.seed)
    directory=ROOT/f'prefix-bpe-{args.merges}';data=read(directory/'data.json');tok=read(directory/'tokenizer.json')
    if sha(ROOT/'documents.jsonl')!=data['sourceSha256'] or sha(ROOT/'split.json')!=data['splitSha256'] or sha(directory/'tokenizer.json')!=data['tokenizerSha256']:raise ValueError('Frozen data or tokenizer identity changed')
    config=dict(vocabulary=len(tok['bytes']),dim=args.dim,layers=args.layers,heads=args.heads,hidden=args.dim*4,context=256,dropout=.1,epsilon=1e-5)
    if args.parent.resolve()!=(ROOT/'raw-modern-million/checkpoint.pt').resolve():raise ValueError('Only this own raw parent is allowed')
    parent=torch.load(args.parent,map_location='cpu',weights_only=False)
    if parent['step']!=parent['settings']['steps'] or parent['step']!=10000:raise ValueError('Own raw parent must complete its actual10000 updates')
    if parent['config']!=config or parent['settings']['sourceSha256']!=data['sourceSha256'] or parent['settings']['tokenizerSha256']!=data['tokenizerSha256'] or parent['settings']['externalWeights']:raise ValueError('Own raw parent identity mismatch')
    model=Decoder(config);model.load_state_dict(parent['beststate']);optimizer=torch.optim.AdamW(model.parameters(),lr=args.lr,weight_decay=.05)
    train,train_values=load_partition(directory,'train');valid,valid_values=load_partition(directory,'validation')
    bysite={s:[r for r in train['rows'] if r['site']==s] for s in sorted({r['site'] for r in train['rows']})}
    byview={(site,p):[r for r in rows if r['variant']==p] for site,rows in bysite.items() for p in [0,.15,.3]}
    out=ROOT/args.run;out.mkdir(exist_ok=True);checkpoint=out/'checkpoint.pt'
    settings=vars(args).copy();settings.pop('resume');settings['parent']=str(args.parent);settings['sourceSha256']=data['sourceSha256'];settings['splitSha256']=data['splitSha256'];settings['tokenizerSha256']=data['tokenizerSha256'];settings['genreSampling']={'aozora':.3,'mic':.3,'env':.3,'mdn':.075,'jma':.0125,'maff':.0125}
    settings['paragraphSelectionsSha256']=data['paragraphSelectionsSha256'];settings['trainingViews']={'canonical':.5,'mergeDropout015':.1,'mergeDropout030':.1,'prefixCut':.3};settings['prefixCutsSha256']=data['prefixCutsSha256'];settings['parentCheckpointSha256']=sha(args.parent);settings['parentCompletedSteps']=parent['step'];settings['parentSelectedSteps']=parent['beststep'];settings['ownParentOnly']=True;settings['optimizerReset']=True;settings['seedReset']=True;settings['trainerAncestorSha256']=sha(ROOT.parent/'train.py');settings['objective']='Raw complete original paragraph causal next-token cross entropy; masked lookback, true boundary BOS/EOS; no QA, instruction tuning or teacher';settings['externalWeights']=False;settings['externalTokenizer']=False;settings['externalInferenceAPI']=False;settings['randomInitialization']=False;settings['ownRandomInitializedLineage']=True
    strata,stratum_weights,bucket_masses=sampler(train['rows'],settings['genreSampling'])
    settings['lengthBucketMasses']={str(k):v for k,v in bucket_masses.items()};settings['batching']='Conditional length buckets64/128/256; same marginal row probabilities, correlated batch lengths; no target truncation. Different update trajectory from unbucketed pilots.'
    settings['trainerSourceSha256']=sha(pathlib.Path(__file__))
    startstep=0;history=[];bestloss=float('inf');beststep=0;beststate=None;elapsed_offset=0.;seen_tokens=0;seen_bytes=0
    if args.resume:
        saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
        if saved['settings']!=settings or saved['config']!=config:raise ValueError('Resume identity mismatch')
        model.load_state_dict(saved['model']);optimizer.load_state_dict(saved['optimizer']);torch.set_rng_state(saved['torchRng']);rng.setstate(saved['pythonRng']);startstep=saved['step'];history=saved['history'];bestloss=saved['bestloss'];beststep=saved['beststep'];beststate=saved['beststate'];elapsed_offset=saved['elapsed'];seen_tokens=saved['seen_tokens'];seen_bytes=saved['seen_bytes']
    write(out/'config.json',dict(config=config,settings=settings,parameters=sum(p.numel() for p in model.parameters()),selection='Lowest full held-paragraph validation NLL/UTF8byte; own raw parent, fresh optimizer and RNG; TEST not read'))
    interrupted=[False]
    def stop(signum,frame):interrupted[0]=True
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGINT,stop)
    begun=time.monotonic()
    def elapsed():return elapsed_offset+time.monotonic()-begun
    def save(step):
        temporary=checkpoint.with_suffix('.tmp')
        torch.save(dict(schemaVersion=1,settings=settings,config=config,step=step,model=model.state_dict(),optimizer=optimizer.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate(),history=history,bestloss=bestloss,beststep=beststep,beststate=beststate,elapsed=elapsed(),seen_tokens=seen_tokens,seen_bytes=seen_bytes),temporary);temporary.replace(checkpoint)
    def report(row):history.append(row);print(json.dumps(row),flush=True);write(out/'metrics.json',dict(config=config,settings=settings,history=history,bestStep=beststep,bestValidationNllPerByte=bestloss))
    if not args.resume:
        initial=measure(model,valid,valid_values,args.batch);bestloss=initial['nllPerUtf8Byte'];beststate=copy.deepcopy(model.state_dict());report(dict(step=0,validation=initial,elapsedSeconds=round(elapsed(),2)));save(0)
    def objective(x,y):
        with torch.autocast('cpu',dtype=torch.bfloat16,enabled=args.precision=='bfloat16'):
            return F.cross_entropy(model(x).reshape(-1,config['vocabulary']),y.reshape(-1))
    train_objective=torch.compile(objective,dynamic=False) if args.compile else objective
    byte_lengths=torch.tensor([len(bytes.fromhex(p)) for p in tok['bytes']],dtype=torch.long)
    lastloss=None;laststep=startstep
    for step in range(startstep+1,args.steps+1):
        width,rows=draw(rng,args.batch,strata,stratum_weights,bucket_masses)
        x,y=pack(rows,train_values,width);model.train();optimizer.zero_grad(set_to_none=True)
        warmup=min(250,max(50,args.steps//10));schedule=step/warmup if step<=warmup else .15+.85*.5*(1+math.cos(math.pi*(step-warmup)/max(1,args.steps-warmup)))
        for group in optimizer.param_groups:group['lr']=args.lr*schedule
        loss=train_objective(x,y)
        if not torch.isfinite(loss):raise ValueError('Non-finite objective')
        loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step();laststep=step;lastloss=float(loss.detach())
        targets=y[y!=-100];seen_tokens+=len(targets);seen_bytes+=int(byte_lengths[targets].sum())
        if step%args.validation_every==0 or step==args.steps:
            metric=measure(model,valid,valid_values,args.batch)
            if metric['nllPerUtf8Byte']<bestloss:bestloss=metric['nllPerUtf8Byte'];beststep=step;beststate=copy.deepcopy(model.state_dict())
            report(dict(step=step,trainingLoss=lastloss,validation=metric,seenTargetTokens=seen_tokens,seenTargetUtf8Bytes=seen_bytes,elapsedSeconds=round(elapsed(),2),learningRate=optimizer.param_groups[0]['lr']));save(step)
        elif step%100==0:
            print(json.dumps(dict(event='updates',step=step,trainingLoss=lastloss,elapsedSeconds=round(elapsed(),2))),flush=True)
        if interrupted[0]:save(step);print(json.dumps(dict(event='interrupted',confirmedUpdates=step)),flush=True);break
    save(laststep)
    training=dict(**settings,completedRun=laststep==args.steps,completedSteps=laststep,requestedSteps=args.steps,bestStep=beststep,parameters=sum(p.numel() for p in model.parameters()),seenTargetTokens=seen_tokens,seenTargetUtf8Bytes=seen_bytes,checkpointSha256=sha(checkpoint),selection='Lowest full validation paragraph NLL per UTF8 byte; test untouched',history=history)
    export_model(model,beststate,tok,config,training,out/'model.js');write(out/'result.json',training)
    print(json.dumps(dict(event='finished' if laststep==args.steps else 'suspended',completedUpdates=laststep,bestStep=beststep,bestValidationNllPerByte=bestloss,parameters=training['parameters'],elapsedSeconds=round(elapsed(),2))),flush=True)
if __name__=='__main__':main()
