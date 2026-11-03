"""Independent alternative storage preflight; never lowers the256MiB reserve.
Previous generations must be pushed and Git-only restored before local removal.
"""
import pathlib,sys,json,hashlib,shutil,os,subprocess
C=pathlib.Path(__file__).resolve().parent;P=C.parent;sys.path.insert(0,str(P))
from study_runtime import read,write,sha
RESERVE=256*1024**2;PAYLOAD=27397632*12+2*1024**2
DEST=pathlib.Path('/workspace/4k29')/P.relative_to(P.parents[3])/'private/capacity-hybrid'

def main():
 assert(P/'FINITE_COMPARISON_COMPLETE.json').exists(),'Do not compete for disk with running main comparison'
 assert read(P/'FINITE_COMPARISON_COMPLETE.json')['complete'];DEST.mkdir(exist_ok=True,parents=True);free=shutil.disk_usage(DEST).free
 protocol=read(C/'HYBRID_FEASIBILITY_PROTOCOL.json');result=dict(topology='Verified remote/local-Git previous generation plus one atomically written workspace generation; no two local dense generations',old_two_local_topology_remains_NoGo=True,reserve_bytes=RESERVE,probe_payload_bytes=PAYLOAD,free_before=free,optimizer_updates=0,payload_is_not_a_model_or_training_benchmark=True,protocol_sha256=sha(C/'HYBRID_FEASIBILITY_PROTOCOL.json'))
 if free<PAYLOAD+RESERVE:result.update(pass_all=False,reason='Insufficient space even for hybrid single-dense-payload peak');write(C/'HYBRID_STORAGE_PREFLIGHT.json',result);print(json.dumps(result));return
 source=P/'private/source-B-6361.pt';assert sha(source)==read(P/'PLAN.json')['initial_checkpoint_sha256'];pending=DEST/'payload.pending';target=DEST/'payload.storage-probe';assert not pending.exists()and not target.exists();expected=hashlib.sha256();left=PAYLOAD
 with pending.open('wb')as out:
  while left:
   with source.open('rb')as inp:
    while left:
     b=inp.read(min(1048576,left))
     if not b:break
     out.write(b);expected.update(b);left-=len(b)
  out.flush();os.fsync(out.fileno())
 minimum=shutil.disk_usage(DEST).free;assert minimum>=RESERVE and pending.stat().st_size==PAYLOAD and sha(pending)==expected.hexdigest();os.replace(pending,target);fd=os.open(DEST,os.O_RDONLY);os.fsync(fd);os.close(fd);assert sha(target)==expected.hexdigest();target.unlink()
 # Actual initialized candidate0 archive/proof is mandatory before its first update.
 result.update(pass_all=True,minimum_observed_free=minimum,payload_sha256=expected.hexdigest(),atomic_new_generation_written_and_reread=True,probe_removed=True,mandatory_before_updates='Archive exact candidate0 all-state; push, confirm remote commit, Git-only full-state reload, then release only its working mirror. Repeat at2 and4.',whole_environment_loss='Only remote verified generations are claimed durable outside the workspace; per-call workspace ledgers enable exact replay when retained.')
 write(C/'HYBRID_STORAGE_PREFLIGHT.json',result);print(json.dumps(result))
if __name__=='__main__':main()
