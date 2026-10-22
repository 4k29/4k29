"""Post-launch read-only environment record; no access to live training tensors."""
import pathlib,json,hashlib,datetime,os,platform,sys,torch,numpy
E=pathlib.Path(__file__).resolve().parent;R=E.parent
torch.set_num_threads(1)
cpu={}
for line in pathlib.Path('/proc/cpuinfo').read_text().splitlines():
 if ':'in line:
  k,v=map(str.strip,line.split(':',1))
  if k in ['vendor_id','model name','flags']and k not in cpu:cpu[k]=v
last=json.loads((E/'continuous-checkpoint-audits.jsonl').read_text().splitlines()[-1]);launch=json.loads((E/'launch.json').read_text());quota=pathlib.Path('/sys/fs/cgroup/cpu.max')
out=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),observation='Separate post-launch read-only process, not a preflight or live trainer introspection',lastAuditedActualUpdates=last['retainedActualUpdates'],python=sys.version,torch=torch.__version__,numpy=numpy.__version__,platform=platform.platform(),machine=platform.machine(),cpu=cpu,cgroupCpuMax=quota.read_text().strip()if quota.exists()else None,probeAffinity=sorted(os.sched_getaffinity(0)),torchBuildConfiguration=torch.__config__.show(),probeFloat32MatmulPrecision=torch.get_float32_matmul_precision(),probeTorchThreads=1,trainerConfiguredThreads=2,trainerPrecision='float32; autocast disabled by frozen CLI',cudaAvailable=torch.cuda.is_available(),explicitEnvironment={k:os.environ.get(k)for k in ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','CUBLAS_WORKSPACE_CONFIG']},sourceManifestSha256=hashlib.sha256((R/'source-manifest.json').read_bytes()).hexdigest(),codeSha256=hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),additionalOptimizerUpdates=0,liveTrainerNotModified=True,bitwiseReproductionOnDifferentHardwareNotGuaranteed=True)
(E/'post-launch-numeric-environment.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k]for k in ['lastAuditedActualUpdates','torch','numpy','cgroupCpuMax','additionalOptimizerUpdates','liveTrainerNotModified']}))
