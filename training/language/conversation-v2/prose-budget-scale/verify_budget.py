"""Verify the frozen schedule, optimizer receipt, raw evaluation and Git checkpoint."""
import gzip
import hashlib
import io
import json
import subprocess
from collections import Counter
from run_budget import ROOT, BASE, plan, prose, replay, schedule, parent, read, torch, batch_for
from freeze_budget import grams, family

def digest(data):
    return hashlib.sha256(data).hexdigest()

def git_blob(path):
    repo = ROOT.parents[3]
    return subprocess.check_output(['git','show',f'HEAD:{path.relative_to(repo)}'],cwd=repo)

def recover(folder):
    manifest = read(folder/'checkpoint.json')
    buffer = io.BytesIO()
    checksum = hashlib.sha256()
    for part in manifest['chunks']:
        data = git_blob(folder/part['path'])
        assert len(data)==part['bytes'] and digest(data)==part['sha256']
        checksum.update(data)
        buffer.write(data)
    assert checksum.hexdigest()==manifest['sha256'] and buffer.tell()==manifest['bytes']
    buffer.seek(0)
    return torch.load(buffer,map_location='cpu',weights_only=False)['trajectory']

def main():
    for path,d in plan['inherited'].items():
        assert digest(git_blob(BASE/path))==d
    pieces = [bytes.fromhex(t) for t in read(BASE/'data/tokenizer.json')['bytes']]
    previous_prose = read(BASE/'broad-prose-replay/TRAIN.json')
    excluded_prose = set().union(*(grams(r['prefix']+r['gold']) for r in previous_prose))
    heldout = read(ROOT/'HELDOUT.json')[0]
    excluded_prose.update(grams(heldout['prefix']+heldout['gold']))
    for row in prose:
        tokens = row['prefix']+row['gold']
        assert family(row['family'])!=family(heldout['family'])
        assert b''.join(pieces[t] for t in tokens).decode()==row['text']
        assert not set(tokens)&{0,1,2,3,4}
        assert not excluded_prose&grams(tokens)
        excluded_prose.update(grams(tokens))
    previous_replay = read(BASE/'replay-study/REPLAY.json')+read(BASE/'replay-study/MONITOR.json')
    images = {r['original_image_id'] for r in previous_replay}
    texts = {r['source_text_sha256'] for r in previous_replay}
    for row in replay:
        assert row['original_image_id'] not in images and row['source_text_sha256'] not in texts
        assert row['prefix']==[1] and row['gold'][-1]==2 and row['license']=='CC-BY-4.0'
        images.add(row['original_image_id'])
        texts.add(row['source_text_sha256'])
    seen=set()
    labels=Counter()
    for k,batch in enumerate(schedule,301):
        total = 307 if k<=525 else 306
        assert batch['denominator']==total
        x,y,group,denominator=batch_for('C',k)
        assert denominator==total and int(y.ne(-100).sum())==total and x.size(1)<=256
        assert torch.equal(y.ne(-100),group.ge(0))
        assert abs(sum(x[2] for x in batch['prose'])-sum(x[2] for x in batch['replay']))<=1
        assert sum(w[2] for side in ('prose','replay') for w in batch[side])==total
        for side,records in [('prose',prose),('replay',replay)]:
            for i,start,count in batch[side]:
                row=records[i]
                assert 0<=start<start+count<=row.get('eligible_targets',len(row['gold']))
                assert len(row['prefix'])+start+count<=256
                for pos in range(start,start+count):
                    identifier=(side,row['id'],pos)
                    assert identifier not in seen
                    seen.add(identifier)
                    labels[side]+=1
    assert labels=={'prose':46012,'replay':46013}
    old = recover(parent)
    new = recover(ROOT/'artifacts/C-600')
    assert old['uniqueUpdates']==300 and new['uniqueUpdates']==600
    rows=read(ROOT/'LEDGER.json')
    assert new['history']==old['history']+rows
    for k,(row,batch) in enumerate(zip(rows,schedule,strict=True),301):
        assert row['step']==row['step_adam']==k and row['lr']==plan['lr'] and not row['nonfinite']
        for side in ('prose','replay'):
            assert row[side]==sum(x[2] for x in batch[side])
        assert abs(row['prose_loss']+row['replay_loss']-row['loss'])<1e-5
    for k,state in ((300,old),(600,new)):
        assert {int(x['step']) for x in state['optimizer']['state'].values()}=={k}
    assert read(ROOT/'RESUME.json')['row']==rows[0]
    calls=[json.loads(line) for line in (ROOT/'CALL_JOURNAL.jsonl').read_text().splitlines()]
    assert calls[::2]==[dict(x,event='begin') for x in calls[1::2]]
    assert Counter(x['kind'] for x in calls[1::2])=={'retained':300,'witness':1}
    for name,n in [('C-450',71),('C-600',71),('heldout-300',1),('heldout-600',1)]:
        panel=json.loads(gzip.decompress((ROOT/f'{name}.json.gz').read_bytes()))
        assert len(panel['cases'])==n
        for row in panel['cases']:
            seq=row['generated']
            assert not row['forced'] and seq==[s['top5'][0][0] for s in row['steps']]
            assert b''.join(pieces[t] for t in seq).hex()==row['raw_hex']
            assert len(seq)<=row['budget']
    print('PASS 300 unique scheduled updates, 301 optimizer calls, two cold-restored states, raw evaluations')

if __name__=='__main__':
    main()
