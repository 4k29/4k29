"""Fixed v2 endpoint evaluation; no optimizer, selection, crop or output repair."""
import argparse,copy,hashlib,importlib.util,json,pathlib,platform,sys,time
import numpy as np
import torch
from core import HERE,REPO,decoder,digest,sha
from eval_core import aggregate,byte_payload,fence,greedy,groups,response_scores,window_scores

def read(p):return json.loads(pathlib.Path(p).read_text())
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def source_path(name):
    path=(REPO/name).resolve()
    if not path.is_relative_to(REPO):raise ValueError('Expected isolated repository input')
    return path

def state_payload(saved):
    if 'trajectory'in saved:return saved['trajectory']['config'],saved['trajectory']['model'],saved['trajectory']['uniqueUpdates']
    weights=saved.get('model',saved.get('state'))
    if weights is None:raise ValueError('Expected own raw state')
    return saved['config'],weights,saved.get('uniqueUpdates',saved.get('selectedStep',saved.get('step')))

def load(a,plan,data):
    if sha(a.checkpoint)!=a.checkpoint_sha256:raise ValueError('Exact endpoint SHA mismatch')
    saved=torch.load(a.checkpoint,map_location='cpu',weights_only=False)
    config,weights,step=state_payload(saved)
    if a.model=='r46':
        if a.checkpoint_sha256 not in ['a75320178439c0669a1ffbcb7cd744c72a437eaea3797404d7331b63ad1aaa50','d99f85f706d40702393410c05733274bcc59528c7c776ff9ba3cea74d2647f1d']or step!=9500:
            raise ValueError('Legacy reference must be fixed R46 selected9500')
        tok_path=REPO/'training/language/round46/multiview/tokenizer.json'
        if sha(tok_path)!='453e93eafe8bf745e47c5241f9c7e9ed9e0b7dd3dc2bb912c21255b654bf5613':raise ValueError('Legacy own tokenizer mismatch')
        tok=read(tok_path)
    else:
        if a.expected_updates not in [256,512] or step!=a.expected_updates:raise ValueError('Need fixed terminal512 or fixed resource milestone256')
        if config!=plan['models'][a.model]or saved.get('modelName')!=a.model:raise ValueError('Wrong registered architecture/arm')
        if saved.get('planSha256')!=a.plan_sha256 or saved.get('dataSha256')!=plan['dataSha256'] or saved.get('tokenizerSha256')!=data['tokenizerSha256']:
            raise ValueError('Checkpoint/data/plan identity differs')
        tok_path=source_path(data['tokenizerPath']);tok=read(tok_path)
        if sha(tok_path)!=data['tokenizerSha256']:raise ValueError('New own TRAIN-only tokenizer mismatch')
    if any(v.dtype!=torch.float32 or not bool(torch.isfinite(v).all())for v in weights.values()):raise ValueError('Expected finite raw FP32 weights')
    rng=torch.get_rng_state().clone()
    model=decoder(config);model.load_state_dict(weights,strict=True);model.eval();torch.set_rng_state(rng)
    if not torch.equal(rng,torch.get_rng_state()):raise AssertionError('Constructor RNG not restored')
    return model,tok,step,tok_path

def summarize_responses(rows):
    body=[t for r in rows if r.get('supported')for t in r['scores']['tokens']]
    return dict(cases=len(rows),supported=sum(r.get('supported',False)for r in rows),body=aggregate(body),
        macroBodyNll=sum(r['scores']['body']['nllPerToken']for r in rows if r.get('supported'))/sum(r.get('supported',False)for r in rows)if any(r.get('supported')for r in rows)else None,
        scope='Canonical human-body encoding, EOS excluded; reference not unique; raw token NLL not cross-tokenizer comparable')

def selfplay(model,cases,pieces,plan):
    """Three A/B self-generated human-style turns, not human-interactive skill."""
    selected=plan.get('evaluation',{}).get('rolloutCaseIds')
    if selected is None:
        selected=sorted([c['id']for c in cases],key=lambda s:hashlib.sha256(('v2-selfplay4-v1|'+s).encode()).hexdigest())[:4]
    if len(selected)!=4 or len(set(selected))!=4 or not set(selected)<=set(c['id']for c in cases):raise ValueError('Need4 fixed self-play episodes')
    output=[]
    for ident in selected:
        c=next(c for c in cases if c['id']==ident);original=c['prefixTokens'];role=c['targetLocalRoleToken']
        if original[0]!=1 or original[-1]!=role or role not in [3,4]:raise ValueError('Invalid original role prefix')
        remain=original[1:-1];turns=[];index=0
        while remain:
            end=remain.index(2);ids=remain[:end+1];remain=remain[end+1:]
            if ids[0]not in [3,4]or any(t<6 for t in ids[1:-1]):raise ValueError('Original turns must preserve role/body/EOS')
            turns.append(dict(turnId='source-'+str(index),origin='source-human-history',role=ids[0],tokens=ids));index+=1
        if [1]+[t for turn in turns for t in turn['tokens']]+[role]!=original:raise AssertionError('Original source reconstruction differs')
        rows=[];all_dropped=[];status='completed3-self-generated-turns'
        for j in range(3):
            dropped=[]
            while 1+sum(len(t['tokens'])for t in turns)+1+64>model.config['context']:
                if not turns:raise ValueError('Cannot fit turn without original content cropping')
                dropped.append(turns.pop(0))
            prefix=[1]+[t for turn in turns for t in turn['tokens']]+[role]
            g=greedy(model,prefix,pieces,max_new=64)
            rows.append(dict(turn=j,localRoleToken=role,inputTokens=prefix,inputBodyBytes=byte_payload(prefix,pieces),
                droppedWholeTurns=dropped,retainedTurnIds=[t['turnId']for t in turns],generation=g))
            all_dropped.extend(dropped)
            if not g['eos']:
                status='incomplete-no-true-eos-do-not-advance-speaker';break
            turns.append(dict(turnId='generated-'+str(j),origin='own-unmodified-output',role=role,tokens=[role]+g['tokensIncludingEos']))
            role=4 if role==3 else 3
        output.append(dict(id='selfplay-'+ident,sourceCaseId=ident,document=c['document'],originalHumanHistory=c['history'],
            initialPrefixTokens=original,initialPrefixDisplayText=c['prefixText'],requestedTurns=3,completedTurns=sum(r['generation']['eos']for r in rows),
            status=status,rows=rows,allDroppedWholeTurns=all_dropped,
            interpretation='A/B self-play consistency stress only, not human-interactive response or unseen dialogue success',
            policy='Actual generated history, true EOS only, role3/4 alternating externally, max64/turn, drop oldest complete turns if needed; no gold future prompts/answers or repairs'))
    return output

def run(a):
    if sha(a.plan)!=a.plan_sha256:raise ValueError('Frozen plan SHA mismatch')
    plan=read(a.plan)
    for path,expected in plan['codeReceipts'].items():
        if sha(source_path(path))!=expected:raise ValueError('Frozen code changed: '+path)
    dp=source_path(plan['dataPath'])
    if sha(dp)!=plan['dataSha256']:raise ValueError('Frozen data mismatch')
    data=read(dp);bp=source_path(data['benchmarkPath'])
    if sha(bp)!=data['benchmarkSha256']:raise ValueError('Frozen benchmark mismatch')
    cases=read(bp)['cases']
    if len(cases)!=32 or len({c['document']for c in cases})!=32:raise ValueError('Need all32 fixed unique-document probes')
    ids=plan.get('evaluation',{}).get('generationCaseIds',[c['id']for c in cases])
    if not ids or len(ids)!=len(set(ids))or not set(ids)<=set(c['id']for c in cases):raise ValueError('Invalid fixed generation subset')
    out=a.output.resolve()
    if not out.is_relative_to(HERE)or out.exists():raise ValueError('NEW output directory inside v2 required')
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    model,tok,step,tp=load(a,plan,data);pieces=[bytes.fromhex(x)for x in tok['bytes']]
    initial=digest(model.state_dict());rng=torch.get_rng_state().clone();started=time.monotonic()
    out.mkdir(parents=True);window_rows=[];response_rows=[];generated=[];coverage=[]
    receipt=dict(status='running',endpoint=a.model,checkpointSha256=a.checkpoint_sha256,checkpointPath=str(a.checkpoint),
        selectedOrUniqueUpdates=step,planSha256=a.plan_sha256,dataSha256=plan['dataSha256'],benchmarkSha256=data['benchmarkSha256'],
        tokenizerSha256=sha(tp),mode='human_dialogue_continuation',optimizerUpdates=0,sealedTestUsed=False,
        oldReferenceNotEqualExposure=a.model=='r46',newSeriesRoleTokens='3/4 humanA/B; EOS2 human utterance end',
        generationPolicy='full-vocabulary greedy192, true EOS2, no filters/penalties/repair/crop/rolling',
        python=sys.version,torch=torch.__version__,platform=platform.platform(),threads=1,precision='CPU FP32 deterministic')
    write(out/'receipt.json',receipt)
    if a.model!='r46':
        path=source_path(data['devTokensPath'])
        if sha(path)!=data['devTokensSha256']:raise ValueError('Frozen DEV tokens mismatch')
        values=np.memmap(path,dtype='<u4',mode='r')
        if len(data['devWindows'])!=64:raise ValueError('Expected64 fixed DEV windows')
        for j,row in enumerate(data['devWindows']):
            seq=list(map(int,values[row['offset']:row['offset']+row['length']]))
            scores=window_scores(model,seq,pieces)
            window_rows.append(dict(window=j,document=row['document'],startToken=row['startToken'],**scores))
    else:
        spec=importlib.util.spec_from_file_location('_v2_legacy_own_encoder',REPO/'training/dialogue/tokenizer.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        encode=lambda s:module.encode_stream(s,tok)
    for c in cases:
        if a.model=='r46':
            prefix=[1]+encode(c['prefixText']);gold=encode(c['targetText'])
            additive=encode(c['prefixText']+c['targetText'])==prefix[1:]+gold
            if b''.join(pieces[t]for t in prefix[1:])!=c['prefixText'].encode('utf8'):raise ValueError('Legacy prefix bytes differ')
        else:prefix=c['prefixTokens'];gold=c['goldTokens'];additive=True
        if b''.join(pieces[t]for t in gold)!=c['targetText'].encode('utf8'):raise ValueError('Human gold bytes differ')
        base=dict(id=c['id'],document=c['document'],endpoint=a.model,prefixText=c['prefixText'],prefixTokens=prefix,
            targetText=c['targetText'],goldTokens=gold,bodyUtf8Bytes=len(c['targetText'].encode('utf8')),
            sourceSha256=c['sourceSha256'],mode='human_dialogue_continuation',legacyConcatAdditive=additive,
            oldReferenceNotEqualExposure=a.model=='r46',history=c['history'],targetLocalRoleToken=c['targetLocalRoleToken'],
            prefixRawBytesHex=b''.join(pieces[t]for t in prefix).hex(),
            prefixTextPolicy='Readable source turns joined with newline; actual model input is prefixTokens, including native role/EOS markers for new series; raw bytes exclude empty special pieces')
        tf_supported=len(prefix)+len(gold)<=model.config['context']
        gen_supported=len(prefix)+192<=model.config['context']
        coverage.append(dict(id=c['id'],prefixTokens=len(prefix),bodyTokens=len(gold),teacherForcedSupported=tf_supported,
            full192GenerationSupported=gen_supported,selectedForGeneration=c['id']in ids,noCrop=True))
        logits=None
        if tf_supported:
            logits,scores=response_scores(model,prefix,gold,pieces)
            response_rows.append(dict(**base,supported=True,scores=scores))
        else:response_rows.append(dict(**base,supported=False,reason='Full prefix+body exceeds native context; no crop'))
        if c['id']in ids:
            if gen_supported:
                g=greedy(model,prefix,pieces,gold,logits,max_new=192)
                generated.append(dict(**base,generationSupported=True,**g))
            else:generated.append(dict(**base,generationSupported=False,reason='Full unchanged prefix+192 exceeds native context; no crop or smaller budget',tokensIncludingEos=None,text=None))
    rollouts=selfplay(model,cases,pieces,plan)if a.model!='r46'else[]
    if initial!=digest(model.state_dict())or not torch.equal(rng,torch.get_rng_state()):raise AssertionError('Inference changed model or RNG')
    metrics=dict(responseCases=summarize_responses(response_rows),
        windowMetrics=groups([t for r in window_rows for t in r['tokens']])if window_rows else None,
        scope='New-new same-tokenizer width comparison; legacy plain/old-tokenizer previously trained reference descriptive only. No token-NLL cross-tokenizer ranking.',
        generationCases=len(generated),generationSupported=sum(g['generationSupported']for g in generated),
        generatedEos=sum(g.get('eos',False)for g in generated),strictUtf8=sum(g.get('strictUtf8',False)for g in generated),
        limitations=['Single-source exposed DEV after use','R46 source exposure/format/tokenizer differ','Python raw inference only; no new JS export parity','Reference gold not unique; metrics do not replace whole-language reading'])
    write(out/'window-tf.json',window_rows);write(out/'response-tf.json',response_rows);write(out/'generations.json',generated)
    write(out/'coverage.json',coverage);write(out/'summary.json',metrics);write(out/'selfplay.json',rollouts)
    md=['# Unmodified human-dialogue continuations','',metrics['scope']]
    for g in generated:
        md.extend(['','## '+g['id'],'','Prefix:',fence(g['prefixText'])])
        if not g['generationSupported']:md.extend(['UNSUPPORTED: '+g['reason']]);continue
        md.extend(['Continuation:',fence(g['text']if g['strictUtf8']else g['rawBytesHex']),'All generated IDs including emitted EOS:',fence(json.dumps(g['tokensIncludingEos']))])
    for episode in rollouts:
        md.extend(['','## '+episode['id'],'A/B self-play stress only; no human interactive-response claim.','Original source history:',fence(episode['initialPrefixDisplayText'])])
        for row in episode['rows']:
            g=row['generation'];md.extend(['Turn '+str(row['turn'])+' role '+str(row['localRoleToken']),'Actual input IDs:',fence(json.dumps(row['inputTokens'])),'Dropped complete turns:',fence(json.dumps(row['droppedWholeTurns'],ensure_ascii=False)),'Continuation:',fence(g['text']if g['strictUtf8']else g['rawBytesHex']),'All generated IDs:',fence(json.dumps(g['tokensIncludingEos']))])
    (out/'ALL_GENERATIONS.md').write_text('\n'.join(md)+'\n')
    receipt.update(status='complete',elapsedSeconds=time.monotonic()-started,modelDigestBefore=initial,
        modelAndTorchRngUnchanged=True,checkpointUnchanged=sha(a.checkpoint)==a.checkpoint_sha256,
        windowRows=len(window_rows),responseRows=len(response_rows),generatedCases=len(generated),
        supportedGenerations=sum(g['generationSupported']for g in generated),selfplayEpisodes=len(rollouts),
        selfplayGeneratedTurns=sum(len(e['rows'])for e in rollouts),selfplayNotHumanInteractiveEvaluation=True)
    write(out/'receipt.json',receipt);print(json.dumps(receipt,ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--plan-sha256',required=True)
    p.add_argument('--model',choices=['small','medium','r46'],required=True);p.add_argument('--checkpoint',type=pathlib.Path,required=True)
    p.add_argument('--checkpoint-sha256',required=True);p.add_argument('--expected-updates',type=int)
    p.add_argument('--output',type=pathlib.Path,required=True);run(p.parse_args())
