"""Materialize and deserialize all three remote-only Git states, zero model/optimizer calls."""
from lf_runtime import *
import argparse,subprocess
ap=argparse.ArgumentParser();ap.add_argument('--repository',required=True);ap.add_argument('--commit',default='FETCH_HEAD');args=ap.parse_args();repo=pathlib.Path(args.repository);results=[]
def blob(rel):return subprocess.check_output(['git','show',args.commit+':'+rel],cwd=repo)
commit=subprocess.check_output(['git','rev-parse',args.commit],cwd=repo,text=True).strip()
for n in [4,289,579]:
 rel=str(P.relative_to(ROOT)/f'artifacts/LF1-{n}');meta=json.loads(blob(rel+'/checkpoint.json'));dest=repo/f'git-restored-LF1-{n}.pt';assert not dest.exists();h=hashlib.sha256()
 with dest.open('wb') as f:
  for c in meta['chunks']:
   b=blob(rel+'/'+c['path']);assert hashlib.sha256(b).hexdigest()==c['sha256'];f.write(b);h.update(b)
  f.flush();os.fsync(f.fileno())
 assert h.hexdigest()==meta['sha256']==sha(dest);o=torch.load(dest,map_location='cpu',weights_only=False)
 assert integrity(o)==o['integrity']==meta['integrity'];assert o['active_cursor']==o['sampler']['cursor']==n;assert len(o['trace'])==n;assert {int(v['step']) for v in o['trajectory']['optimizer']['state'].values()}=={6361+n};assert o['plan_sha256']==sha(P/'PLAN.json') and o['sampler']['schedule_sha256']==sha(P/'schedule-LF1.json.gz')
 results.append(dict(cursor=n,checkpoint_sha256=h.hexdigest(),written_and_deserialized=True,full_state_integrity_match=True,model_Adam_all_RNG_sampler_trace_present=True));del o
write(P/'GIT_FULL_STATE_RESTORE_AUDIT.json',dict(passed=True,source_repository='Fresh remote-only filtered Git repository, no alternates',source_commit=commit,cases=results,optimizer_calls=0,model_forwards=0));print('Three Git-only files written, SHA checked and full states deserialized: PASS')
