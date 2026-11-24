"""Zero-update supplementary prefix diagnosis; never replaces main evaluation."""
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from next_runtime import D, N, read, write, sha, torch, load_study_model
from prose_decode import greedy


def main():
    plan_path = D/'WORD_BOUNDARY_DIAGNOSIS_PLAN.json'
    plan = read(plan_path)
    out = D/'WORD_BOUNDARY_DIAGNOSIS.json'
    assert not out.exists(), 'Preserve prior results'
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    pieces = [bytes.fromhex(t) for t in read(N.parent/'data/tokenizer.json')['bytes']]
    rows = []
    for name in plan['checkpoint_names']:
        model, cursor = load_study_model(name)
        model.eval()
        with torch.inference_mode():
            for case in plan['cases']:
                generated = greedy(model, case['word_complete_prefix'], pieces, max_new=128)
                rows.append(dict(model=name, cursor=cursor, id=case['id'],
                                 actual_prefix_text=case['actual_word_complete_prefix_text'],
                                 prefix_tokens=case['word_complete_prefix'], **generated))
        del model
    write(out, dict(plan_sha256=sha(plan_path), optimizer_updates=0,
                    diagnostic_only=True, main_evaluation_unchanged=True,
                    independent_human_evaluation=False, cases=rows))


if __name__ == '__main__':
    main()
