"""Own-BPE length/fallback metrics, source message IDs counted once per source."""
import collections
import gzip
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]


def main():
    tok = json.loads((HERE.parent/'data/tokenizer.json').read_text())
    result = {}
    for name in ['conversations.jsonl.gz', 'oasst-conversations.jsonl.gz']:
        path = HERE/'derived'/name
        docs = [json.loads(line) for line in gzip.open(path, 'rt')]
        unique = {u['id']: u for d in docs for u in d['utterances']}
        values = list(unique.values())
        lengths = sorted(u['body_tokens'] for u in values)
        text = ''.join(u['text'] for u in values)
        unknown = collections.Counter(c for c in text if c not in tok['glyphTokenIds'])
        result[docs[0]['source']] = {
            'unique_utterances': len(values),
            'body_token_quantiles': {str(q): lengths[math.ceil(len(lengths)*q)-1]
                                     for q in [.5, .9, .99]},
            'characters': len(text), 'body_tokens': sum(lengths),
            'characters_per_body_token': len(text)/sum(lengths),
            'unknown_training_glyph_occurrences': sum(unknown.values()),
            'unknown_training_glyph_types': len(unknown),
            'meaning': 'unknown glyphs use own byte/glyph fallback, not UNK; quantiles are utterance lengths, not whole conversation context fit',
            'derived_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
    (HERE/'research/token-length-audit.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
