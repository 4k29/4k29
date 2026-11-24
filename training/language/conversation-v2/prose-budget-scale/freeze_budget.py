"""Freeze an uninterrupted continuation using already audited TRAIN archives."""
import gzip
import hashlib
import itertools
import json
import random
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
REPO = BASE.parents[2]
WIKI = 'modern-corpus/next-foundation/'
MIX = 'mixed-retention-study/'
hashes = {}

def load(path, lines=False):
    target = BASE/path
    data = subprocess.check_output(['git', 'show', f'HEAD:{target.relative_to(REPO)}'], cwd=REPO)
    hashes[path] = hashlib.sha256(data).hexdigest()
    if path.endswith('.gz'):
        data = gzip.decompress(data)
    return list(map(json.loads, data.splitlines())) if lines else json.loads(data)

def save(name, data):
    (ROOT/name).write_text(json.dumps(data, ensure_ascii=False, indent=1)+'\n')

def family(s):
    return re.sub(r'\s+', '', s.split('|')[-1]).casefold()

def grams(seq):
    return set(zip(*(seq[k:] for k in range(12))))

def main():
    rng = random.Random(12103)
    wiki = load(WIKI+'corpus.jsonl.gz', True)
    old_windows = load(WIKI+'schedule.json.gz')['batches']
    mix = load(MIX+'corpus.json.gz')
    mix_windows = load(MIX+'schedule.json.gz')
    pieces = list(map(bytes.fromhex, load('data/tokenizer.json')['bytes']))
    broad = load('broad-prose-replay/TRAIN.json')
    held = load('gv-prose-pilot/EVALUATION_INPUTS.json')
    replay_old = load('replay-study/REPLAY.json')
    monitor = load('replay-study/MONITOR.json')
    prefix_schedule = load('broad-prose-replay/SCHEDULE.json')['C']
    load('prose-lr-decay/PLAN.json')
    ledger = load('prose-lr-decay/C-ledger.json')
    checkpoint = load('prose-lr-decay/artifacts/C-300/checkpoint.json')
    assert len(ledger) == 150 and ledger[-1]['adam_step'] == 300 and ledger[-1]['lr'] == 1.65e-5
    history = defaultdict(set)
    for batch in old_windows:
        for w in batch:
            history[w['record']].update(range(w['start']+1,w['start']+w['length']))
    exposed_family = {family(wiki[i]['family']) for i in history}
    for batch in mix_windows:
        exposed_family.update(family(mix[w['record']]['family']) for w in batch)
    old_dev = held['prose']+load('broad-prose-replay/NEW_DEV.json')
    blocked = {family(r['family']) for r in old_dev}
    occupied = set()
    for row in broad+old_dev:
        occupied.update(grams(row.get('tokens') or row['prefix']+row.get('gold',[])))
    unsafe = re.compile(r'薬|医学|医療|銃|兵器|爆発|化学|生物|軍|病|高校理科|法学|著作権')
    fragments = re.compile(r'^(また、|例えば|たとえば|このように|そのため|したがって|しかし|他、|上記|以下|次に)|https?://|\{\{|\[\[|\|\||[–•]|^.{1,8}[:：]|\n.{1,8}[:：]')
    pools = defaultdict(list)
    rejects = Counter()
    for i,r in enumerate(wiki):
        if r['source'] not in ('jawikibooks','jawikivoyage','jaquad') or r['split'].lower() != 'train':
            continue
        f = family(r['family'])
        t = r['text']
        seq = r['tokens']
        if f in blocked or unsafe.search(f) or fragments.search(t) or not t.endswith('。'):
            rejects['family_or_fragment'] += 1
            continue
        if t.count('。') < 3 or len(seq)>256 or set(seq)&{0,1,2,3,4} or t.count('「')!=t.count('」'):
            rejects['length_or_structure'] += 1
            continue
        if not r.get('provenance') or b''.join(pieces[k] for k in seq)!=t.encode():
            rejects['provenance_or_reconstruction'] += 1
            continue
        ends = list(itertools.accumulate(len(pieces[k]) for k in seq))
        boundary = len((t.split('。',1)[0]+'。').encode())
        if boundary not in ends:
            rejects['boundary'] += 1
            continue
        n = ends.index(boundary)+1
        if n<10 or not 35 <= len(seq)-n <= 220:
            rejects['continuation_length'] += 1
            continue
        if grams(seq)&occupied:
            rejects['existing_12gram'] += 1
            continue
        pools[r['source']].append(dict(r, archive_index=i, prefix=seq[:n], gold=seq[n:],
                                       text_sha256=hashlib.sha256(t.encode()).hexdigest(),
                                       pr105_exposed_offsets=[k-n for k in sorted(history.get(i,())) if n<=k<len(seq)]))
    captions = load('modern-corpus/STAIR_DEV_FAMILIES.json')
    split = load('modern-corpus/STAIR_SPLIT_AUDIT.json')
    license_receipt = load('modern-corpus/STAIR_LICENSE_RECEIPT.json')
    assert 'CC-BY-4.0' in license_receipt['license']
    excluded = {r['id'] for r in split['held']+held['caption']+replay_old+monitor}
    images = set(captions['original_TRAIN_image_ids_reserved_for_DEV'])
    images.update(r['original_image_id'] for r in replay_old+monitor)
    texts = {r['text'] for r in replay_old+monitor}
    valid = {}
    for step,batch in enumerate(old_windows,1):
        for w in batch:
            i = w['record']
            r = wiki[i]
            if r['source']=='stair' and not w['start'] and w['length']==len(r['tokens']):
                valid[r['id']] = (r,step,'PR105')
    for step,batch in enumerate(mix_windows,1):
        for w in batch:
            r = mix[w['record']]
            if r['source']=='stair' and not w['start'] and w['length']==len(r['tokens']):
                valid[r['id']] = (r,step,'PR108')
    replay = []
    for i in rng.sample(sorted(valid),len(valid)):
        r,step,run=valid[i]
        image=r.get('original_image_id')
        if i in excluded or image is None or image in images or r['text'] in texts:
            continue
        seq=r['tokens']
        assert r['license']=='CC-BY-4.0' and seq[0]==1 and seq[-1]==2
        assert b''.join(pieces[k] for k in seq[1:-1])==r['text'].encode()
        assert hashlib.sha256(r['text'].encode()).hexdigest()==r['source_text_sha256']
        images.add(image)
        texts.add(r['text'])
        replay.append(dict(r, prefix=seq[:1],gold=seq[1:], past_exposure_run=run,past_exposure_step=step))
    print('prose', {k:(len(v),sum(len(r['gold']) for r in v),sum(family(r['family']) not in exposed_family for r in v)) for k,v in pools.items()})
    print('replay',len(replay),sum(len(r['gold']) for r in replay),'reject',rejects)
    dev = json.loads((ROOT/'HELDOUT.json').read_text()) if (ROOT/'HELDOUT.json').exists() else []
    for r in dev:
        assert family(r['family']) not in exposed_family
        occupied.update(grams(r['prefix']+r['gold']))
        blocked.add(family(r['family']))
    for source in pools:
        rng.shuffle(pools[source])
    total = 46012
    prose = []
    used = Counter()
    counts = Counter()
    for sources, budget in [(('jawikibooks','jawikivoyage'),5000),(('jaquad',),total-5000)]:
        left = budget
        for source in sources:
            for r in pools[source]:
                f = family(r['family'])
                seq = r['prefix']+r['gold']
                g = grams(seq)
                if f in blocked or g&occupied or used[f]>=500:
                    continue
                n = min(left,500-used[f],len(r['gold']))
                prose.append(dict(r,eligible_targets=n))
                occupied.update(g)
                used[f] += n
                counts[source] += n
                left -= n
                if not left:
                    break
            if not left:
                break
        assert not left, (sources,left)
    rng.shuffle(prose)
    def consume(records,amount,cursor):
        i, offset = cursor
        output = []
        while amount:
            length = records[i].get('eligible_targets',len(records[i]['gold']))
            count = min(amount,length-offset)
            output.append([i,offset,count])
            offset += count
            amount -= count
            if offset == length:
                i += 1
                offset = 0
        return output,(i,offset)
    prefix_prose = sum(sum(w[2] for w in b['prose']) for b in prefix_schedule)
    prefix_replay = sum(sum(w[2] for w in b['replay']) for b in prefix_schedule)
    assert (prefix_prose,prefix_replay)==(46013,46012)
    cursors = [(0,0),(0,0)]
    schedule = []
    cumulative = sum((prefix_prose,prefix_replay))
    for k in range(300):
        n = 307 if k<225 else 306
        r = (cumulative+n)//2-cumulative//2
        cumulative += n
        p,cursors[0] = consume(prose,n-r,cursors[0])
        q,cursors[1] = consume(replay,r,cursors[1])
        schedule.append(dict(prose=p,replay=q,denominator=n))
    replay = replay[:cursors[1][0]+bool(cursors[1][1])]
    save('TRAIN.json',prose)
    save('REPLAY.json',replay)
    save('SCHEDULE.json',schedule)
    save('AUDIT.json',dict(structural_exclusions=rejects,source_targets=counts,
         family_count=len(used),largest_family_targets=max(used.values()),
         prose_records=len(prose),replay_records=len(replay), replay_candidate_families=len(valid),
         replay_available_targets=sum(len(r['gold']) for r in replay),
         pr105_exposed=sum(sum(i<r['eligible_targets'] for i in r['pr105_exposed_offsets']) for r in prose),
         prior_exposure_scope='PR105 exact archive positions; absence is not proof of no other exposure',
         review='Previously accepted frozen TRAIN; inherited PR125 extraction filters and near duplicate exclusion. No new manual record-by-record adjudication.'))
    files=['TRAIN.json','REPLAY.json','SCHEDULE.json','AUDIT.json']
    if dev:
        files.append('HELDOUT.json')
    save('PLAN.json',dict(parent_checkpoint=checkpoint['sha256'],start=300,stop=600,
        target_4x_unmet_reason='The screened non-encyclopedic pool cannot sustain the balanced 4x mix; fixed 2x scope.',
        cumulative_targets=184050,prose=92025,replay=92025,lr=1.65e-5,clip=1.,seed=12103,
        evaluation=[300,450,600],checkpoint=[600],heldout_evaluation=[300,600] if dev else [],
        frozen={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files},inherited=hashes))
    (ROOT/'PLAN.sha256').write_text(hashlib.sha256((ROOT/'PLAN.json').read_bytes()).hexdigest()+'\n')


if __name__=='__main__':
    main()
