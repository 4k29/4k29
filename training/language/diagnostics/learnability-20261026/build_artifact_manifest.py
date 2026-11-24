"""Hash the final bundle; omit this manifest and its final verification report."""
import hashlib,json,pathlib
H=pathlib.Path(__file__).resolve().parent
def sha(p):
    h=hashlib.sha256()
    with p.open('rb')as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()
files={str(p.relative_to(H)):sha(p)for p in sorted(H.rglob('*'))if p.is_file()and'__pycache__'not in p.parts
    and p.suffix not in ['.pt','.pyc']and p.name not in ['artifact-manifest.json','verification.json']}
(H/'artifact-manifest.json').write_text(json.dumps({'scope':'Final diagnostic bundle, no adoption; manifest and final self-verification excluded to avoid circular hashes','files':files},indent=2)+'\n')
print(len(files))
