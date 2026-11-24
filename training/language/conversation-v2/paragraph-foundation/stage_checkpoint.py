"""Archive/push/prove before releasing only this study's disposable working mirrors."""
import argparse,subprocess,io,hashlib
from study_runtime import *
from archive_state import archive

def main():
 ap=argparse.ArgumentParser();ap.add_argument('name');ap.add_argument('--restore',action='store_true');args=ap.parse_args();arm,n=args.name.split('-');n=int(n);assert arm in ['A','B'];folder=P/'artifacts'/args.name
 if args.restore:
  obj=legacy.loader.load_checkpoint(folder/'checkpoint.json',read(folder/'checkpoint.json')['sha256']);assert obj['active_cursor']==n and integrity(obj)==obj['state_integrity_sha256'];mirror(arm,obj);print('Restored durable study mirror',args.name);return
 raw=P/'private/run'/arm/'checkpoint.pt';obj=torch.load(raw,map_location='cpu',weights_only=False);assert obj['active_cursor']==n and integrity(obj)==obj['state_integrity_sha256'];m=archive(raw,folder)
 receipts=P/'receipts';receipts.mkdir(exist_ok=True);write(receipts/(args.name+'.json'),read(raw.parent/f'receipt-{n:05d}.json'))
 log=DURABLE/arm/'actual-updates.jsonl';shutil.copy2(log,P/('ACTUAL_UPDATES_'+arm+'.jsonl'))
 subprocess.run(['git','add','--sparse',str(P.relative_to(ROOT))],cwd=ROOT,check=True);subprocess.run(['git','commit','-m','Archive full isolated paragraph-study state '+args.name],cwd=ROOT,check=True);subprocess.run(['git','push'],cwd=ROOT,check=True)
 head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/research/paragraph-foundation'],cwd=ROOT,text=True).split()[0];assert head==remote
 whole=hashlib.sha256();buf=io.BytesIO()
 for c in m['chunks']:
  path=folder/c['path'];rel=str(path.relative_to(ROOT));data=subprocess.check_output(['git','show','HEAD:'+rel],cwd=ROOT);assert hashlib.sha256(data).hexdigest()==c['sha256']and len(data)==c['bytes'];whole.update(data);buf.write(data)
 assert whole.hexdigest()==m['sha256'];buf.seek(0);check=torch.load(buf,map_location='cpu',weights_only=False);assert digest(check)==m['full_state_digest'];buf.close();del check
 # These newly created derived files have a verified remote commit and full Git-only restore.
 for c in m['chunks']:
  path=folder/c['path'];subprocess.run(['git','update-index','--skip-worktree',str(path.relative_to(ROOT))],cwd=ROOT,check=True);path.unlink()
 mirror_path=DURABLE/arm/'checkpoint.pt';before=shutil.disk_usage(DURABLE).free
 if mirror_path.exists():
  assert digest(torch.load(mirror_path,map_location='cpu',weights_only=False))==m['full_state_digest'];mirror_path.unlink();mirror_path.with_name('checkpoint-receipt.json').unlink()
 write(receipts/(args.name+'-GIT_RESTORE_PROOF.json'),dict(checkpoint_sha256=m['sha256'],full_state_digest=m['full_state_digest'],git_commit_pushed_and_confirmed=head,git_only_chunk_and_full_state_restore_exact=True,working_chunk_copies_removed_after_proof=True,new_disposable_durable_mirror_removed_after_proof=True,persistent_bytes_reclaimed=shutil.disk_usage(DURABLE).free-before,original_formal_checkpoints_touched=False,optimizer_updates=0))
 print('Pushed and full-state Git restore verified',args.name,m['sha256'],flush=True)
if __name__=='__main__':main()
