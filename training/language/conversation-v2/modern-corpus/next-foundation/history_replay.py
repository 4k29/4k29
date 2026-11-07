"""Post-training forensic replay of already fixed outputs; zero updates/selection."""
import pathlib
import sys
import math
import datetime
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from next_runtime import D, N, read, write, sha, torch, load_study_model
sys.path.insert(0, str(N.parent))
from new_tokenizer import Encoder


def main():
    out = D/'HISTORY_REPLAY.json'
    assert not out.exists()
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    tokenizer = read(N.parent/'data/tokenizer.json')
    pieces = [bytes.fromhex(t) for t in tokenizer['bytes']]
    encoder = Encoder(tokenizer)
    names = ['B-0', 'B-6361']
    files = {name: D/'evaluation'/f'{name}.json' for name in names}
    cases = {name: {c['id']: c for c in read(files[name])['cases']
                    if c['panel'] in ['old24', 'new-caption32']} for name in names}
    comparisons = []
    for identity, first in cases[names[0]].items():
        last = cases[names[1]][identity]
        assert first['prefix'] == last['prefix']
        if first['panel'] == 'old24':
            gold = first['reference_tokens']
        else:
            # EOS is the genuine original annotation boundary, never a window cut.
            full = [1] + encoder(first['source_reference_text']) + [2]
            assert full[:len(first['prefix'])] == first['prefix']
            gold = full[len(first['prefix']):]
        length = min(32, len(gold), *(len(cases[name][identity]['tokensIncludingEos']) for name in names))
        comparisons.append(dict(id=identity, panel=first['panel'], prefix=first['prefix'],
                                gold=gold[:length], common_positions=length))
    protocol = dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    posthoc_forensic_diagnosis=True, models=names,
                    original_result_SHA={name: sha(path) for name, path in files.items()},
                    cases=len(comparisons), positions=sum(c['common_positions'] for c in comparisons),
                    fixed_panels=['all old24', 'all new-caption32'], maximum_positions=32,
                    optimizer_updates=0,
                    scope='Jointly available positions in both saved generations; never replay past EOS. '
                          'Reference disagreement is not semantic failure because valid alternatives exist. '
                          'No new DEV, checkpoint choice, training adjustment or main-score change. '
                          'Pure-ASCII digit/whitespace piece mass is a limited spelling proxy.')
    write(D/'HISTORY_REPLAY_PROTOCOL.json', protocol)
    groups = {
        'digits': [i for i, p in enumerate(pieces) if p and all(b in b'0123456789' for b in p)],
        'whitespace': [i for i, p in enumerate(pieces) if p and all(b in b' \n\r\t' for b in p)],
    }
    rows = []
    for name in names:
        model, _ = load_study_model(name)
        model.eval()
        with torch.inference_mode():
            for case in comparisons:
                generated = cases[name][case['id']]['tokensIncludingEos']
                gold = case['gold']
                sequence = case['prefix'] + gold
                assert len(sequence) <= 256
                teacher = model(torch.tensor([sequence[:-1]], dtype=torch.long))[0]
                prefix_length = len(case['prefix'])
                for position, target in enumerate(gold):
                    history = case['prefix'] + generated[:position]
                    assert 2 not in generated[:position]
                    logits = model(torch.tensor([history], dtype=torch.long))[0, -1]
                    logp = torch.log_softmax(logits, -1)
                    teacher_logp = torch.log_softmax(teacher[prefix_length-1+position], -1)
                    probability = logp.exp()
                    row = dict(model=name, id=case['id'], panel=case['panel'], position=position,
                               target=target, saved_chosen=generated[position],
                               teacher_gold_NLL=-float(teacher_logp[target]),
                               self_history_gold_NLL=-float(logp[target]),
                               self_EOS_probability=float(probability[2]),
                               teacher_EOS_probability=float(teacher_logp[2].exp()),
                               saved_chosen_probability=float(probability[generated[position]]),
                               replay_argmax_matches_saved=int(logits.argmax()) == generated[position],
                               prior_history_already_differs=generated[:position] != gold[:position],
                               entropy=-float((probability*logp).sum()),
                               digit_probability_mass=float(probability[groups['digits']].sum()),
                               whitespace_probability_mass=float(probability[groups['whitespace']].sum()))
                    assert all(math.isfinite(value) for value in row.values() if isinstance(value, float))
                    rows.append(row)
        del model
    summary = {}
    for name in names:
        summary[name] = {}
        for panel in ['old24', 'new-caption32']:
            part = [r for r in rows if r['model'] == name and r['panel'] == panel]
            changed = [r for r in part if r['prior_history_already_differs']]
            summary[name][panel] = dict(positions=len(part),
                teacher_gold_NLL=sum(r['teacher_gold_NLL'] for r in part)/len(part),
                self_history_gold_NLL=sum(r['self_history_gold_NLL'] for r in part)/len(part),
                after_departure_positions=len(changed),
                after_departure_mean_NLL_penalty=sum(r['self_history_gold_NLL']-r['teacher_gold_NLL'] for r in changed)/max(1,len(changed)),
                self_mean_EOS_probability=sum(r['self_EOS_probability'] for r in part)/len(part),
                replay_argmax_disagreements=sum(not r['replay_argmax_matches_saved'] for r in part))
    write(out, dict(protocol_sha256=sha(D/'HISTORY_REPLAY_PROTOCOL.json'), optimizer_updates=0,
                    summary=summary, rows=rows, semantic_failure_onset_not_inferred=True))
    print(summary)


if __name__ == '__main__':
    main()
