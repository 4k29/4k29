"""Isolated exact-FP32 Python/JS parity, fixed short probes, zero updates.

This never exports decimal-rounded model weights or changes production code.
The source raw checkpoint fully reconstructs the temporary binary, which is
deleted after its hash is independently verified by the existing JS decoder.
"""
import argparse
import json
import pathlib
import subprocess
import time

import numpy as np
import torch

from core import HERE, REPO, decoder, digest, sha
from eval_core import byte_payload


def read(p):return json.loads(pathlib.Path(p).read_text())
def write(p,x):pathlib.Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')


def checkpoint(saved):
    if 'trajectory'in saved:
        return saved['trajectory']['config'],saved['trajectory']['model'],saved['trajectory']['uniqueUpdates']
    return saved['config'],saved.get('model',saved.get('state')),saved['uniqueUpdates']


def emit_binary(weights,binary):
    specs={};offset=0
    with binary.open('wb')as f:
        for name,tensor in sorted(weights.items()):
            if tensor.dtype!=torch.float32 or not bool(torch.isfinite(tensor).all()):raise ValueError('Finite raw FP32 only')
            array=tensor.detach().cpu().contiguous().numpy().astype('<f4',copy=False)
            f.write(array.tobytes(order='C'))
            specs[name]=dict(shape=list(tensor.shape),floatOffset=offset,floatCount=tensor.numel())
            offset+=tensor.numel()
    return specs,offset


@torch.inference_mode()
def py_greedy(model,prefix,max_new):
    emitted=[];steps=[]
    for j in range(max_new):
        inputs=prefix+emitted
        logits=model(torch.tensor([inputs],dtype=torch.long))[0,-1]
        if not bool(torch.isfinite(logits).all()):raise ValueError('Nonfinite Python logits')
        best=int(logits.argmax());top=logits.topk(2).values
        steps.append(dict(position=j,inputTokens=inputs,logits=logits.tolist(),argmax=best,topTwoLogitGap=float(top[0]-top[1])))
        emitted.append(best)
        if best==2:break
    return dict(tokensIncludingEos=emitted,eos=emitted[-1]==2,steps=steps)


def payload(generation,pieces):
    ids=generation['tokensIncludingEos'];body=ids[:-1]if generation['eos']else ids
    return {**generation,'nonEosTokens':body,**byte_payload(body,pieces),
        'stopReason':'trueEOS2'if generation['eos']else'fixed-four-token-probe-not-full-reply'}


def run(a):
    if sha(a.plan)!=a.plan_sha256:raise ValueError('Parity plan SHA mismatch')
    plan=read(a.plan)
    for path,expected in plan['codeReceipts'].items():
        p=(REPO/path).resolve()
        if not p.is_relative_to(REPO)or sha(p)!=expected:raise ValueError('Frozen parity source mismatch: '+path)
    training_path=REPO/plan['trainingPlanPath']
    if sha(training_path)!=plan['trainingPlanSha256']:raise ValueError('Frozen training plan mismatch')
    training=read(training_path);data_path=REPO/training['dataPath']
    if sha(data_path)!=training['dataSha256']:raise ValueError('Frozen data identity mismatch')
    data=read(data_path);bench_path=REPO/data['benchmarkPath']
    if sha(bench_path)!=plan['benchmarkSha256']:raise ValueError('Frozen cases mismatch')
    cases=read(bench_path)['cases']
    if [c['id']for c in cases[:3]]!=plan['caseIds']:raise ValueError('Exactly first three predeclared cases required')
    selected=cases[:3]
    if sha(a.checkpoint)!=a.checkpoint_sha256:raise ValueError('Exact source checkpoint SHA required')
    source_before=sha(a.checkpoint)
    saved=torch.load(a.checkpoint,map_location='cpu',weights_only=False)
    config,weights,step=checkpoint(saved)
    if step!=a.expected_updates or step not in plan['allowedUpdates']:raise ValueError('Unsupported fixed resource endpoint')
    if config!=training['models'][a.model]or saved['modelName']!=a.model:raise ValueError('Wrong own model')
    if saved['planSha256']!=plan['trainingPlanSha256']or saved['dataSha256']!=training['dataSha256']or saved['tokenizerSha256']!=data['tokenizerSha256']:
        raise ValueError('Model/data/tokenizer lineage mismatch')
    tokenizer_path=REPO/data['tokenizerPath']
    if sha(tokenizer_path)!=data['tokenizerSha256']:raise ValueError('Own tokenizer identity differs')
    tokenizer=read(tokenizer_path);pieces=[bytes.fromhex(x)for x in tokenizer['bytes']]
    if set(tokenizer['specials'].values())!=set(range(6)):raise ValueError('Exactly six original numeric special IDs required')
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    rng=torch.get_rng_state().clone();model=decoder(config);model.load_state_dict(weights);model.eval();torch.set_rng_state(rng)
    initial=digest(model.state_dict())
    output=a.output.resolve()
    if not output.is_relative_to(HERE)or output.exists():raise ValueError('New isolated output directory required')
    output.mkdir(parents=True)
    binary=output/'weights.f32';metadata=output/'weights-metadata.json';request=output/'node-request.json';js_path=output/'javascript.json'
    specs,count=emit_binary(weights,binary)
    binary_sha=sha(binary);started=time.monotonic()
    write(metadata,dict(binaryPath=str(binary),bytes=count*4,binarySha256=binary_sha,tensors=specs,config=config,
        tokenizer=tokenizer,checkpointSha256=a.checkpoint_sha256))
    py_rows=[];requests=[]
    for case in selected:
        prefix=case['prefixTokens']
        if prefix[0]!=1 or len(prefix)>64 or len(prefix)+plan['maxNewTokens']>config['context']:
            raise ValueError('Full original prefix must fit without any crop')
        g=py_greedy(model,prefix,plan['maxNewTokens'])
        py_rows.append(dict(id=case['id'],prefixTokens=prefix,prefixText=case['prefixText'],generation=payload(g,pieces)))
        requests.append(dict(id=case['id'],prefixTokens=prefix,pythonHistoryInputs=[r['inputTokens']for r in g['steps']]))
    write(output/'python.json',py_rows)
    write(request,dict(metadataPath=str(metadata),expectedRunnerSha256=sha(HERE/'parity.mjs'),maxNewTokens=plan['maxNewTokens'],cases=requests))
    process=subprocess.run(['node',str(HERE/'parity.mjs'),str(request),str(js_path)],text=True,capture_output=True)
    (output/'node.log').write_text(process.stdout+process.stderr)
    if process.returncode!=0:raise RuntimeError('JS parity execution failed; raw temporary weights retained for audit')
    js=read(js_path)
    if js['binarySha256']!=binary_sha or not js['rawBinaryExactVerified']:raise AssertionError('Binary hash not independently verified')
    comparisons=[]
    for py,jr in zip(py_rows,js['rows'],strict=True):
        if py['id']!=jr['id']:raise AssertionError('Case order differs')
        rows=[];py_gen=py['generation'];js_gen=payload(jr['independentAutoregression'],pieces)
        pids=py_gen['tokensIncludingEos'];jids=js_gen['tokensIncludingEos']
        first=next((i for i,(p,j)in enumerate(zip(pids,jids))if p!=j),None)
        if first is None and len(pids)!=len(jids):first=min(len(pids),len(jids))
        for p,j in zip(py_gen['steps'],jr['referencePythonHistoryScores'],strict=True):
            if p['inputTokens']!=j['inputTokens']:raise AssertionError('Same-history input differs')
            pl=np.array(p['logits'],dtype=np.float64);jl=np.array(j['logits'],dtype=np.float64)
            error=float(np.max(np.abs(pl-jl)))
            rows.append(dict(position=p['position'],inputTokens=p['inputTokens'],maximumAbsoluteLogitError=error,
                withinFrozenTolerance=error<=plan['absoluteLogitTolerance'],pythonArgmax=p['argmax'],javascriptArgmax=j['argmax'],
                argmaxAgreement=p['argmax']==j['argmax'],pythonTopTwoGap=p['topTwoLogitGap'],javascriptTopTwoGap=j['topTwoLogitGap'],
                nearTieComparedWithObservedError=min(p['topTwoLogitGap'],j['topTwoLogitGap'])<=2*error,
                sameNativeAutoregressiveHistory=first is None or p['position']<=first))
        comparisons.append(dict(id=py['id'],prefixTokens=py['prefixTokens'],prefixText=py['prefixText'],
            referencePathComparisons=rows,firstIndependentAutoregressiveDeparture=first,
            pythonRawGeneration=py_gen,javascriptRawGeneration=js_gen,
            interpretation='All forced comparisons use identical Python-path inputs; native histories shared only through departure prediction. Full independent short paths retained.'))
    rows=[r for c in comparisons for r in c['referencePathComparisons']]
    if initial!=digest(model.state_dict())or not torch.equal(rng,torch.get_rng_state())or sha(a.checkpoint)!=source_before:
        raise AssertionError('Model/RNG/source checkpoint changed')
    receipt=dict(scope=plan['scope'],model=a.model,selectedUniqueUpdates=step,planSha256=a.plan_sha256,
        trainingPlanSha256=plan['trainingPlanSha256'],checkpointSha256=a.checkpoint_sha256,
        binarySha256=binary_sha,binaryBytes=count*4,binaryIndependentlyHashVerified=True,
        temporaryBinaryDeletedAfterVerification=True,parametersWritten=count,actualOptimizerUpdates=0,
        originalCheckpointModelAndTorchRngUnchanged=True,threads=1,torch=torch.__version__,node=js['node'],
        cases=len(comparisons),comparisonPositions=len(rows),maximumAbsoluteLogitError=max(r['maximumAbsoluteLogitError']for r in rows),
        tolerance=plan['absoluteLogitTolerance'],toleranceExceedances=sum(not r['withinFrozenTolerance']for r in rows),
        sameHistoryArgmaxDisagreements=sum(not r['argmaxAgreement']for r in rows),
        independentAutoregressiveDivergentCases=sum(c['firstIndependentAutoregressiveDeparture']is not None for c in comparisons),
        weightConversion='Exact little-endian IEEE754 FP32; no decimal rounding',
        full192All32ParityEstablished=False,elapsedSeconds=time.monotonic()-started,comparisons=comparisons)
    write(output/'receipt.json',receipt)
    binary.unlink()
    print(json.dumps({k:v for k,v in receipt.items()if k!='comparisons'},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=pathlib.Path,required=True);p.add_argument('--plan-sha256',required=True)
    p.add_argument('--model',choices=['small','medium'],required=True);p.add_argument('--checkpoint',type=pathlib.Path,required=True)
    p.add_argument('--checkpoint-sha256',required=True);p.add_argument('--expected-updates',type=int,choices=[256,512],required=True)
    p.add_argument('--output',type=pathlib.Path,required=True);run(p.parse_args())
