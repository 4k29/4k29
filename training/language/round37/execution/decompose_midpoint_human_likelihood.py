"""Canonical likelihood on human everyday DEV only. Reserved TEST stays closed.
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
p.add_argument('--raw-cache', type=pathlib.Path, default=pathlib.Path('/workspace/daily-conversation-source-audit/human-only-raw'))
p.add_argument('--reuse-exact', action='store_true')
a = p.parse_args(); ev.torch.set_num_threads(1)
sha = lambda b: hashlib.sha256(b).hexdigest()
meta_root = R.parent / 'round28/prospective-daily-source'
meta_raw = gzip.decompress((meta_root / 'human-source-acquisition.json.gz').read_bytes())
meta = json.loads(meta_raw)
fold_raw = (meta_root / 'prospective-speaker-folds.json').read_bytes()
assert sha(fold_raw) == meta['foldPolicySha256']
folds = json.loads(fold_raw)['speakerFolds']
tok_raw = (R / 'multiview/tokenizer.json').read_bytes(); tok = json.loads(tok_raw)
source_rows = [row for row in meta['records'] if row['fold'] == 'development']
assert len(source_rows) == 99
windows = []; documents = []; target_count = 0; token_hash = hashlib.sha256()
for row in source_rows:
    assert all(folds[s] == 'development' for s in row['speakers'])
    raw = (a.raw_cache / 'development' / pathlib.PurePosixPath(row['sourcePath']).name).read_bytes()
    assert sha(raw) == row['sha256']
    dialogue = json.loads(raw)
    # Keep each human utterance unchanged; insert one newline between turns, no role/profile text.
    text = '\n'.join(u['text'] for u in dialogue['utterances'])
    tokens = [ev.SPECIALS['bos']] + ev.encode_stream(text, tok) + [ev.SPECIALS['eos']]
    before = target_count
    for lo in range(1, len(tokens), 192):
        hi = min(lo + 192, len(tokens)); start = max(0, lo - 1 - 64)
        x = tokens[start:hi-1]
        y = [-100 if start+1+i < lo else t for i, t in enumerate(tokens[start+1:hi])]
        assert len(x) == len(y) <= 256
        assert sum(t != -100 for t in y) == hi-lo
        target_count += hi-lo
        windows.append((len(documents), x, y))
    assert target_count-before == len(tokens)-1
    token_hash.update(json.dumps(tokens, separators=(',', ':')).encode())
    documents.append(dict(dialogueId=row['dialogueId'], sourceSha256=row['sha256'], serializedTextSha256=sha(text.encode()), serializedUtf8Bytes=len(text.encode()), targetTokensIncludingEos=len(tokens)-1))
identity = dict(modelSha256=sha(a.model.read_bytes()), evaluatorSha256=sha(pathlib.Path(__file__).read_bytes()), rawEvaluatorSha256=sha((R.parent / 'round10/evaluate.py').read_bytes()), sourceManifestSha256=sha(meta_raw), foldPolicySha256=sha(fold_raw), tokenizerSha256=sha(tok_raw), orderedCanonicalTokensSha256=token_hash.hexdigest(), serialization='unchanged utterance texts joined by single newline; no role/persona insertion', window='context256, newTargets192, upTo64 prior input tokens; each target including terminalEOS exactly once', evaluationThreads=1, batchSize=8)
if a.reuse_exact and a.out.exists():
    cached = json.loads(a.out.read_text()); assert cached['identity'] == identity
    assert cached['documents'] == 99 and cached['targetTokensIncludingEos'] == target_count
    print(json.dumps(dict(reusedExactHumanDevLikelihood=True, resultSha256=sha(a.out.read_bytes()), developmentDialogues=99)), flush=True)
    raise SystemExit(0)
checkpoint = ev.torch.load(a.model, map_location='cpu', weights_only=False)
assert checkpoint['step'] == 5000 and sorted({int(x['step']) for x in checkpoint['optimizer']['state'].values()}) == [25000]
model = ev.Decoder(checkpoint['config']); model.load_state_dict(checkpoint['model']); model.eval()
export = dict(tokenizer=tok)
# Full checkpoint SHA identifies the raw model file including moments; no export/JS parity claim.
assert export['tokenizer'] == tok and model.config['context'] == 256
losses = [0.0] * len(documents); counted = [0] * len(documents)
piece_bytes = [bytes.fromhex(x) for x in tok['bytes']]
assert piece_bytes[16] == b'\n'
compound_newline = ev.torch.tensor([i >= 6 and i != 16 and b'\n' in b for i,b in enumerate(piece_bytes)])
category_totals = {k: dict(targets=0, negativeLogLikelihoodSum=0.0) for k in ['standaloneNewline16','compoundNewlineToken','originalDialogueEos','otherOriginalContent']}
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
        safe = y.clamp_min(0)
        masks = dict(standaloneNewline16=y.eq(16), compoundNewlineToken=y.ge(6) & compound_newline[safe], originalDialogueEos=y.eq(2))
        masks['otherOriginalContent'] = y.ne(-100) & ~masks['standaloneNewline16'] & ~masks['compoundNewlineToken'] & ~masks['originalDialogueEos']
        assert sum(int(mask.sum()) for mask in masks.values()) == int(y.ne(-100).sum())
        for name,mask in masks.items():
            category_totals[name]['targets'] += int(mask.sum())
            category_totals[name]['negativeLogLikelihoodSum'] += float(ce[mask].sum())
        for i, (doc_index, _, _) in enumerate(batch):
            losses[doc_index] += float(ce[i].sum()); counted[doc_index] += int(y[i].ne(-100).sum())
assert counted == [d['targetTokensIncludingEos'] for d in documents]
for i, d in enumerate(documents): d['negativeLogLikelihoodSum'] = losses[i]
total_bytes = sum(d['serializedUtf8Bytes'] for d in documents)
report = dict(rawCheckpointStep=5000, rawFp32Checkpoint=True, numericalScope='Raw Python FP32 only; no interim JS or rounded export claim', identity=identity, partition='human everyday development; NOT TEST', documents=99, windows=len(windows), targetTokensIncludingEos=target_count, serializedUtf8Bytes=total_bytes, negativeLogLikelihoodSum=sum(losses), nllPerSerializedUtf8Byte=sum(losses)/total_bytes, lossPerTargetTokenIncludingEos=sum(losses)/target_count, eosContributesLossButZeroSerializedBytes=True, modelTrainingUpdates=0, optimizerInstantiated=False, modelMode='eval/no_grad', usedForCheckpointSelection=False, originalStrictGateChanged=False, reservedTestRead=False, sourceNotUsedByRound26Training=True, elapsedSeconds=time.monotonic()-begun, rows=documents)
assert sum(x['targets'] for x in category_totals.values()) == target_count
for x in category_totals.values():
    x['lossPerTarget'] = x['negativeLogLikelihoodSum']/x['targets'] if x['targets'] else None
    x['contributionPerSerializedUtf8Byte'] = x['negativeLogLikelihoodSum']/total_bytes
assert abs(sum(x['negativeLogLikelihoodSum'] for x in category_totals.values())-sum(losses)) < 0.1
report['originalGoldTokenCategories'] = category_totals
report['categoryCaution'] = 'Token classes, not character likelihood or meaning; compound-newline tokens may also contain content. All original contexts and targets unchanged; no gate or selector replacement.'
a.out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['rows', 'identity']}, ensure_ascii=False), flush=True)
