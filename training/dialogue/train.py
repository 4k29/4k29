"""Train an own question-to-full-answer Transformer from random weights.

No teacher, pretrained weights, retrieved answer, or grammar-constrained decoder.
The answer loss masks the input question/history, as in supervised causal LM.
"""
import argparse
import copy
import importlib.util
import json
import math
import pathlib
import sys
import time

import torch
from torch.nn import functional as F
from tokenizer import SPECIALS, decode

HERE=pathlib.Path(__file__).resolve().parent
module_spec=importlib.util.spec_from_file_location('own_architecture',HERE.parent/'train-transformer.py')
architecture=importlib.util.module_from_spec(module_spec)
sys.modules[module_spec.name]=architecture
module_spec.loader.exec_module(architecture)


class DialogueDecoder(architecture.Decoder):
    """Optional training-only intent head, never an answer lookup at inference."""
    def __init__(self,config):
        super().__init__(config)
        if config.get('intents'):
            self.intent=torch.nn.Linear(config['dim'],len(config['intents']))
            self.initialize(self.intent)
        if config.get('semanticTasks'):
            self.semantic=torch.nn.ModuleDict({name:torch.nn.Linear(config['dim'],len(labels)) for name,labels in config['semanticTasks'].items()})
            self.semantic.apply(self.initialize)

    def forward(self,tokens,intent_positions=None,semantic_positions=None):
        x=self.token(tokens)+self.position(torch.arange(tokens.shape[1],device=tokens.device))
        for block in self.blocks:x=block(x)
        x=self.norm(x)
        logits=F.linear(x,self.token.weight)
        if semantic_positions is not None:
            selected=x[torch.arange(len(tokens)),semantic_positions]
            return logits,{name:head(selected) for name,head in self.semantic.items()}
        if intent_positions is None:return logits
        return logits,self.intent(x[torch.arange(len(tokens)),intent_positions])


def pack(rows,pad,width):
    x=torch.full((len(rows),width),pad,dtype=torch.long)
    y=torch.full_like(x,-100)
    for i,row in enumerate(rows):
        tokens=torch.tensor(row['tokens'])
        x[i,:len(tokens)-1]=tokens[:-1]
        y[i,:len(tokens)-1]=tokens[1:]
        y[i,:row['prefixLength']-1]=-100
    return x,y


@torch.no_grad()
def generate(model,rows,tokenizer,batch_size=16):
    model.eval()
    results=[]
    for start in range(0,len(rows),batch_size):
        batch=rows[start:start+batch_size]
        width=model.config['context']
        tokens=torch.full((len(batch),width),SPECIALS['pad'],dtype=torch.long)
        lengths=torch.tensor([row['prefixLength'] for row in batch])
        for i,row in enumerate(batch):tokens[i,:lengths[i]]=torch.tensor(row['tokens'][:row['prefixLength']])
        ended=[False]*len(batch)
        reached_eos=[False]*len(batch)
        outputs=[[] for row in batch]
        for _ in range(width-min(lengths).item()):
            logits=model(tokens[:,:max(lengths).item()])
            next_ids=logits[torch.arange(len(batch)),lengths-1].argmax(-1)
            for i,token in enumerate(next_ids.tolist()):
                if ended[i]:continue
                if token==SPECIALS['eos']:
                    ended[i]=True
                    reached_eos[i]=True
                else:outputs[i].append(token)
                if lengths[i]>=width:
                    ended[i]=True
                else:
                    tokens[i,lengths[i]]=token
                    lengths[i]+=1
            if all(ended):break
        for row,output,finished in zip(batch,outputs,reached_eos):
            text=decode(output,tokenizer)
            valid_utf8=True
            try:b''.join(bytes.fromhex(tokenizer['bytes'][t]) for t in output).decode('utf-8')
            except UnicodeDecodeError:valid_utf8=False
            valid=valid_utf8 and all(token>=len(SPECIALS) for token in output)
            results.append(dict(id=row['id'],kind=row['kind'],question=row['question'],history=row['history'],expected=row['answer'],answer=text,exact=text==row['answer'] and finished and valid,eos=finished,validTokens=valid,validUtf8=valid_utf8))
    return results


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--corpus',default=str(HERE/'corpus.json'))
    p.add_argument('--steps',type=int,default=10000)
    p.add_argument('--batch-size',type=int,default=8)
    p.add_argument('--threads',type=int,default=1)
    p.add_argument('--learning-rate',type=float,default=0.001)
    p.add_argument('--seed',type=int,default=429)
    p.add_argument('--validation-every',type=int,default=500)
    p.add_argument('--compile-loss',action='store_true')
    p.add_argument('--checkpoint',default='/tmp/4k29-dialogue-checkpoint.pt')
    p.add_argument('--resume')
    p.add_argument('--intent-loss',type=float,default=0.0)
    p.add_argument('--version',default='2026-10-04.dialogue-experimental-1')
    p.add_argument('--output',default=str(HERE/'candidate.js'))
    p.add_argument('--artifacts-prefix',default=str(HERE/'experiment'))
    args=p.parse_args()
    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    torch.use_deterministic_algorithms(True)
    corpus=json.loads(pathlib.Path(args.corpus).read_text())
    train=[r for r in corpus['rows'] if r['partition']=='train']
    valid=[r for r in corpus['rows'] if r['partition']=='validation']
    config=dict(vocabulary=len(corpus['tokenizer']['bytes']),dim=64,heads=4,hidden=128,layers=2,context=128,dropout=0.1,epsilon=1e-5)
    if args.intent_loss:
        config['intents']=sorted({r['id'].split(':')[0] for r in train})
    model=DialogueDecoder(config)
    width=max(len(r['tokens'])-1 for r in train+valid)
    if width>=config['context']:raise ValueError('Sequence exceeds context; never silently truncate')
    x,y=pack(train,SPECIALS['pad'],width)
    vx,vy=pack(valid,SPECIALS['pad'],width)
    weights=torch.tensor([r['weight'] for r in train],dtype=torch.float32)
    intent_labels=torch.tensor([config.get('intents',[]).index(r['id'].split(':')[0]) if args.intent_loss else 0 for r in train])
    intent_positions=torch.tensor([r['prefixLength']-1 for r in train])
    optimizer=torch.optim.AdamW(model.parameters(),lr=args.learning_rate,weight_decay=0.02)
    def objective(tokens,targets,positions,intents):
        if args.intent_loss:
            logits,classes=model(tokens,positions)
            auxiliary=args.intent_loss*F.cross_entropy(classes,intents)
        else:
            logits=model(tokens)
            auxiliary=0
        return F.cross_entropy(logits.reshape(-1,config['vocabulary']),targets.reshape(-1),label_smoothing=0.01)+auxiliary
    train_objective=torch.compile(objective,dynamic=False) if args.compile_loss else objective
    @torch.no_grad()
    def measure(tokens,targets):
        model.eval()
        total,count=0.0,0
        for start in range(0,len(tokens),64):
            labels=targets[start:start+64]
            total+=F.cross_entropy(model(tokens[start:start+64]).reshape(-1,config['vocabulary']),labels.reshape(-1),reduction='sum').item()
            count+=labels.ne(-100).sum().item()
        return total/count
    history=[]
    best_rank=(-1,float('-inf'))
    best_state,best_step=None,0
    resume_step=0
    if args.resume:
        checkpoint=torch.load(args.resume,weights_only=False)
        if checkpoint['sourceSha256']!=corpus['sourceSha256']:raise ValueError('Corpus changed')
        for key in ['steps','batch_size','learning_rate','seed','validation_every','intent_loss']:
            if checkpoint['args'][key]!=getattr(args,key):raise ValueError('Resume settings changed: '+key)
        model.load_state_dict(checkpoint['model']);optimizer.load_state_dict(checkpoint['optimizer']);torch.set_rng_state(checkpoint['rng'])
        history,best_state,best_step,best_rank=checkpoint['history'],checkpoint['bestState'],checkpoint['bestStep'],checkpoint['bestRank']
        resume_step=checkpoint['step']
    started=time.monotonic()
    print(json.dumps(dict(event='start',parameters=sum(p.numel() for p in model.parameters()),trainRows=len(train),validationRows=len(valid),width=width,randomInitialization=True,resumeStep=resume_step)),flush=True)
    for step in range(resume_step+1,args.steps+1):
        model.train()
        index=torch.multinomial(weights,args.batch_size,replacement=True)
        progress=step/args.steps
        lr=args.learning_rate*min(1.0,step/200)*max(0.1,0.5+0.5*math.cos(math.pi*progress))
        for group in optimizer.param_groups:group['lr']=lr
        optimizer.zero_grad(set_to_none=True)
        loss=train_objective(x[index],y[index],intent_positions[index],intent_labels[index]);loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(),1.0);optimizer.step()
        if step%args.validation_every==0 or step==args.steps:
            val_loss=measure(vx,vy)
            outputs=generate(model,valid,corpus['tokenizer'])
            exact=sum(r['exact'] for r in outputs)
            row=dict(step=step,trainLoss=measure(x[:256],y[:256]),validationLoss=val_loss,validationExact=exact,validationTotal=len(valid),elapsedSeconds=round(time.monotonic()-started,2))
            history.append(row);print(json.dumps(row),flush=True)
            rank=(exact,-val_loss)
            if rank>best_rank:best_rank,best_state,best_step=rank,copy.deepcopy(model.state_dict()),step
            target=pathlib.Path(args.checkpoint);temporary=target.with_suffix('.tmp')
            torch.save(dict(step=step,model=model.state_dict(),optimizer=optimizer.state_dict(),rng=torch.get_rng_state(),history=history,bestState=best_state,bestStep=best_step,bestRank=best_rank,args=vars(args),sourceSha256=corpus['sourceSha256']),temporary);temporary.replace(target)
    model.load_state_dict(best_state);model.eval()
    training=dict(optimizer='AdamW',seed=args.seed,requestedSteps=args.steps,completedSteps=step,bestStep=best_step,randomInitialization=True,externalWeights=False,teacher=False,intentLossWeight=args.intent_loss,intentHeadUsedAtInference=False,parameters=sum(p.numel() for p in model.parameters()),trainRows=len(train),validationRows=len(valid),sourceSha256=corpus['sourceSha256'],validationExact=best_rank[0],validationLoss=-best_rank[1],elapsedSeconds=round(time.monotonic()-started,2),pytorch=torch.__version__,note='Full answer tokens learned from question/history input; no answer template or retrieval at generation. Engineer-authored finite-domain QA and exact synthetic arithmetic. Test questions never train, fit tokenizer, or select weights.')
    tensors={key:dict(shape=list(t.shape),data=[round(v,7) for v in t.flatten().tolist()]) for key,t in model.state_dict().items()}
    exported=dict(schemaVersion=1,version=args.version,config=config,tokenizer=corpus['tokenizer'],tensors=tensors,training=training)
    pathlib.Path(args.output).write_text('// Experimental own question-to-answer model; not the production model.\nexport const dialogueModel='+json.dumps(exported,separators=(',',':'))+';\n')
    pathlib.Path(args.artifacts_prefix+'-training.json').write_text(json.dumps(dict(config=config,training=training,history=history),indent=2)+'\n')
    references=[]
    for row in valid[:4]:
        prefix=row['tokens'][:row['prefixLength']]
        with torch.no_grad():logits=model(torch.tensor([prefix]))[0,-1].tolist()
        references.append(dict(id=row['id'],tokens=prefix,logits=logits))
    pathlib.Path(args.artifacts_prefix+'-reference.json').write_text(json.dumps(dict(version=exported['version'],references=references),separators=(',',':'))+'\n')
    print(json.dumps(dict(event='complete',**training)),flush=True)


if __name__=='__main__':main()
