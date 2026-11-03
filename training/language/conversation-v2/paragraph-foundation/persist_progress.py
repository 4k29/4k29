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
 d=json.loads((P/'RESUME_STATUS.json').read_text());d.update(updated_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),draft_pr=106,acquisition_status=json.loads((P/'ACQUISITION_STATUS.json').read_text()),validation_optimizer_calls=6,comparative_learning_updates=0,persistence=dict(root=str(DEST),new_mirrored_files=count,bytes=total,raw_acquisition_included=True,scratch_weights_excluded=True))
 (P/'RESUME_STATUS.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');shutil.copy2(P/'RESUME_STATUS.json',DEST/'RESUME_STATUS.json');print(json.dumps(d['persistence']))
if __name__=='__main__':main()
