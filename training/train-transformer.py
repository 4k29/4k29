"""Train a tiny GPT-style decoder on authored grammar paths, using real backprop.

PyTorch is a training-only dependency. The exported browser model needs no ML
runtime. Unique phrase groups keep duplicate style-tagged English paths together
in the training or validation partition; held-out evaluation phrases are not read.
"""
import argparse
import copy
import hashlib
import json
import math
import pathlib
import time

import torch
from torch import nn
from torch.nn import functional as F

ROOT = pathlib.Path(__file__).resolve().parent.parent


class Block(nn.Module):
    def __init__(self, dim, heads, hidden, dropout):
        super().__init__()
        self.heads = heads
        self.ln1 = nn.LayerNorm(dim)
        self.qkv = nn.Linear(dim, 3 * dim)
        self.proj = nn.Linear(dim, dim)
        self.ln2 = nn.LayerNorm(dim)
        self.fc1 = nn.Linear(dim, hidden)
        self.fc2 = nn.Linear(hidden, dim)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        batch, steps, dim = x.shape
        q, k, v = self.qkv(self.ln1(x)).chunk(3, dim=-1)
        q, k, v = [a.view(batch, steps, self.heads, dim // self.heads).transpose(1, 2) for a in (q, k, v)]
        weights = q @ k.transpose(-2, -1) / math.sqrt(dim // self.heads)
        mask = torch.ones(steps, steps, dtype=torch.bool, device=x.device).triu(1)
        weights = F.softmax(weights.masked_fill(mask, float('-inf')), dim=-1)
        attention = (weights @ v).transpose(1, 2).contiguous().view(batch, steps, dim)
        x = x + self.dropout(self.proj(attention))
        # tanh GELU matches the dependency-free JavaScript inference exactly.
        return x + self.dropout(self.fc2(F.gelu(self.fc1(self.ln2(x)), approximate='tanh')))


class Decoder(nn.Module):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.token = nn.Embedding(config['vocabulary'], config['dim'])
        self.position = nn.Embedding(config['context'], config['dim'])
        self.blocks = nn.ModuleList([Block(config['dim'], config['heads'], config['hidden'], config['dropout']) for _ in range(config['layers'])])
        self.norm = nn.LayerNorm(config['dim'])
        self.apply(self.initialize)

    @staticmethod
    def initialize(module):
        if isinstance(module, (nn.Linear, nn.Embedding)):
            nn.init.normal_(module.weight, mean=0.0, std=0.02)
        if isinstance(module, nn.Linear):
            nn.init.zeros_(module.bias)

    def forward(self, tokens):
        x = self.token(tokens) + self.position(torch.arange(tokens.shape[1], device=tokens.device))
        for block in self.blocks:
            x = block(x)
        # Weight tying: the input embedding also predicts the next token.
        return F.linear(self.norm(x), self.token.weight)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--corpus', default='/tmp/4k29-transformer-corpus.json')
    parser.add_argument('--steps', type=int, default=10000)
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--seed', type=int, default=2941)
    parser.add_argument('--dropout', type=float, default=0.12)
    parser.add_argument('--learning-rate', type=float, default=0.00015)
    parser.add_argument('--warmup', type=int, default=1000)
    parser.add_argument('--minimum-steps', type=int, default=10000)
    parser.add_argument('--version', default='2026-10-04.transformer-2')
    parser.add_argument('--initialize-model')
    parser.add_argument('--expand-vocabulary', action='store_true')
    parser.add_argument('--distill', type=float, default=0.0)
    parser.add_argument('--distill-model', help='Optional frozen grammar teacher, separate from the continued checkpoint')
    parser.add_argument('--rounds', type=int, default=0)
    parser.add_argument('--updates-per-round', type=int, default=10000)
    parser.add_argument('--adaptive-learning-rate', action='store_true')
    parser.add_argument('--label-smoothing', type=float, default=0.0)
    parser.add_argument('--batch-size', type=int, default=64)
    parser.add_argument('--validation-every', type=int, default=100)
    parser.add_argument('--checkpoint')
    parser.add_argument('--compile', action='store_true')
    parser.add_argument('--compile-loss', action='store_true')
    parser.add_argument('--resume')
    parser.add_argument('--export-final', action='store_true', help='Export the checkpoint after every requested update, keeping earlier validation results as diagnostics')
    parser.add_argument('--output', default=str(ROOT / 'docs' / 'neural-model.js'))
    parser.add_argument('--artifacts-prefix', default=str(ROOT / 'training' / 'transformer'))
    args = parser.parse_args()
    if args.rounds:
        if args.rounds < 1 or args.updates_per_round < 1:
            parser.error('rounds and updates-per-round must be positive')
        args.steps = args.rounds * args.updates_per_round
    if args.steps < args.minimum_steps or args.learning_rate <= 0 or args.warmup < 1:
        parser.error('steps must reach minimum-steps; learning-rate and warmup must be positive')
    torch.set_num_threads(args.threads)
    torch.manual_seed(args.seed)
    torch.use_deterministic_algorithms(True)
    corpus = json.loads(pathlib.Path(args.corpus).read_text())
    validation = lambda row: not row.get('trainOnly', False) and int(hashlib.sha256(row['group'].encode()).hexdigest()[:8], 16) % 7 == 0
    train = [row for row in corpus['rows'] if not validation(row)]
    valid = [row for row in corpus['rows'] if validation(row)]
    assert not ({row['group'] for row in train} & {row['group'] for row in valid})
    config = dict(vocabulary=len(corpus['vocabulary']), dim=32, heads=4, hidden=64, layers=2, context=32, dropout=args.dropout, epsilon=1e-5)
    model = Decoder(config)
    initialized_from = None
    if args.initialize_model:
        source = pathlib.Path(args.initialize_model).read_text()
        initialized_from = json.loads(source.split('export const neuralModel=',1)[1].strip().removesuffix(';'))
        for key in ['dim','heads','hidden','layers','context']+([] if args.expand_vocabulary else ['vocabulary']):
            if initialized_from['config'][key] != config[key]:
                raise ValueError('Warm-start architecture mismatch: '+key)
        old_vocabulary=initialized_from['vocabulary']
        vocabulary_matches=corpus['vocabulary'][:len(old_vocabulary)]==old_vocabulary if args.expand_vocabulary else old_vocabulary==corpus['vocabulary']
        if not vocabulary_matches or initialized_from['training']['baseSourceSha256'] != corpus['baseSourceSha256']:
            raise ValueError('Warm-start vocabulary or base grammar mismatch')
        state={key:torch.tensor(tensor['data']).reshape(tensor['shape']) for key,tensor in initialized_from['tensors'].items()}
        if args.expand_vocabulary:
            expanded=model.token.weight.detach().clone()
            expanded[:len(old_vocabulary)]=state['token.weight']
            state['token.weight']=expanded
        model.load_state_dict(state)
    if args.distill and initialized_from is None:
        parser.error('distill requires initialize-model')
    max_length = max(len(row['tokens']) for row in corpus['rows']) - 1
    if max_length>config['context']:
        raise ValueError('Training sequence exceeds context')

    def pack(rows):
        x = torch.full((len(rows), max_length), corpus['pad'], dtype=torch.long)
        y = torch.full_like(x, -100)
        for i, row in enumerate(rows):
            tokens = torch.tensor(row['tokens'], dtype=torch.long)
            x[i, :len(tokens) - 1] = tokens[:-1]
            y[i, :len(tokens) - 1] = tokens[1:]
            y[i, :row.get('prefixLength',4)-1] = -100  # Sentence/value tokens and EOS only.
        return x, y

    train_x, train_y = pack(train)
    valid_x, valid_y = pack(valid)
    weights = torch.tensor([row['weight'] for row in train], dtype=torch.float)
    teacher_probabilities = None
    if args.distill:
        model.eval()
        teacher_model=model
        teacher_vocabulary=config['vocabulary']
        if args.distill_model:
            teacher_export=json.loads(pathlib.Path(args.distill_model).read_text().split('export const neuralModel=',1)[1].strip().removesuffix(';'))
            teacher_vocabulary=len(teacher_export['vocabulary'])
            if corpus['vocabulary'][:teacher_vocabulary]!=teacher_export['vocabulary']:
                raise ValueError('Distillation teacher vocabulary prefix mismatch')
            teacher_model=Decoder(config)
            teacher_state={key:torch.tensor(tensor['data']).reshape(tensor['shape']) for key,tensor in teacher_export['tensors'].items()}
            embeddings=torch.zeros_like(model.token.weight)
            embeddings[:teacher_vocabulary]=teacher_state['token.weight']
            teacher_state['token.weight']=embeddings
            teacher_model.load_state_dict(teacher_state);teacher_model.eval()
        with torch.no_grad():
            pieces=[]
            for start in range(0,len(train_x),64):
                logits=teacher_model(train_x[start:start+64])/2.0
                logits[:,:,teacher_vocabulary:]=-1e9
                pieces.append(F.softmax(logits,dim=-1))
            teacher_probabilities=torch.cat(pieces)
            for i,row in enumerate(train):
                if row.get('trainOnly',False):teacher_probabilities[i].zero_()  # New literal values have no pretrained teacher targets.

    @torch.no_grad()
    def measure(x, y):
        model.eval()
        total, tokens = 0.0, 0
        for start in range(0, len(x), 64):
            targets = y[start:start + 64]
            total += F.cross_entropy(model(x[start:start + 64]).reshape(-1, config['vocabulary']), targets.reshape(-1), reduction='sum').item()
            tokens += targets.ne(-100).sum().item()
        return total / tokens

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=0.02)
    initial_train, initial_valid = measure(train_x, train_y), measure(valid_x, valid_y)
    def objective(tokens,targets,teacher):
        logits=model(tokens)
        loss=F.cross_entropy(logits.reshape(-1,config['vocabulary']),targets.reshape(-1),label_smoothing=args.label_smoothing)
        if teacher is not None:
            divergence=F.kl_div(F.log_softmax(logits/2.0,dim=-1),teacher,reduction='none').sum(-1)
            mask=targets.ne(-100)
            loss=loss+args.distill*4.0*(divergence*mask).sum()/mask.sum()
        return loss
    if args.compile_loss:
        train_objective=torch.compile(objective,dynamic=False)
    else:
        if args.compile:
            model_forward=torch.compile(model,dynamic=False)
            # Keep export/validation on the original module and state keys.
            def forward_objective(tokens,targets,teacher):
                logits=model_forward(tokens)
                loss=F.cross_entropy(logits.reshape(-1,config['vocabulary']),targets.reshape(-1),label_smoothing=args.label_smoothing)
                if teacher is not None:
                    divergence=F.kl_div(F.log_softmax(logits/2.0,dim=-1),teacher,reduction='none').sum(-1)
                    mask=targets.ne(-100)
                    loss=loss+args.distill*4.0*(divergence*mask).sum()/mask.sum()
                return loss
            train_objective=forward_objective
        else:
            train_objective=objective
    best_loss, best_step, best_state = (float('inf'), 0, None) if args.minimum_steps else (initial_valid, 0, copy.deepcopy(model.state_dict()))
    overall_best_loss, overall_best_step = initial_valid, 0
    round_history, learning_rate_scale, plateau_rounds = [], 1.0, 0
    history = [dict(step=0, trainLoss=initial_train, validationLoss=initial_valid)]
    resume_step,elapsed_offset=0,0
    if args.resume:
        checkpoint=torch.load(args.resume,weights_only=False)
        if checkpoint['sourceSha256']!=corpus['sourceSha256']:
            raise ValueError('Resume corpus mismatch')
        for key in ['steps','rounds','updates_per_round','seed','batch_size','learning_rate','distill','dropout','label_smoothing','warmup','minimum_steps']:
            if checkpoint['args'][key]!=getattr(args,key):
                raise ValueError('Resume training configuration mismatch: '+key)
        model.load_state_dict(checkpoint['model']);optimizer.load_state_dict(checkpoint['optimizer']);torch.set_rng_state(checkpoint['rng'])
        best_state,best_step,best_loss=checkpoint['bestState'],checkpoint['bestStep'],checkpoint['bestLoss']
        history,round_history=checkpoint['history'],checkpoint['rounds']
        learning_rate_scale=checkpoint['learningRateScale'];plateau_rounds=checkpoint.get('plateauRounds',0)
        resume_step=checkpoint['step'];elapsed_offset=history[-1]['elapsedSeconds']
        initial_train,initial_valid=history[0]['trainLoss'],history[0]['validationLoss']
        overall_best=min(history,key=lambda row:row['validationLoss'])
        overall_best_loss,overall_best_step=overall_best['validationLoss'],overall_best['step']
    started = time.monotonic()
    print(json.dumps(dict(event='start',parameters=sum(p.numel() for p in model.parameters()),trainRows=len(train),validationRows=len(valid),initialTrainLoss=initial_train,initialValidationLoss=initial_valid)), flush=True)
    step=resume_step
    for step in range(resume_step+1, args.steps + 1):
        model.train()
        indices = torch.multinomial(weights, args.batch_size, replacement=True)
        learning_rate = args.learning_rate * min(step / args.warmup, 1.0) * (0.12 + 0.88 * (1 + math.cos(math.pi * step / args.steps)) / 2)
        if args.adaptive_learning_rate:
            learning_rate=max(0.000002,learning_rate*learning_rate_scale)
        for group in optimizer.param_groups:
            group['lr'] = learning_rate
        optimizer.zero_grad(set_to_none=True)
        # Only training-partition next-token targets and frozen teacher outputs.
        loss=train_objective(train_x[indices],train_y[indices],teacher_probabilities[indices] if teacher_probabilities is not None else None)
        if not torch.isfinite(loss):
            raise RuntimeError('Nonfinite training loss')
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        if step % args.validation_every == 0 or step == args.steps or args.rounds and step % args.updates_per_round == 0:
            train_loss, valid_loss = measure(train_x, train_y), measure(valid_x, valid_y)
            row = dict(step=step, trainLoss=train_loss, validationLoss=valid_loss,learningRate=learning_rate,elapsedSeconds=round(elapsed_offset+time.monotonic() - started, 2))
            history.append(row)
            print(json.dumps(row), flush=True)
            improved = valid_loss < overall_best_loss - 0.0001
            if valid_loss < overall_best_loss:
                overall_best_loss, overall_best_step = valid_loss, step
            if step >= args.minimum_steps and valid_loss < best_loss - 0.0001:
                best_loss, best_step, best_state = valid_loss, step, copy.deepcopy(model.state_dict())
            if args.rounds and step % args.updates_per_round == 0:
                plateau_rounds=0 if improved else plateau_rounds+1
                if args.adaptive_learning_rate and plateau_rounds>=3:
                    learning_rate_scale=max(0.1,learning_rate_scale*0.7)
                    plateau_rounds=0
                round_row=dict(round=step//args.updates_per_round,updates=step,trainLoss=train_loss,validationLoss=valid_loss,learningRateScale=learning_rate_scale,elapsedSeconds=row['elapsedSeconds'])
                round_history.append(round_row)
                print(json.dumps(dict(event='round-complete',**round_row)),flush=True)
                if args.checkpoint:
                    target = pathlib.Path(args.checkpoint)
                    temporary = target.with_suffix('.tmp')
                    torch.save(dict(step=step,model=model.state_dict(),optimizer=optimizer.state_dict(),rng=torch.get_rng_state(),bestState=best_state,bestStep=best_step,bestLoss=best_loss,history=history,rounds=round_history,learningRateScale=learning_rate_scale,plateauRounds=plateau_rounds,args=vars(args),sourceSha256=corpus['sourceSha256']),temporary)
                    temporary.replace(target)
            if not args.rounds and step >= max(1000,args.minimum_steps) and best_state is not None and step - best_step >= 800:
                print(json.dumps(dict(event='early-stop',step=step,bestStep=best_step)), flush=True)
                break
    if args.export_final:
        if step!=args.steps or args.rounds and len(round_history)!=args.rounds:
            raise RuntimeError('Final export requires all requested updates and rounds')
        best_state,best_step,best_loss=copy.deepcopy(model.state_dict()),step,measure(valid_x,valid_y)
    if best_state is None:
        raise RuntimeError('No checkpoint reached the minimum update count')
    model.load_state_dict(best_state)
    model.eval()
    metadata = dict(seed=args.seed,optimizer='AdamW',schedule=str(args.warmup)+'-step warmup and cosine decay',peakLearningRate=args.learning_rate,batchSize=64,gradientClip=1.0,weightDecay=0.02,requestedSteps=args.steps,minimumSteps=args.minimum_steps,completedSteps=step,bestStep=best_step,overallBestStep=overall_best_step,overallBestValidationLoss=overall_best_loss,trainRows=len(train),validationRows=len(valid),trainGroups=len({r['group'] for r in train}),validationGroups=len({r['group'] for r in valid}),partition='SHA256(language:kind:tokens) first 8 hex digits modulo 7; duplicates share a partition',initialTrainLoss=initial_train,initialValidationLoss=initial_valid,finalTrainLoss=measure(train_x,train_y),finalValidationLoss=measure(valid_x,valid_y),parameters=sum(p.numel() for p in model.parameters()),elapsedSeconds=round(time.monotonic()-started,2),pytorch=torch.__version__,sourceSha256=corpus['sourceSha256'],baseSourceSha256=corpus['baseSourceSha256'],note='Engineer-authored grammar. No user writing samples, generated chat replies, profile values, or external evaluation phrases were used as training targets.')
    if initialized_from:
        previous_steps=initialized_from['training'].get('cumulativeCheckpointSteps',initialized_from['training']['bestStep'])
        metadata.update(initializedModelSha256=hashlib.sha256(pathlib.Path(args.initialize_model).read_bytes()).hexdigest(),initialCheckpointStep=initialized_from['training']['bestStep'],distillationWeight=args.distill,distillationTemperature=2.0,cumulativeCheckpointSteps=previous_steps+best_step)
    metadata.update(checkpointPolicy='after-all-requested-updates' if args.export_final else 'best-validation-after-minimum-updates',elapsedSeconds=round(elapsed_offset+time.monotonic()-started,2),resumedFromStep=resume_step,batchSize=args.batch_size,compiled=args.compile,compiledLoss=args.compile_loss,labelSmoothing=args.label_smoothing,adaptiveLearningRate=args.adaptive_learning_rate,completedRounds=len(round_history),requestedRounds=args.rounds,updatesPerRound=args.updates_per_round if args.rounds else None)
    if args.distill_model:metadata['grammarTeacherSha256']=hashlib.sha256(pathlib.Path(args.distill_model).read_bytes()).hexdigest()
    tensors = {key:dict(shape=list(value.shape),data=[round(v,7) for v in value.detach().reshape(-1).tolist()]) for key,value in model.state_dict().items()}
    exported = dict(schemaVersion=1,version=args.version,baseVersion=corpus['baseVersion'],config=config,controls=corpus['controls'],pad=corpus['pad'],vocabulary=corpus['vocabulary'],tensors=tensors,training=metadata)
    if corpus.get('specificationMemory'):
        exported['specificationMemory']=corpus['specificationMemory']
        metadata.update(literalFactRows=sum(r.get('trainOnly',False) for r in train),expandedVocabularyFrom=len(initialized_from['vocabulary']),specificationSourceSha256=corpus['specificationMemory']['sourceSha256'],note='Own Transformer weights continued from 600,000 additional updates. Officially sourced product values and owner-approved drama descriptions are literal next-token training targets; source-backed memory is bundled in the same model artifact. Known-fact recall is memorization, not held-out factual generalization. Grammar validation groups remain separate. No external model or evaluation phrases used.')
    pathlib.Path(args.output).write_text('// Generated by training/train-transformer.py; do not edit weights by hand.\nexport const neuralModel='+json.dumps(exported,separators=(',',':'))+';\n')
    pathlib.Path(args.artifacts_prefix+'-training.json').write_text(json.dumps(dict(config=config,training=metadata,history=history,rounds=round_history),indent=2)+'\n')
    references=[]
    for language,kind,style in [('ja','name','friendly'),('ja','name','polite'),('ja','workflow','friendly'),('ja','audio','friendly'),('en','name','friendly'),('en','subscription','polite')]:
        row=next(r for r in corpus['rows'] if r['language']==language and r['kind']==kind and r['style']==style)
        for length in [4,min(9,len(row['tokens'])-1)]:
            tokens=row['tokens'][:length]
            with torch.no_grad():
                logits=model(torch.tensor([tokens]))[0,-1].tolist()
            references.append(dict(context=dict(language=language,kind=kind,style=style),tokens=tokens,logits=[round(v,7) for v in logits]))
    pathlib.Path(args.artifacts_prefix+'-reference.json').write_text(json.dumps(dict(version=exported['version'],references=references),separators=(',',':'))+'\n')
    print(json.dumps(dict(event='complete',**metadata)), flush=True)


if __name__ == '__main__':
    main()
