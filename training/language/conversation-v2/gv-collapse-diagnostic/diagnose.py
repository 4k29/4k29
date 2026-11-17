"""Replay archived histories in FP32, without updating weights or changing decoding."""
import hashlib
import json
from pathlib import Path
import sys

P = Path(__file__).resolve().parent
V = P.parent
OLD = V / 'gv-prose-pilot'
sys.path[:0] = [str(V), str(V / 'foundation-data/research')]
import torch
from core import decoder
from zero_update_preflight import load_checkpoint

def read(path):
    return json.loads(path.read_text())

def main():
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    plan = read(P / 'PLAN.json')
    for relative, expected in plan['inputs'].items():
        assert hashlib.sha256((V / relative).read_bytes()).hexdigest() == expected
    inputs = read(OLD / 'EVALUATION_INPUTS.json')['prose']
    pieces = [bytes.fromhex(s) for s in read(V / 'data/tokenizer.json')['bytes']]
    labels = read(OLD / 'SEMANTIC_REVIEW.json')['cases']
    blank_ids = [i for i, p in enumerate(pieces) if p and set(p) == {32}]
    results, forwards = [], 0
    with torch.inference_mode():
        for name, ref in plan['models'].items():
            manifest = V / ref['path']
            state = load_checkpoint(manifest, ref['sha'])
            model = decoder(state['trajectory']['config']).eval()
            model.load_state_dict(state['trajectory']['model'])
            del state
            archived = {r['id']: r for r in read(OLD / 'evaluation' / f'{name}.json')['cases']}
            judgments = {r['id']: r for r in labels[name]}
            for case in inputs:
                raw = archived[case['id']]
                prefix, gold = case['prefix'], case['teacher_continuation']
                generated = raw['tokensIncludingEos']
                assert prefix == raw['prefix']
                repetition = raw['repeated4gram']
                paths = {}
                for kind, continuation in [('gold', gold), ('self', generated)]:
                    sequence = prefix + continuation[:-1]
                    assert len(sequence) <= 256
                    logits = model(torch.tensor([sequence]))[0, len(prefix)-1:]
                    forwards += 1
                    probabilities = logits.double().softmax(-1)
                    steps = []
                    for j, prob in enumerate(probabilities):
                        top = prob.topk(10)
                        g = gold[j] if j < len(gold) else None
                        steps.append(dict(position=len(prefix)-1+j, history_tokens=len(prefix)+j,
                            argmax=int(top.indices[0]), top10=list(zip(top.indices.tolist(),top.values.tolist())),
                            p_gold=float(prob[g]) if g is not None else None,
                            p_eos=float(prob[2]), p_lf=float(prob[16]), p_ascii_space=float(prob[blank_ids].sum()),
                            repeat_token_probabilities={str(t):float(prob[t]) for t in set(repetition['tokens'])} if repetition else {}))
                    paths[kind] = steps
                mismatches = [j for j, step in enumerate(paths['self']) if step['argmax'] != generated[j]]
                exact = {}
                if repetition:
                    for j in sorted({repetition['repeatStart'], repetition['completion']}):
                        logit = model(torch.tensor([prefix + generated[:j]]))[0,-1]
                        forwards += 1
                        exact[j] = dict(argmax=int(logit.argmax()), archived=generated[j],
                                        max_top10_probability_difference=max(abs(float(logit.double().softmax(-1)[t])-p) for t,p in paths['self'][j]['top10']))
                results.append(dict(model=name,id=case['id'],panel=case['panel'], prefix=prefix,
                    divergence=raw['firstGoldDeparturePosition'], repeat=repetition, judgment=judgments[case['id']],
                    generated=generated,raw_bytes=raw['rawBytesHex'],text=raw['text'],stop=raw['stopReason'],
                    maximum_history=len(prefix)+len(generated)-1,paths=paths, archived_argmax_mismatches=mismatches,
                    exact_history_probes=exact))
    (P / 'DIAGNOSTIC.json').write_text(json.dumps(dict(optimizer_calls=0,forwards=forwards,cases=results),ensure_ascii=False,separators=(',',':'))+'\n')

if __name__ == '__main__':
    main()
