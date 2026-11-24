"""Stream verified tmpfs checkpoint parts into Git without a duplicate disk archive.

Only new epoch1 archive paths are written. Each part is checked against the
source manifest, staged, checked through Git, and excluded from this workspace
afterwards. Git objects remain authoritative and are pushed with the draft PR.
"""
import argparse, hashlib, json, pathlib, subprocess

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[3]

def checksum(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()

def archive(source, name):
    source=pathlib.Path(source); record=json.loads(source.read_text())
    destination=HERE/name/'archive'; destination.mkdir(parents=True,exist_ok=True)
    target_manifest=destination/source.name
    if target_manifest.exists():raise ValueError('Refuse to replace an archived checkpoint')
    combined=hashlib.sha256(); total=0; receipts=[]
    for part in record['chunks']:
        src=source.parent/part['path']; dst=destination/part['path']
        if not dst.resolve().is_relative_to(destination.resolve()):raise ValueError('Unsafe part path')
        if src.stat().st_size!=part['bytes'] or checksum(src)!=part['sha256']:raise ValueError('Source part mismatch')
        if dst.exists():raise ValueError('Refuse archive overwrite')
        dst.parent.mkdir(parents=True,exist_ok=True)
        relative=str(dst.relative_to(REPO))
        # Stream directly to the object store: even a temporary40MiB working
        # copy would exceed the final remaining disk margin.
        with src.open('rb') as f:
            blob=subprocess.check_output(['git','hash-object','-w','--stdin'],cwd=REPO,stdin=f,text=True).strip()
        subprocess.run(['git','update-index','--add','--cacheinfo','100644',blob,relative],cwd=REPO,check=True)
        h=hashlib.sha256(); size=0
        process=subprocess.Popen(['git','cat-file','blob',blob],cwd=REPO,stdout=subprocess.PIPE)
        for b in iter(lambda:process.stdout.read(1048576),b''):
            h.update(b);combined.update(b);size+=len(b);total+=len(b)
        process.stdout.close()
        if process.wait()!=0 or h.hexdigest()!=part['sha256'] or size!=part['bytes']:raise ValueError('Staged Git blob differs')
        # Exclude only this verified, fully reproducible workspace copy.
        subprocess.run(['git','update-index','--skip-worktree','--',relative],cwd=REPO,check=True)
        patterns=REPO/'.git/info/sparse-checkout'
        with patterns.open('a') as f:f.write('!/'+relative+'\n')
        receipts.append(dict(path=relative,gitBlob=blob,bytes=size,sha256=h.hexdigest()))
    if total!=record['bytes'] or combined.hexdigest()!=record['sha256']:raise ValueError('Whole archive differs')
    target_manifest.write_text(json.dumps(record,indent=2)+'\n')
    receipt=dict(model=name,manifest=str(target_manifest.relative_to(REPO)),sha256=record['sha256'],bytes=total,
        gitPartsVerified=True,workspacePartsSparse=True,parts=receipts,
        restore='git sparse-checkout disable (requires sufficient storage); then use round46/checkpoint_chunks.py restore on this manifest')
    (destination/'git-archive-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    subprocess.run(['git','add','--',str(target_manifest.relative_to(REPO)),str((destination/'git-archive-receipt.json').relative_to(REPO))],cwd=REPO,check=True)
    print(json.dumps(receipt))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=pathlib.Path,required=True);p.add_argument('--model',choices=['small','medium'],required=True)
    a=p.parse_args();archive(a.manifest,a.model)
