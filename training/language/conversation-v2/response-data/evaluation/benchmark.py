"""Prepare-only, source-grounded content DEV. No model/optimizer imports.

Exact evidence/slot checks are integrity aids, never semantic language scoring.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoder():
    spec = importlib.util.spec_from_file_location('response_eval_own_bpe', V2/'new_tokenizer.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    tok = json.loads((V2/'data/tokenizer.json').read_text())
    return m.Encoder(tok), tok


def validate_case(case, source):
    if case['source']['split'] != 'DEV' or source['split'] != 'DEV':
        raise ValueError('Only original official DEV permitted')
    if case['source']['dialogue_id'] != source['dialogue_name']:
        raise ValueError('Wrong source dialogue')
    by_id = {t['turn_id']: t for t in source['turns']}
    for evidence in case['evidence']:
        turn = by_id.get(evidence['turn_id'])
        if turn is None:
            raise ValueError('Unknown source turn')
        if evidence['kind'] == 'utterance':
            text = turn['utterance']
            start, end = evidence['start'], evidence['end']
            if not (0 <= start < end <= len(text)) or text[start:end] != evidence['quote']:
                raise ValueError('Evidence offset/quote mismatch')
        elif evidence['kind'] == 'source-field':
            value = turn
            for key in evidence['path']:
                value = value[key]
            if value != evidence['value']:
                raise ValueError('Source field mismatch')
        else:
            raise ValueError('Unknown evidence type')
    if not case['required_content']:
        raise ValueError('Acknowledgement-only case is not content-required')
    for slot in case['required_content']:
        if not slot['evidence_indices']:
            raise ValueError('Content slot needs evidence')
        if any(i < 0 or i >= len(case['evidence']) for i in slot['evidence_indices']):
            raise ValueError('Unknown slot evidence')
        if not slot['source_values'] or any(not str(v).strip() for v in slot['source_values']):
            raise ValueError('Empty content value')
    if case.get('gold_authorship') not in ('original-human-response', 'no-generated-gold-verbatim-source-slots'):
        raise ValueError('Unapproved gold provenance')
    return True


def prepare(cases):
    enc, tok = encoder()
    vocab = [bytes.fromhex(x) for x in tok['bytes']]
    prepared = []
    for case in cases:
        prompt = case['prompt']
        body = enc(prompt)
        if b''.join(vocab[i] for i in body) != prompt.encode():
            raise ValueError('BPE roundtrip failure')
        prefix = [1, 3] + body + [2, 4]
        budget = case['generation']['max_new_tokens']
        if len(prefix) + budget > 256:
            raise ValueError('No truncation allowed: context budget exceeded')
        prepared.append({'id': case['id'], 'input_ids': prefix,
                         'prefix_tokens': len(prefix), 'max_new_tokens': budget,
                         'prompt_sha256': sha(prompt.encode())})
    return prepared


if __name__ == '__main__':
    cases = json.loads((HERE/'dev.json').read_text())['cases']
    prepared = prepare(cases)
    result = {'cases': len(prepared), 'prepared': prepared, 'model_calls': 0,
              'optimizer_updates': 0, 'inference_authorized': False,
              'tokenizer_sha256': sha((V2/'data/tokenizer.json').read_bytes())}
    (HERE/'prepare.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
