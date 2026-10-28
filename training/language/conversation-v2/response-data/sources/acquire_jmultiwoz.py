"""Official mixed container: select declared TRAIN/DEV, lexically skip TEST.

The compressed container and temporary decompressed bytes necessarily include
TEST. TEST values are never JSON-decoded, semantically inspected or emitted.
Do not describe this as 'TEST bytes never processed'. No remote code executes.
"""
import datetime
import gzip
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

HERE = Path(__file__).resolve().parent
TMP = Path('/dev/shm/response-jmultiwoz')
REV = 'a78dd334b907e12318b76bb23d0a9ed1498b8d15'
BASE = 'https://raw.githubusercontent.com/nu-dialogue/jmultiwoz/' + REV + '/'
GIT_BLOB = 'd5652056febc647bd5907aadd39ce39fe2ea2702'


def sha(b):
    return hashlib.sha256(b).hexdigest()


def fetch(url, limit):
    with urllib.request.urlopen(urllib.request.Request(url, headers={
            'User-Agent': '4k29-conversation-research/1.0'}), timeout=90) as r:
        b = r.read(limit+1)
        if len(b) > limit:
            raise ValueError('Bounded download exceeded')
        return b


def members(blob):
    """Yield top-level object key and raw value bytes without decoding value.

    Each value must be an object/array. The lexical scanner tracks quoted
    strings and escapes; braces inside text cannot end the source record.
    """
    n = len(blob)
    i = 0
    def whitespace(pos):
        while pos < n and blob[pos] in b' \t\r\n':
            pos += 1
        return pos
    i = whitespace(i)
    if i >= n or blob[i] != 123:
        raise ValueError('Expected top-level object')
    i += 1
    while True:
        i = whitespace(i)
        if i < n and blob[i] == 125:
            if whitespace(i+1) != n:
                raise ValueError('Trailing data')
            return
        if i >= n or blob[i] != 34:
            raise ValueError('Expected member key')
        start = i
        i += 1
        escaped = False
        while i < n:
            c = blob[i]
            i += 1
            if escaped:
                escaped = False
            elif c == 92:
                escaped = True
            elif c == 34:
                break
        else:
            raise ValueError('Unterminated key')
        key = json.loads(blob[start:i])
        i = whitespace(i)
        if i >= n or blob[i] != 58:
            raise ValueError('Expected colon')
        i = whitespace(i+1)
        if i >= n or blob[i] not in (123, 91):
            raise ValueError('Expected structured member')
        start = i
        stack = []
        quoted = escaped = False
        while i < n:
            c = blob[i]
            i += 1
            if quoted:
                if escaped:
                    escaped = False
                elif c == 92:
                    escaped = True
                elif c == 34:
                    quoted = False
            elif c == 34:
                quoted = True
            elif c in (123, 91):
                stack.append(c)
            elif c in (125, 93):
                if not stack or stack.pop() != (123 if c == 125 else 91):
                    raise ValueError('Mismatched container')
                if not stack:
                    yield key, blob[start:i]
                    break
        else:
            raise ValueError('Unterminated member')
        i = whitespace(i)
        if i < n and blob[i] == 44:
            i += 1
        elif i >= n or blob[i] != 125:
            raise ValueError('Expected member separator')


def validate_splits(split):
    assert set(split) == {'train', 'dev', 'test'}
    sets = {k: set(v) for k, v in split.items()}
    assert all(len(sets[k]) == len(split[k]) for k in sets)
    assert not (sets['train'] & sets['dev'] or sets['train'] & sets['test']
                or sets['dev'] & sets['test'])
    return sets


def main():
    TMP.mkdir(exist_ok=True)
    evidence = {}
    for name in ['README.md', 'LICENSE', 'dataset/README.md']:
        b = fetch(BASE+name, 100000)
        path = HERE/('jmultiwoz-'+name.replace('/', '-'))
        path.write_bytes(b)
        evidence[name] = dict(url=BASE+name, sha256=sha(b))
    readme = (HERE/'jmultiwoz-README.md').read_text()
    assert 'Models trained using the dataset are not considered copies' in readme
    archive = TMP/'JMultiWOZ_1.0.zip'
    if not archive.exists():
        archive.write_bytes(fetch(BASE+'dataset/JMultiWOZ_1.0.zip', 12000000))
    b = archive.read_bytes()
    assert len(b) == 11016438
    assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest() == GIT_BLOB
    with zipfile.ZipFile(archive) as z:
        split_raw = z.read('JMultiWOZ_1.0/split_list.json')
        splits = json.loads(split_raw)
        sets = validate_splits(splits)
        assert {k: len(v) for k,v in sets.items()} == {'train':3646, 'dev':300, 'test':300}
        raw = z.read('JMultiWOZ_1.0/dialogues.json')
    outputs = {}
    counters = {'train':0, 'dev':0, 'test_lexically_skipped':0}
    seen = set()
    try:
        for split in ['train', 'dev']:
            f = (TMP/(split+'.jsonl.gz')).open('wb')
            outputs[split] = (f, gzip.GzipFile(fileobj=f, mode='wb', mtime=0))
        for key, value_bytes in members(raw):
            assert key not in seen
            seen.add(key)
            if key in sets['test']:
                counters['test_lexically_skipped'] += 1
                continue
            which = 'train' if key in sets['train'] else 'dev' if key in sets['dev'] else None
            assert which is not None
            d = json.loads(value_bytes)
            assert d['dialogue_name'] == key
            outputs[which][1].write((json.dumps({'official_split':which,
                'source_id':key, 'source_object_sha256':sha(value_bytes), 'data':d},
                ensure_ascii=False, separators=(',',':'))+'\n').encode())
            counters[which] += 1
    finally:
        for f,z in outputs.values():
            z.close()
            f.close()
    assert seen == sets['train'] | sets['dev'] | sets['test']
    assert counters == {'train':3646, 'dev':300, 'test_lexically_skipped':300}
    (HERE/'jmultiwoz-split-list.json').write_bytes(split_raw)
    receipt = dict(repository='nu-dialogue/jmultiwoz', revision=REV,
        license='CC-BY-SA-4.0', checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        rights_evidence=evidence, container_url=BASE+'dataset/JMultiWOZ_1.0.zip',
        container_bytes=len(b), container_sha256=sha(b), container_git_blob=GIT_BLOB,
        container_persisted_in_repository=False, split_sha256=sha(split_raw),
        counts=counters, test_dialogue_values_json_decoded=0, test_dialogues_emitted=0,
        test_byte_processing='container fetched; mixed dialogue bytes decompressed and lexically skipped; no semantic inspection/evaluation/training',
        outputs={s:dict(tmpfs_path=str(TMP/(s+'.jsonl.gz')),
                       bytes=(TMP/(s+'.jsonl.gz')).stat().st_size,
                       sha256=sha((TMP/(s+'.jsonl.gz')).read_bytes())) for s in ['train','dev']},
        publication_admitted=False, training_admitted=False,
        warning='Raw selected TRAIN/DEV still require privacy/individual rights/quality audit before any Git publication')
    (HERE/'jmultiwoz-acquisition.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k:receipt[k] for k in ['counts','outputs','test_byte_processing']},ensure_ascii=False))


if __name__ == '__main__':
    main()
