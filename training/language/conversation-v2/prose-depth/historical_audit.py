"""Check a second set of archived TRAIN inputs against the locked DEV families."""
import collections
import gzip
import json
import subprocess

from freeze import BASE,ROOT,read,dump,sha,labels,grams

PATHS=['mixed-retention-study/corpus.json.gz','mixed-volume-study/corpus.json.gz',
       'pretraining-scale/corpus.jsonl.gz','broad-prose-replay/TRAIN.json',
       'prose-budget-scale/TRAIN.json']

def main():
    families=[r for r in read(ROOT/'DEV.json') if r['panel']=='independent']
    index=collections.defaultdict(set)
    names=collections.defaultdict(set)
    collisions=collections.defaultdict(set)
    archives={}
    for r in families:
        for p in grams(r['prefix']+r['gold']):index[p].add(r['id'])
        for key in labels(r):names[key].add(r['id'])
    repo=ROOT.parents[3]
    for source in PATHS:
        path=(BASE/source).relative_to(repo)
        blob=subprocess.check_output(['git','show',f'HEAD:{path}'],cwd=repo)
        archives[source]=sha(blob)
        plain=gzip.decompress(blob) if source.endswith('.gz') else blob
        rows=map(json.loads,plain.splitlines()) if source.endswith('.jsonl.gz') else json.loads(plain)
        if isinstance(rows,dict):
            rows=rows['rows']
        for r in rows:
            for key in labels(r)&names.keys():
                for dev in names[key]:collisions[dev].add((source,'family'))
            ids=r.get('tokens') or r['prefix']+r['gold']
            for gram in grams(ids):
                for dev in index.get(gram,()):collisions[dev].add((source,'12-token'))
    dump(ROOT/'HISTORICAL_DEV_AUDIT.json',dict(archives=archives,collisions={k:sorted(v) for k,v in collisions.items()},
        result='Additional historical reach; panel membership remains fixed. No sealed data read.'))

if __name__=='__main__':
    main()
