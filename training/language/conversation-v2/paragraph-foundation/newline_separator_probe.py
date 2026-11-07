"""Read-only fixed-B next-token probe on the previously fixed eight TRAIN histories."""
import argparse
import hashlib
import json
import pathlib
import sys

P = pathlib.Path(__file__).resolve().parent

def sha(path):
    h = hashlib.sha256()
    with pathlib.Path(path).open('rb') as f:
        while b := f.read(1048576):
            h.update(b)
    return h.hexdigest()

def conditions(history, nl):
    assert len(history) >= 3 and history[-2:] == [nl, nl]
    one = history[:-1]
    # Same token IDs, but remove the first LF's position rather than the last.
    gap_positions = list(range(len(history)-2)) + [len(history)-1]
    return {'LF2': (list(history), list(range(len(history)))),
            'LF1': (one, list(range(len(one)))),
            'LF1_same_final_position': (one, gap_positions)}

def rank(values, target):
    """1-based minimum rank for ties, no arbitrary ID tie breaking."""
    return 1 + sum(v > values[target] for v in values)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--out', type=pathlib.Path, default=P/'newline-followup/single-lf')
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    assert not (a.out/'RESULTS.json').exists(), 'Never overwrite a completed probe'
    audit_path = P/'newline-followup/EIGHT_CASE_AUDIT.json'
    audit = json.loads(audit_path.read_text())
    assert len(audit['cases']) == 8
    tok_path = P.parent/'data/tokenizer.json'
    pieces = [bytes.fromhex(s) for s in json.loads(tok_path.read_text())['bytes']]
    manifest_path = P/'artifacts/B-579/checkpoint.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['sha256'] == '3cebff9801302bd9969601e539adccaca7e0ea83943cc96bf2dc0b35f0906b9c'
    watched = [audit_path, tok_path, manifest_path, P/'PLAN.json', P/'ACTUAL_UPDATES_B.jsonl', P/'NEWLINE_COLLAPSE_DIAGNOSIS.json']
    before = {str(p): sha(p) for p in watched}
    protocol = dict(cases='The same eight in EIGHT_CASE_AUDIT.json, no reselection',
        checkpoint_sha256=manifest['sha256'], conditions=['LF2', 'LF1', 'LF1_same_final_position'],
        interpretation='After LF1 the next original TRAIN token is the second LF, so predicting LF is not an error. Original non-LF continuation gold is retained as a counterfactual edited-input comparison.',
        supplementary_position_control='Remove first LF while keeping original absolute positions of every surviving token. Gapped positions are diagnostic-only, not standard inference or proposed production repair.',
        expected_next_token_forward_calls=25, optimizer_updates=0, generation_runs=0,
        probability='Temperature1 full-vocabulary softmax from raw FP32 logits; probabilities accumulated in FP64; ranks use strict greater-than (minimum tie rank).',
        historical_probability_reproduction_tolerance=1e-5,
        selection_or_tuning_after_results=False, input_sha256=before, script_sha256=sha(__file__))
    (a.out/'PROTOCOL.json').write_text(json.dumps(protocol, indent=2)+'\n')
    import torch
    from torch.nn import functional as F
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    sys.path.insert(0, str(P.parent))
    import core
    assert sha(a.checkpoint) == manifest['sha256']
    obj = torch.load(a.checkpoint, map_location='cpu', weights_only=False)
    assert core.digest(obj) == manifest['full_state_digest']
    assert obj['active_cursor'] == 579
    with torch.random.fork_rng(devices=[]):
        model = core.decoder(obj['trajectory']['config'])
    model.load_state_dict(obj['trajectory']['model'], strict=True)
    model.eval()
    del obj
    initial_model_hash = core.digest(model.state_dict())
    calls = 0
    def forward(ids, positions=None):
        nonlocal calls
        calls += 1
        t = torch.tensor([ids], dtype=torch.long)
        if positions is None:
            return model(t)[0,-1]
        x = model.token(t) + model.position(torch.tensor(positions, dtype=torch.long))
        for block in model.blocks:
            x = block(x)
        return F.linear(model.norm(x), model.token.weight)[0,-1]
    rows = []
    with torch.inference_mode():
        for case in audit['cases']:
            history = case['history_tokens']
            gold = case['gold']
            nl = 16
            variants = conditions(history, nl)
            raw = bytes.fromhex(case['history_raw_hex'])
            assert b''.join(pieces[t] for t in history) == raw
            assert raw.endswith(b'\n\n')
            assert case['original_tokens'][case['source_offset']-1] == nl
            predictions = {}
            for name, (ids, pos) in variants.items():
                changed_raw = b''.join(pieces[t] for t in ids)
                assert changed_raw == (raw if name == 'LF2' else raw[:-1])
                assert ids[:-1] == (history[:-1] if name == 'LF2' else history[:-2])
                log = forward(ids, pos if name == 'LF1_same_final_position' else None)
                values = log.tolist()
                prob = log.double().softmax(-1).tolist()
                top = int(log.argmax())
                predictions[name] = dict(input_tokens=ids, position_ids=pos, input_length=len(ids), last_query_position=pos[-1],
                    raw_hex=changed_raw.hex(), P_newline=prob[nl], rank_newline=rank(values,nl),
                    P_original_nonnewline_gold=prob[gold], rank_original_nonnewline_gold=rank(values,gold),
                    argmax=top, argmax_piece_hex=pieces[top].hex(), argmax_piece_text=pieces[top].decode('utf-8',errors='replace'))
                if name == 'LF2':
                    saved = case['predictions']['B-579']
                    assert top == saved['argmax']
                    assert abs(prob[nl]-saved['P_newline']) <= 1e-5
                    assert abs(prob[gold]-saved['P_gold']) <= 1e-5
                    if case['index'] == 0:
                        explicit = forward(ids, pos)
                        assert torch.equal(log, explicit), 'Position-control path differs from normal forward'
            rows.append(dict(index=case['index'], source_id=case['source_id'], source_offset=case['source_offset'],
                original_nonnewline_gold=gold, gold_piece_text=case['gold_piece_text'],
                original_TRAIN_gold_after_LF1=nl, original_TRAIN_gold_after_LF2=gold,
                original_saved_prediction=case['predictions']['B-579'], predictions=predictions))
    assert calls == 25
    assert core.digest(model.state_dict()) == initial_model_hash
    assert sha(a.checkpoint) == manifest['sha256']
    assert before == {str(p):sha(p) for p in watched}
    summary = {name:dict(newline_argmax=sum(r['predictions'][name]['argmax']==16 for r in rows),
        mean_P_newline=sum(r['predictions'][name]['P_newline']for r in rows)/8,
        mean_P_original_nonnewline_gold=sum(r['predictions'][name]['P_original_nonnewline_gold']for r in rows)/8)
        for name in variants}
    out = dict(protocol_sha256=sha(a.out/'PROTOCOL.json'), checkpoint_sha256=manifest['sha256'],
        summary=summary, cases=rows, model_forward_calls=calls, optimizer_updates=0,
        new_model_series_created=0, checkpoint_and_model_tensors_unchanged=True,
        input_and_BPE_token_identity_checks_pass=True, default_vs_explicit_position_path_exact=True,
        historical_LF2_max_probability_delta=max(abs(r['predictions']['LF2']['P_newline']-r['original_saved_prediction']['P_newline'])for r in rows),
        independent_evaluation=False, new_generation_or_ability_benchmark=False)
    (a.out/'RESULTS.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False))

if __name__ == '__main__':
    main()
