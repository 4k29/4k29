"""Canonical likelihood on fixed99 human TRAIN split units; diagnostic only.
Separate diagnostic; never a checkpoint selector or training target.
"""
import argparse, gzip, hashlib, importlib.util, json, pathlib, sys, time
R = pathlib.Path(__file__).resolve().parents[1]
E = R / 'execution'
sys.path.insert(0, str(R.parent / 'round10'))
spec = importlib.util.spec_from_file_location('raw_evaluation', R.parent / 'round10/evaluate.py')
ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)
p = argparse.ArgumentParser()
p.add_argument('--model', type=pathlib.Path, required=True)
p.add_argument('--out', type=pathlib.Path, required=True)
p.add_argument('--reuse-exact', action='store_true')
a = p.parse_args(); ev.torch.set_num_threads(1)
sha = lambda b: hashlib.sha256(b).hexdigest()
result=R/'continue-10000/result.json'
assert result.exists()and json.loads(result.read_text())['completedRun']and json.loads(result.read_text())['completedSteps']==10000,'Human TRAIN gap waits for actual10000 completion'
import numpy as np
plan_raw=(E/'human-train-gap-plan.json').read_bytes();plan=json.loads(plan_raw);index_raw=(R/'multiview/train.index.json').read_bytes();assert sha(index_raw)==plan['trainIndexSha256'];assert sha((R/'sources/documents.jsonl').read_bytes())==plan['sourceDocumentsSha256'];info=json.loads(index_raw);assert info['tokensSha256']==plan['trainTokensSha256'];values=np.memmap(R/'multiview/train.tokens.bin',dtype='<u4',mode='r');source={d['originalDocument']:d for d in map(json.loads,(R/'sources/documents.jsonl').read_text().splitlines())};tok_raw=(R/'multiview/tokenizer.json').read_bytes();tok=json.loads(tok_raw);assert sha(tok_raw)==plan['tokenizerSha256'];windows=[];documents=[];target_count=0;token_hash=hashlib.sha256()
for row in plan['selectedUnits']:
    u=source[row['sourceDocument']];assert u['partition']=='train'and row['variant']==0 and row['site']=='human-chat';text=u['text'];tokens=[ev.SPECIALS['bos']]+ev.encode_stream(text,tok)+[ev.SPECIALS['eos']];assert tokens==list(map(int,values[row['offset']:row['offset']+row['length']]));before=target_count
    for lo in range(1,len(tokens),192):
        hi=min(lo+192,len(tokens));start=max(0,lo-1-64);x=tokens[start:hi-1];y=[-100 if start+1+i<lo else t for i,t in enumerate(tokens[start+1:hi])];assert len(x)==len(y)<=256;assert sum(t!=-100 for t in y)==hi-lo;target_count+=hi-lo;windows.append((len(documents),x,y))
    assert target_count-before==len(tokens)-1;token_hash.update(json.dumps(tokens,separators=(',',':')).encode());documents.append(dict(sourceDocument=row['sourceDocument'],sourceSha256=u['sourceSha256'],serializedTextSha256=sha(text.encode()),serializedUtf8Bytes=len(text.encode()),targetTokensIncludingEos=len(tokens)-1))
identity=dict(modelSha256=sha(a.model.read_bytes()),evaluatorSha256=sha(pathlib.Path(__file__).read_bytes()),rawEvaluatorSha256=sha((R.parent/'round10/evaluate.py').read_bytes()),planSha256=sha(plan_raw),sourceManifestSha256=plan['sourceManifestSha256'],sourceDocumentsSha256=plan['sourceDocumentsSha256'],trainIndexSha256=plan['trainIndexSha256'],tokenizerSha256=sha(tok_raw),orderedCanonicalTokensSha256=token_hash.hexdigest(),serialization='unchanged utterance texts joined by single newline; no role/profile insertion',window='context256, newTargets192, upTo64 prior input tokens; each target including terminalEOS exactly once',evaluationThreads=1,batchSize=8)
if a.reuse_exact and a.out.exists():
    cached = json.loads(a.out.read_text()); assert cached['identity'] == identity
    assert cached['documents'] == 99 and cached['targetTokensIncludingEos'] == target_count
    print(json.dumps(dict(reusedExactHumanTrainLikelihood=True, resultSha256=sha(a.out.read_bytes()), trainingSplitUnits=99)), flush=True)
    raise SystemExit(0)
model, export = ev.load_model(a.model)
assert export['tokenizer'] == tok and model.config['context'] == 256
losses = [0.0] * len(documents); counted = [0] * len(documents)
begun = time.monotonic()
with ev.torch.no_grad():
    for offset in range(0, len(windows), 8):
        batch = windows[offset:offset+8]; width = max(len(x) for _, x, _ in batch)
        x = ev.torch.zeros((len(batch), width), dtype=ev.torch.long)
        y = ev.torch.full_like(x, -100)
        for i, (_, inputs, targets) in enumerate(batch):
            x[i, :len(inputs)] = ev.torch.tensor(inputs); y[i, :len(targets)] = ev.torch.tensor(targets)
        logits = model(x)
        ce = ev.torch.nn.functional.cross_entropy(logits.reshape(-1, model.config['vocabulary']), y.reshape(-1), reduction='none').reshape_as(y)
        for i, (doc_index, _, _) in enumerate(batch):
            losses[doc_index] += float(ce[i].sum()); counted[doc_index] += int(y[i].ne(-100).sum())
assert counted == [d['targetTokensIncludingEos'] for d in documents]
for i, d in enumerate(documents): d['negativeLogLikelihoodSum'] = losses[i]
total_bytes = sum(d['serializedUtf8Bytes'] for d in documents)
report = dict(identity=identity, partition='fixed human TRAIN split sample99; not full TRAIN mean', documents=99, windows=len(windows), targetTokensIncludingEos=target_count, serializedUtf8Bytes=total_bytes, negativeLogLikelihoodSum=sum(losses), nllPerSerializedUtf8Byte=sum(losses)/total_bytes, lossPerTargetTokenIncludingEos=sum(losses)/target_count, eosContributesLossButZeroSerializedBytes=True, modelTrainingUpdates=0, optimizerInstantiated=False, modelMode='eval/no_grad', usedForCheckpointSelection=False, originalStrictGateChanged=False, reservedTestRead=False, trainingSplitDoesNotImplyAllTargetsSeen=True, sourceModelEvaluatedStep=(export['training']['evaluatedStep'] if 'evaluatedStep' in export['training'] else export['training']['bestStep']), elapsedSeconds=time.monotonic()-begun, rows=documents)
a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['rows', 'identity']}, ensure_ascii=False), flush=True)
