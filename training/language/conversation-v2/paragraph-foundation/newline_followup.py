"""Eight saved newline failures: actual production packing/CE, no model or updates.
Run from any directory. Reuses saved predictions rather than loading checkpoints.
"""
import ast
import gzip
import hashlib
import json
import pathlib

P = pathlib.Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def production_function(path, name, namespace):
    tree = ast.parse(path.read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    # Execute the unchanged function body without importing training/loader modules.
    module = ast.Module(body=[node], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), 'exec'), namespace)
    return namespace[name]

def main():
    import torch
    from torch.nn import functional as F
    torch.set_num_threads(2)
    out = P / 'newline-followup'
    out.mkdir(exist_ok=True)
    tracked = [P/'PLAN.json', P/'NEWLINE_COLLAPSE_DIAGNOSIS.json', P/'corpus.jsonl.gz', P/'schedule.json.gz']
    tracked += sorted(P.rglob('*ACTUAL_UPDATES*.jsonl'))
    tracked += sorted(P.rglob('checkpoint.json'))
    tracked = [f for f in tracked if 'private' not in f.parts]
    before = {str(f.relative_to(P)): sha(f) for f in tracked}
    diagnosis = json.loads((P/'NEWLINE_COLLAPSE_DIAGNOSIS.json').read_text())
    corpus = [json.loads(s) for s in gzip.open(P/'corpus.jsonl.gz', 'rt')]
    schedule = json.load(gzip.open(P/'schedule.json.gz', 'rt'))
    tokenizer_path = P.parent/'data/tokenizer.json'
    pieces = [bytes.fromhex(s) for s in json.loads(tokenizer_path.read_text())['bytes']]
    nl = diagnosis['newline_token_id']
    assert nl == 16 and pieces[nl] == b'\n' and pieces[0] == b''
    pack_path = P.parent/'modern-corpus/next_runtime.py'
    ce_path = P.parent/'core.py'
    pack = production_function(pack_path, 'pack', {'torch': torch})
    ce = production_function(ce_path, 'causal_ce', {'torch': torch, 'F': F})
    # Deterministic subset of the pre-existing hash-ordered32, no outcome reranking.
    chosen = diagnosis['models']['B-579']['true_TRAIN_two_newline_events'][:8]
    results = []
    for index, event in enumerate(chosen):
        matches = []
        for bi, refs in enumerate(schedule['arms']['B']):
            for ri, ref in enumerate(refs):
                if corpus[ref['record']]['id'] == event['source_id'] and ref['start'] < event['source_offset'] < ref['start']+ref['length']:
                    matches.append((bi, ri, ref, refs))
        assert len(matches) == 1
        bi, ri, ref, refs = matches[0]
        original = corpus[ref['record']]
        full = original['tokens']
        assert b''.join(pieces[t] for t in full) == original['text'].encode('utf-8')
        rows = [{'tokens':corpus[r['record']]['tokens'][r['start']:r['start']+r['length']]} for r in refs]
        x, y = pack(rows)
        # Independent whole-batch source-position oracle, not just the chosen label.
        for k, r in enumerate(refs):
            raw = corpus[r['record']]['tokens'][r['start']:r['start']+r['length']]
            n = len(raw)-1
            assert x[k,:n].tolist() == raw[:-1]
            assert y[k,:n].tolist() == raw[1:]
            assert bool(x[k,n:].eq(0).all()) and bool(y[k,n:].eq(-100).all())
        j = event['source_offset']-ref['start']
        slot = j-1
        assert full[event['source_offset']] == event['gold'] == int(y[ri,slot]) != nl
        assert x[ri,slot-1:slot+1].tolist() == [nl,nl]
        assert int(y[ri,slot-1]) == nl and int(y[ri,slot]) != -100
        n = len(rows[ri]['tokens'])-1
        assert y[ri,:n].ne(-100).all() and not y[ri,:n].eq(0).any()
        raw_history = b''.join(pieces[t] for t in x[ri,:slot+1].tolist())
        assert raw_history.endswith(b'\n\n')
        predictions = {}
        for model, saved in diagnosis['models'].items():
            same = [e for e in saved['true_TRAIN_two_newline_events'] if (e['source_id'],e['source_offset']) == (event['source_id'],event['source_offset'])]
            assert len(same) == 1 and same[0]['gold'] == int(y[ri,slot])
            predictions[model] = dict(same[0], argmax_piece_hex=pieces[same[0]['argmax']].hex())
        results.append(dict(index=index, source_id=event['source_id'], source_url=original.get('url',original.get('source_url')), source_offset=event['source_offset'], batch_update=bi+1, row=ri,
            original_tokens=full, actual_ref=ref, original_window_start=(ref['start']//256)*256,
            shortened_history=ref['start']%256 != 0,
            input_tokens_with_padding=x[ri].tolist(), teacher_tokens_with_ignore=y[ri].tolist(), loss_mask=y[ri].ne(-100).tolist(),
            target_logit_position=slot, gold=event['gold'], gold_piece_hex=pieces[event['gold']].hex(), gold_piece_text=pieces[event['gold']].decode('utf-8',errors='replace'),
            history_tokens=x[ri,:slot+1].tolist(), history_raw_hex=raw_history.hex(), history_text=raw_history.decode('utf-8',errors='replace'),
            following_original_text=b''.join(pieces[t] for t in full[event['source_offset']:event['source_offset']+50]).decode('utf-8',errors='replace'),
            padding_positions=x.shape[1]-n, genuine_target_count=n, predictions=predictions,
            correct_shift=True, target_active=True, padding_targets_ignored=True, no_newline_relabeling=True, no_boundary_teacher_override=True))
    # Actual CE must ignore PAD logits, even when they strongly favor newline.
    labels = torch.tensor([[chosen[0]['gold'],-100]])
    logits = torch.zeros((1,2,len(pieces)))
    initial = ce(logits, labels)
    logits[0,1,nl] = 100
    assert torch.equal(initial, ce(logits, labels))
    assert torch.allclose(initial, F.cross_entropy(logits[0,:1], labels[0,:1]))
    # Operator-only causal padding check; no model instantiated, no weights loaded.
    q = torch.arange(12,dtype=torch.float32).reshape(1,1,4,3)/10
    v = q.flip(-1)
    a = F.scaled_dot_product_attention(q[:,:,:2],q[:,:,:2],v[:,:,:2],is_causal=True)
    b = F.scaled_dot_product_attention(q,q,v,is_causal=True)[:,:,:2]
    assert torch.allclose(a,b,atol=1e-6,rtol=1e-6)
    assert before == {str(f.relative_to(P)):sha(f) for f in tracked}
    summary = dict(selection='First8 of existing hash-ordered32 true TRAIN failures, fixed before inspection; not random population estimate or new DEV',cases=8,
        padded_rows=sum(r['padding_positions']>0 for r in results), shortened_history_rows=sum(r['shortened_history'] for r in results),
        model_prediction_counts={name:dict(newline_argmax=sum(r['predictions'][name]['argmax']==nl for r in results),mean_P_newline=sum(r['predictions'][name]['P_newline'] for r in results)/8) for name in diagnosis['models']},
        all_source_shift_mask_checks_pass=True,actual_CE_padding_invariance_pass=True,operator_causal_right_padding_pass=True,
        newline_containing_vocabulary=[dict(id=i,hex=b.hex())for i,b in enumerate(pieces)if b'\n' in b],
        source_sha256={str(f):sha(f)for f in [pack_path,ce_path,tokenizer_path,P/'train.py',P.parent.parent/'model.py',P/'newline_followup.py']},
        immutable_artifact_SHA_before_and_after=before, actual_optimizer_updates=0,model_forward_calls=0,new_models_created=0,new_corpora_acquired=0,
        saved_predictions_reused=True,bug_found_in_eight_cases=False,
        limitations='Only8 saved events, unchanged stored predictions; does not rule out every implementation fault or prove a unique learned cause. Existing context-shortening issue is retained, not newly repaired or trained here.')
    (out/'EIGHT_CASE_AUDIT.json').write_text(json.dumps(dict(summary=summary,cases=results),ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:summary[k]for k in ['cases','padded_rows','shortened_history_rows','model_prediction_counts','all_source_shift_mask_checks_pass','actual_optimizer_updates']},ensure_ascii=False))

if __name__ == '__main__':
    main()
