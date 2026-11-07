"""Offline SHA verification. --write is for intentionally updating the artifact inventory."""
import argparse, hashlib, json, pathlib
H=pathlib.Path(__file__).resolve().parent;ROOT=H.parents[3]
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        while b:=f.read(1024**2):h.update(b)
    return h.hexdigest()
def inventory():
    files=[p for p in H.rglob('*')if p.is_file()and '__pycache__'not in p.parts and p.name!='MANIFEST.json'and p.suffix not in ['.pt','.pending','.pyc']]
    files += [H.parent/p for p in ['core.py','new_tokenizer.py','eval_core.py','parity.py','parity.mjs','PLAN.json','data/tokenizer.json','epoch1/content-dev.json','response-data/final/active-dev.json','foundation-data/research/zero_update_preflight.py','response-data/sources/acquire_jmultiwoz.py']]
    files += [H.parent.parent/'model.py',H.parent.parent/'round10/word_bpe.py',ROOT/'training/dialogue/tokenizer.py',ROOT/'training/dialogue/inference.mjs',ROOT/'GOAL.md',ROOT/'.github/workflows/grounded-objective.yml']
    return {p.relative_to(ROOT).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p))for p in sorted(set(files))}
def verify():
    expected=json.loads((H/'MANIFEST.json').read_text())
    for name,want in expected.items():
        p=ROOT/name
        assert p.stat().st_size==want['bytes']and sha(p)==want['sha256'],name
    for p in (H/'run').glob('*/archive/checkpoint.json'):
        m=json.loads(p.read_text());h=hashlib.sha256();n=0
        for c in m['chunks']:
            data=(p.parent/c['path']).read_bytes();assert len(data)==c['bytes']and hashlib.sha256(data).hexdigest()==c['sha256'];h.update(data);n+=len(data)
        assert n==m['bytes']and h.hexdigest()==m['sha256']
    print('Verified',len(expected),'source/artifact SHAs and six complete checkpoint byte streams')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    if args.write:(H/'MANIFEST.json').write_text(json.dumps(inventory(),indent=2)+'\n')
    verify()
if __name__=='__main__':main()
