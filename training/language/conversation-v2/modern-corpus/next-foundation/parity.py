"""Unchanged limited raw-FP32 JS probe; not a complete reply equivalence claim."""
import pathlib,sys,importlib.util
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from next_runtime import *
spec=importlib.util.spec_from_file_location('retained_parity',OLD/'parity_terminal.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.N=D

def source_sha(name):
 arm,step=name.split('-');path=RUN/arm/f'checkpoint-{int(step):05d}.pt'
 return sha(path)if path.exists()else read(D/'artifacts'/name/'checkpoint.json')['sha256']
def state(name):
 arm,step=name.split('-');path=RUN/arm/f'checkpoint-{int(step):05d}.pt'
 if path.exists():assert sha(path)==source_sha(name);return torch.load(path,weights_only=False)
 manifest=D/'artifacts'/name/'checkpoint.json';return legacy.loader.load_checkpoint(manifest,read(manifest)['sha256'])
module.load=state;module.source_checkpoint_sha=source_sha
if __name__=='__main__':module.main()
