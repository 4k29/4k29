"""Run existing repository checks verbatim in scope, without changing published assets."""
import pathlib,subprocess,glob,json,time,argparse
D=pathlib.Path(__file__).resolve().parent;ROOT=D.parents[3]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--remaining-only',action='store_true');args=parser.parse_args()
 commands=[['node','--test',*sorted(glob.glob('tests/*.test.mjs',root_dir=ROOT))],['node','evaluation/evaluate-japanese.mjs']]
 for line in(ROOT/'.github/workflows/check-site.yml').read_text().splitlines():
  line=line.strip()
  if line.startswith('node --check '):commands.append(line.split())
 if args.remaining_only:commands=commands[1:]
 tag='ROOT_REMAINING'if args.remaining_only else'ROOT_CHECKS';records=[]
 with(D/(tag+'.log')).open('w')as f:
  for command in commands:
   t=time.monotonic();r=subprocess.run(command,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT);records.append(dict(command=command,returncode=r.returncode,elapsed_seconds=time.monotonic()-t))
   if r.returncode:break
 result=dict(all_passed=len(records)==len(commands)and all(r['returncode']==0 for r in records),commands=records,optimizer_updates=0,public_assets_modified=False,scope='Remaining independent commands only'if args.remaining_only else'Full existing root checks')
 (D/(tag+'.json')).write_text(json.dumps(result,indent=2)+'\n');print('Existing root checks',result['all_passed'],len(records))
 if not result['all_passed']:raise SystemExit(1)
if __name__=='__main__':main()
