"""Rebuild the licensed dataset in a fresh directory; does not train a model."""
import argparse,pathlib,subprocess,sys,hashlib,json,shutil
p=argparse.ArgumentParser();p.add_argument('--v2-root',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--source-cache',type=pathlib.Path);a=p.parse_args();source=pathlib.Path(__file__).resolve().parent;out=a.output.resolve();assert not out.exists(),'Use new output directory; never overwrite original evidence';out.mkdir(parents=True)
# Pin source revision independently of mutable remote trees; download only when user invokes reproduction.
(out/'asdc-tree.json').write_text(json.dumps({'sha':'f37d6575c73602adcb8ae3687520726793baa672'}))
if a.source_cache:
 evidence=json.loads((source/'ACQUISITION.json').read_text())
 for f in evidence['files']:assert hashlib.sha256((a.source_cache/f['path']).read_bytes()).hexdigest()==f['sha256']
 shutil.copytree(a.source_cache,out/'asdc')
for name in ['acquire_asdc.py','inventory.py','retrieve_candidates.py','pre_review.py','adopt.py','prepare_run.py']:
 if name=='acquire_asdc.py'and a.source_cache:continue
 text=(source/name).read_text().replace("pathlib.Path('/workspace/4k29/training/language/conversation-v2')",repr(a.v2_root.resolve()).replace('PosixPath','pathlib.Path'))
 (out/name).write_text(text);subprocess.run([sys.executable,str(out/name)],check=True)
for name in ['DATA.json','INPUT_AUDIT.json','DEV_PROTOCOL.json','SPLIT_AUDIT.json']:
 expected=hashlib.sha256((source/name).read_bytes()).hexdigest();got=hashlib.sha256((out/name).read_bytes()).hexdigest();assert got==expected,(name,expected,got)
print('Exact curated inputs, masks and DEV reproduced; optimizer calls0, model forwards0')
