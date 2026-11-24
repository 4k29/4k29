"""Independent remote-only repository restoration, full-state validation; zero updates."""
from mix_runtime import *
import argparse,subprocess
ap=argparse.ArgumentParser();ap.add_argument('--repository',required=True);ap.add_argument('--cursors',nargs='+',type=int,required=True);args=ap.parse_args();repo=pathlib.Path(args.repository);commit=subprocess.check_output(['git','rev-parse','FETCH_HEAD'],cwd=repo,text=True).strip()
for n in args.cursors:
 rel=str(P.relative_to(ROOT)/f'artifacts/VOLUME-{n}');blob=lambda s:subprocess.check_output(['git','show',commit+':'+s],cwd=repo);meta=json.loads(blob(rel+'/checkpoint.json'));dest=repo/f'verified-{n}.pt';assert not dest.exists();h=hashlib.sha256()
 with dest.open('wb') as f:
  for chunk in meta['chunks']:
   b=blob(rel+'/'+chunk['path']);assert hashlib.sha256(b).hexdigest()==chunk['sha256'];f.write(b);h.update(b)
  f.flush();os.fsync(f.fileno())
 assert h.hexdigest()==meta['sha256']==sha(dest);o=torch.load(dest,map_location='cpu',weights_only=False);assert integrity(o)==o['integrity']==meta['integrity'];assert o['sampler']['cursor']==o['active_cursor']==n;assert o['sampler']['schedule_sha256']==sha(P/'schedule.json.gz');assert o['plan_sha256']==sha(P/'PLAN.json');assert {int(v['step']) for v in o['trajectory']['optimizer']['state'].values()}=={6940+n}
 ret=[json.loads(l)['trace'] for l in (P/'UPDATES.jsonl').read_text().splitlines() if json.loads(l)['event']=='completed' and json.loads(l)['phase']=='retained'];assert ret[:n]==o['trace'];write(P/f'GIT_RESTORE-{n}.json',dict(passed=True,source_commit=commit,source='Fresh remote-only Git objects, no alternates or local checkpoint reads',sha256=h.hexdigest(),file_materialized_and_deserialized=True,full_model_Adam_RNG_sampler_cursor_trace_integrity=True,optimizer_calls=0,model_forwards=0));print('Git-only full state',n,'PASS',flush=True);del o
