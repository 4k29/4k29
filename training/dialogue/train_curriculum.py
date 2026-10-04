"""Own raw-text pretraining then answer-only dialogue learning, from scratch.

CPU training, atomic restart checkpoints, source/config identity checks, and
validation-only checkpoint selection. No outside pretrained files are accepted.
"""
import argparse
import copy
import hashlib
import json
import math
import pathlib
import time
import torch
from torch.nn import functional as F
from train import DialogueDecoder,pack,generate
from tokenizer import SPECIALS

HERE=pathlib.Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--corpus',default=str(HERE/'generalization-corpus.json'))
    p.add_argument('--pretrain-steps',type=int,default=1000)
    p.add_argument('--steps',type=int,default=10000)
    p.add_argument('--dim',type=int,default=96)
    p.add_argument('--layers',type=int,default=3)
    p.add_argument('--batch-size',type=int,default=16)
    p.add_argument('--threads',type=int,default=1)
    p.add_argument('--seed',type=int,default=429)
    p.add_argument('--learning-rate',type=float,default=0.001)
    p.add_argument('--validation-every',type=int,default=1000)
    p.add_argument('--compile-loss',action='store_true')
    p.add_argument('--resume')
    p.add_argument('--checkpoint',default='/tmp/4k29-curriculum-checkpoint.pt')
    p.add_argument('--output',default=str(HERE/'generalization-candidate.js'))
    p.add_argument('--artifacts-prefix',default=str(HERE/'generalization'))
    p.add_argument('--version',default='2026-10-04.dialogue-curriculum-1')
    p.add_argument('--length-buckets',action='store_true')
    p.add_argument('--own-pretrained-checkpoint')
    p.add_argument('--replay-weight',type=float,default=0.0)
    args=p.parse_args()
    if args.replay_weight<0:p.error('Replay weight must be nonnegative')
    if args.own_pretrained_checkpoint and (args.resume or args.pretrain_steps):p.error('Own pretraining continuation needs --pretrain-steps 0 and cannot also resume')
    if args.pretrain_steps<0 or args.steps<1 or args.dim%4 or args.layers<1 or args.batch_size<1 or args.learning_rate<=0:p.error('Invalid training configuration')
    torch.set_num_threads(args.threads);torch.manual_seed(args.seed);torch.use_deterministic_algorithms(True)
    corpus=json.loads(pathlib.Path(args.corpus).read_text())
    train=[r for r in corpus['rows'] if r['partition']=='train']
    valid=[r for r in corpus['rows'] if r['partition']=='validation']
    config=dict(vocabulary=len(corpus['tokenizer']['bytes']),dim=args.dim,heads=4,hidden=args.dim*2,layers=args.layers,context=128,dropout=0.12,epsilon=1e-5)
    width=max(len(r['tokens'])-1 for r in train+valid+corpus['pretraining'])
    if width>=config['context']:raise ValueError('No truncation: sequence exceeds context')
    x,y=pack(train,SPECIALS['pad'],width);vx,vy=pack(valid,SPECIALS['pad'],width)
    raw=[dict(tokens=r['tokens'],prefixLength=1) for r in corpus['pretraining']]
    rx,ry=pack(raw,SPECIALS['pad'],width)
    raw_validation=[dict(tokens=r['tokens'],prefixLength=1) for r in corpus.get('pretrainingValidation',[])]
    rvx,rvy=pack(raw_validation,SPECIALS['pad'],width) if raw_validation else (None,None)
    weights=torch.tensor([r['weight'] for r in train])
    raw_width=max(len(r['tokens'])-1 for r in raw)
    bucket_widths=sorted({min(n,width) for n in [72,96,128]})
    bucket_indices=[];bucket_masses=[]
    for bucket_width in bucket_widths:
        previous=max([n for n in bucket_widths if n<bucket_width],default=0)
        index=torch.tensor([i for i,r in enumerate(train) if previous<len(r['tokens'])-1<=bucket_width],dtype=torch.long)
        bucket_indices.append(index);bucket_masses.append(weights[index].sum())
    bucket_masses=torch.stack(bucket_masses)
    model=DialogueDecoder(config)
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.learning_rate,weight_decay=0.03)
    def objective(tokens,targets):return F.cross_entropy(model(tokens).reshape(-1,config['vocabulary']),targets.reshape(-1),label_smoothing=0.01)
    compiled=torch.compile(objective,dynamic=False) if args.compile_loss else objective
    @torch.no_grad()
    def measure(tokens,targets):
        model.eval();total,count=0.0,0
        for start in range(0,len(tokens),32):
            labels=targets[start:start+32]
            total+=F.cross_entropy(model(tokens[start:start+32]).reshape(-1,config['vocabulary']),labels.reshape(-1),reduction='sum').item()
            count+=labels.ne(-100).sum().item()
        return total/count
    settings={k:getattr(args,k) for k in ['pretrain_steps','steps','dim','layers','batch_size','seed','learning_rate','validation_every','length_buckets','replay_weight']}
    resume=0;history=[];best=None;rank=(-1,float('-inf'));best_step=0;elapsed_before=0
    raw_best=None;raw_best_loss=float('inf');raw_best_step=0
    inherited_pretraining=0;own_parent=None
    if args.own_pretrained_checkpoint:
        parent=torch.load(args.own_pretrained_checkpoint,weights_only=False)
        if parent['sourceSha256']!=corpus['sourceSha256'] or parent.get('rawBest') is None:raise ValueError('Own pretraining/source lineage mismatch')
        for k in ['dim','layers','seed']:
            if parent['settings'][k]!=settings[k]:raise ValueError('Own pretraining config mismatch: '+k)
        raw_best=parent['rawBest'];raw_best_loss=parent['rawBestLoss'];raw_best_step=parent['rawBestStep']
        model.load_state_dict(raw_best);inherited_pretraining=raw_best_step
        own_parent=dict(sourceSha256=parent['sourceSha256'],selectedRawStep=raw_best_step,confirmedParentUpdates=parent['step'],checkpointSha256=hashlib.sha256(pathlib.Path(args.own_pretrained_checkpoint).read_bytes()).hexdigest())
    if args.resume:
        c=torch.load(args.resume,weights_only=False)
        previous_settings=dict(c['settings']);previous_settings.setdefault('length_buckets',False);previous_settings.setdefault('replay_weight',0.0)
        if c['sourceSha256']!=corpus['sourceSha256'] or previous_settings!=settings:raise ValueError('Resume dataset/config mismatch')
        model.load_state_dict(c['model']);optimizer.load_state_dict(c['optimizer']);torch.set_rng_state(c['rng'])
        resume=c['step'];history=c['history'];best=c['best'];rank=c['rank'];best_step=c['bestStep'];elapsed_before=c['elapsedSeconds']
        raw_best=c.get('rawBest');raw_best_loss=c.get('rawBestLoss',float('inf'));raw_best_step=c.get('rawBestStep',0)
        inherited_pretraining=c.get('inheritedPretraining',0);own_parent=c.get('ownParent')
    started=time.monotonic()
    initial_language_validation=c.get('initialLanguageValidationLoss') if args.resume else measure(rvx,rvy) if raw_validation else None
    total_steps=args.pretrain_steps+args.steps
    def save(step):
        dst=pathlib.Path(args.checkpoint);tmp=dst.with_suffix('.tmp')
        torch.save(dict(step=step,model=model.state_dict(),optimizer=optimizer.state_dict(),rng=torch.get_rng_state(),history=history,best=best,rank=rank,bestStep=best_step,rawBest=raw_best,rawBestLoss=raw_best_loss,rawBestStep=raw_best_step,inheritedPretraining=inherited_pretraining,ownParent=own_parent,settings=settings,sourceSha256=corpus['sourceSha256'],initialLanguageValidationLoss=initial_language_validation,elapsedSeconds=elapsed_before+time.monotonic()-started),tmp);tmp.replace(dst)
    print(json.dumps(dict(event='start',parameters=sum(t.numel() for t in model.parameters()),config=config,trainRows=len(train),validationRows=len(valid),rawSamples=len(raw),width=width,settings=settings,resumeStep=resume)),flush=True)
    for step in range(resume+1,total_steps+1):
        pretraining=step<=args.pretrain_steps
        local=step if pretraining else step-args.pretrain_steps
        length=args.pretrain_steps if pretraining else args.steps
        if local==1 and not pretraining:
            # Independent optimizer states distinguish language pretraining
            # from instruction tuning; weights remain the same own model.
            if raw_best is not None:model.load_state_dict(raw_best)
            optimizer=torch.optim.AdamW(model.parameters(),lr=args.learning_rate,weight_decay=0.03)
        model.train()
        if pretraining:
            index=torch.randint(len(raw),(args.batch_size,));n=raw_width if args.length_buckets else width
            inputs,targets=rx[index,:n],ry[index,:n]
        elif args.length_buckets:
            # Choose a length bucket by its total sample weight, then examples
            # within it. Each example retains the intended marginal weight;
            # a rare long answer no longer pads every short batch to its width.
            bucket=int(torch.multinomial(bucket_masses,1));eligible=bucket_indices[bucket]
            index=eligible[torch.multinomial(weights[eligible],args.batch_size,replacement=True)]
            n=bucket_widths[bucket];inputs,targets=x[index,:n],y[index,:n]
        else:
            index=torch.multinomial(weights,args.batch_size,replacement=True);inputs,targets=x[index],y[index]
        lr=args.learning_rate*min(1.0,local/100)*max(0.08,(1+math.cos(math.pi*local/length))/2)
        for g in optimizer.param_groups:g['lr']=lr
        optimizer.zero_grad(set_to_none=True);loss=compiled(inputs,targets)
        if not pretraining and args.replay_weight:
            raw_index=torch.randint(len(raw),(args.batch_size,))
            loss=loss+args.replay_weight*compiled(rx[raw_index,:raw_width],ry[raw_index,:raw_width])
        loss.backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step()
        if (pretraining and (local%250==0 or local==length)) or (not pretraining and (local%args.validation_every==0 or local==length)):
            row=dict(step=step,stage='pretraining' if pretraining else 'dialogue',stageStep=local,loss=loss.item(),elapsedSeconds=round(elapsed_before+time.monotonic()-started,2))
            if pretraining and raw_validation:
                row['languageValidationLoss']=measure(rvx,rvy)
                if row['languageValidationLoss']<raw_best_loss:
                    raw_best_loss=row['languageValidationLoss'];raw_best=copy.deepcopy(model.state_dict());raw_best_step=step
            if not pretraining:
                outputs=generate(model,valid,corpus['tokenizer'])
                exact=sum(r['exact'] for r in outputs);val_loss=measure(vx,vy)
                row.update(validationExact=exact,validationTotal=len(valid),validationLoss=val_loss,trainLoss=measure(x[:256],y[:256]))
                if (exact,-val_loss)>rank:rank=(exact,-val_loss);best=copy.deepcopy(model.state_dict());best_step=step
            history.append(row);save(step);print(json.dumps(row),flush=True)
        elif step%250==0:save(step)
    model.load_state_dict(best);model.eval()
    test_sha=hashlib.sha256(json.dumps([r for r in corpus['rows'] if r['partition']=='test'],ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
    training=dict(randomInitialization=True,externalWeights=False,externalInferenceAPIs=False,teacher=False,completedSteps=total_steps,pretrainingUpdates=args.pretrain_steps,dialogueUpdates=args.steps,bestStep=best_step,seed=args.seed,parameters=sum(t.numel() for t in model.parameters()),sourceSha256=corpus['sourceSha256'],testSha256=test_sha,validationExact=rank[0],validationLoss=-rank[1],trainRows=len(train),validationRows=len(valid),rawLanguageSamples=len(raw),elapsedSeconds=round(elapsed_before+time.monotonic()-started,2),pytorch=torch.__version__,settings=settings,note='Source-authored finite curriculum. Raw language next-token pretraining then answer-only SFT; validation-only selection, no outside weights or answer retrieval. This does not establish general dialogue or reasoning.')
    training['initialLanguageValidationLoss']=initial_language_validation
    training['finalLanguageValidationLoss']=measure(rvx,rvy) if raw_validation else None
    training['selectedPretrainingStep']=raw_best_step if raw_best is not None else args.pretrain_steps
    training['selectedPretrainingValidationLoss']=raw_best_loss if raw_best is not None else None
    training['initializationKind']='own-raw-pretraining-continuation' if own_parent else 'random'
    training['inheritedOwnPretrainingUpdates']=inherited_pretraining
    training['ownPretrainingParent']=own_parent
    tensors={k:dict(shape=list(v.shape),data=[round(x,7) for x in v.flatten().tolist()]) for k,v in model.state_dict().items()}
    exported=dict(schemaVersion=1,version=args.version,config=config,tokenizer=corpus['tokenizer'],tensors=tensors,training=training)
    pathlib.Path(args.output).write_text('// Own experimental curriculum Transformer; not the production model.\nexport const dialogueModel='+json.dumps(exported,separators=(',',':'))+';\n')
    pathlib.Path(args.artifacts_prefix+'-training.json').write_text(json.dumps(dict(config=config,training=training,history=history),indent=2)+'\n')
    refs=[]
    for r in valid[:4]:
        tokens=r['tokens'][:r['prefixLength']]
        with torch.no_grad():logits=model(torch.tensor([tokens]))[0,-1].tolist()
        refs.append(dict(id=r['id'],tokens=tokens,logits=logits))
    pathlib.Path(args.artifacts_prefix+'-reference.json').write_text(json.dumps(dict(version=exported['version'],references=refs),separators=(',',':'))+'\n')
    print(json.dumps(dict(event='complete',**training)),flush=True)

if __name__=='__main__':main()
