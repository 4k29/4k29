"""Push and prove this candidate generation before releasing its disposable local copy."""
import pathlib,sys,subprocess,io,hashlib
C=pathlib.Path(__file__).resolve().parent;P=C.parent;sys.path.insert(0,str(P))
from study_runtime import *
from archive_state import archive
DEST=pathlib.Path('/workspace/4k29')/P.relative_to(ROOT)/'private/capacity-hybrid'

def main():
 arm=sys.argv[1];step=int(sys.argv[2]);assert arm in ['11M','27M']and step in [0,2,4];raw=DEST/arm/'checkpoint.pt';obj=torch.load(raw,map_location='cpu',weights_only=False);assert obj['active_cursor']==step and obj['arm']==arm;folder=C/'artifacts'/(arm+'-'+str(step));m=archive(raw,folder)
 if(DEST/arm/'actual-updates.jsonl').exists():shutil.copy2(DEST/arm/'actual-updates.jsonl',C/('ACTUAL_UPDATES_'+arm+'.jsonl'))
 subprocess.run(['git','add','--sparse',str(C.relative_to(ROOT))],cwd=ROOT,check=True);subprocess.run(['git','commit','-m',f'Archive isolated fresh{arm} resource feasibility state{step}'],cwd=ROOT,check=True);subprocess.run(['git','push'],cwd=ROOT,check=True);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip();assert subprocess.check_output(['git','ls-remote','origin','refs/heads/research/paragraph-foundation'],cwd=ROOT,text=True).split()[0]==head
 whole=hashlib.sha256();buf=io.BytesIO()
 for c in m['chunks']:
  data=subprocess.check_output(['git','show','HEAD:'+str((folder/c['path']).relative_to(ROOT))],cwd=ROOT);assert len(data)==c['bytes']and hashlib.sha256(data).hexdigest()==c['sha256'];whole.update(data);buf.write(data)
 assert whole.hexdigest()==m['sha256'];buf.seek(0);check=torch.load(buf,map_location='cpu',weights_only=False);assert digest(check)==m['full_state_digest'];buf.close();del check
 for c in m['chunks']:
  f=folder/c['path'];subprocess.run(['git','update-index','--skip-worktree',str(f.relative_to(ROOT))],cwd=ROOT,check=True);f.unlink()
 assert sha(raw)==m['sha256'];raw.unlink();(C/'receipts').mkdir(exist_ok=True);write(C/'receipts'/(arm+'-'+str(step)+'-ARCHIVE.json'),dict(full_state_digest=m['full_state_digest'],checkpoint_sha256=m['sha256'],pushed_commit=head,Git_only_full_state_restore_exact=True,working_copies_released_only_after_proof=True,optimizer_updates=0));print(arm,step,'archived and restored from Git',flush=True)
if __name__=='__main__':main()
