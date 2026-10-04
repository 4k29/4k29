"""Own byte-level BPE. No external tokenizer files or learned vocabulary.

Vocabulary and merges are fitted on training strings only. Limiting pieces to
12 bytes prevents frequent complete answers becoming a single answer token.
"""
from collections import Counter
import unicodedata

SPECIALS = {'pad': 0, 'bos': 1, 'eos': 2, 'user': 3, 'assistant': 4, 'turn': 5}


def fit(texts, merges=384, max_piece_bytes=12):
    vocabulary = [b''] * len(SPECIALS) + [bytes([i]) for i in range(256)]
    sequences = Counter(tuple(byte+len(SPECIALS) for byte in text.encode('utf-8')) for text in texts)
    rules = []
    for _ in range(merges):
        counts = Counter()
        for tokens, weight in sequences.items():
            for pair in zip(tokens, tokens[1:]):
                if len(vocabulary[pair[0]])+len(vocabulary[pair[1]]) <= max_piece_bytes:
                    counts[pair] += weight
        if not counts:
            break
        pair, frequency = min(counts.items(), key=lambda item: (-item[1], item[0]))
        if frequency < 2:
            break
        token = len(vocabulary)
        vocabulary.append(vocabulary[pair[0]]+vocabulary[pair[1]])
        rules.append([*pair, token])
        updated = Counter()
        for tokens, weight in sequences.items():
            updated[tuple(merge(tokens, pair, token))] += weight
        sequences = updated
    return dict(schemaVersion=1, specials=SPECIALS, bytes=[piece.hex() for piece in vocabulary], merges=rules, maxPieceBytes=max_piece_bytes, note='Fitted on training strings only; no external tokenizer or vocabulary.')


def merge(tokens, pair, token):
    result, index = [], 0
    while index < len(tokens):
        if index+1 < len(tokens) and (tokens[index], tokens[index+1]) == tuple(pair):
            result.append(token)
            index += 2
        else:
            result.append(tokens[index])
            index += 1
    return result


def encode(text, tokenizer):
    tokens = [byte+len(SPECIALS) for byte in text.encode('utf-8')]
    for left, right, token in tokenizer['merges']:
        tokens = merge(tokens, (left, right), token)
    return tokens


def decode(tokens, tokenizer):
    return b''.join(bytes.fromhex(tokenizer['bytes'][token]) for token in tokens).decode('utf-8', errors='replace')


def prompt(question, history, tokenizer):
    normalize=lambda q:unicodedata.normalize('NFKC',q).lower()
    result = [SPECIALS['bos']]
    for turn in history:
        result += [SPECIALS['user']] + encode(normalize(turn['question']), tokenizer)
        result += [SPECIALS['assistant']] + encode(turn['answer'], tokenizer) + [SPECIALS['turn']]
    return result + [SPECIALS['user']] + encode(normalize(question), tokenizer) + [SPECIALS['assistant']]
