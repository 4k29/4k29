"""Mirror small study artifacts and private acquisition receipts to persistent workspace.
Never copies large artifact chunks or scratch weights, changes Git history, or deletes originals.
"""
import pathlib,shutil,json,datetime,hashlib
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3];DEST=pathlib.Path('/workspace/4k29')/P.relative_to(ROOT)
def main():
 DEST.mkdir(parents=True,exist_ok=True);count=0;total=0
 for f in list(P.iterdir())+list((P/'private/discovery').iterdir()):
  if not f.is_file():continue
  if f.stat().st_size>8*1024**2:continue
  rel=f.relative_to(P);target=DEST/rel
  if target.exists()and target.stat().st_size==f.stat().st_size and target.stat().st_mtime_ns>=f.stat().st_mtime_ns:continue
  assert shutil.disk_usage(DEST).free>300*1024**2,'Progress mirror reserve'
  target.parent.mkdir(exist_ok=True,parents=True);pending=target.with_suffix(target.suffix+'.pending');shutil.copy2(f,pending);pending.replace(target);count+=1;total+=f.stat().st_size
 arms={}
 for arm in ['A','B']:
  ledger=DEST/'private/durable'/arm/'actual-updates.jsonl';events=[json.loads(l)for l in ledger.read_text().splitlines()]if ledger.exists()else[];done=[e for e in events if e['event']=='completed'];retained=max((e['step']for e in done if e['phase']in ['retained','recovery-replay']),default=0);saved=DEST/'private/durable'/arm/'checkpoint-receipt.json';archive_steps=[int(f.name.split('-')[1].split('.')[0])for f in(P/'receipts').glob(arm+'-*.json')if f.name.split('-')[1].split('.')[0].isdigit()and 'GIT_RESTORE'not in f.name]if(P/'receipts').exists()else[]
  arms[arm]=dict(actual_completed_optimizer_calls=len(done),retained_trajectory_updates=retained,persisted_checkpoint_updates=max([json.loads(saved.read_text())['cursor']if saved.exists()else 0]+archive_steps),resume_validation_calls=sum(e['phase']=='resume-validation'for e in done),recovery_replay_calls=sum(e['phase']=='recovery-replay'for e in done),unmatched_intents=sum(e['event']=='intent'for e in events)-len(done))
 d=json.loads((P/'RESUME_STATUS.json').read_text());d.update(updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),draft_pr=106,acquisition_status=json.loads((P/'ACQUISITION_STATUS.json').read_text()),validation_optimizer_calls=6,comparative_learning_updates=0,persistence=dict(root=str(DEST),new_mirrored_files=count,bytes=total,raw_acquisition_included=True,scratch_weights_excluded=True))
 d.update(arms=arms,optimizer_updates=6+sum(a['actual_completed_optimizer_calls']for a in arms.values()),total_actual_optimizer_calls=6+sum(a['actual_completed_optimizer_calls']for a in arms.values()),comparative_learning_updates=sum(a['retained_trajectory_updates']for a in arms.values()),retained_comparative_updates=sum(a['retained_trajectory_updates']for a in arms.values()),training_started=any(a['actual_completed_optimizer_calls']for a in arms.values()))
 if(P/'DRIVER_STATUS.json').exists():d['current_driver']=json.loads((P/'DRIVER_STATUS.json').read_text());d['stage']=d['current_driver']['stage']+' ('+d['current_driver']['status']+')'
 (P/'RESUME_STATUS.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');shutil.copy2(P/'RESUME_STATUS.json',DEST/'RESUME_STATUS.json');print(json.dumps(d['persistence']))
if __name__=='__main__':main()
