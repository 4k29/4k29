"""Unchanged limited raw-FP32 Python/JS probe on this study's fixed checkpoints."""
import importlib.util
from study_runtime import *
from load_model import state
spec=importlib.util.spec_from_file_location('paragraph_raw_parity',P.parent/'diverse-foundation/parity_terminal.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.N=P;module.load=state

def checkpoint_sha(name):
 if name=='base-0':return read(P/'PLAN.json')['initial_checkpoint_sha256']
 path=P/'artifacts'/name/'checkpoint.json'
 return read(path)['sha256']if path.exists()else sha(P/'private/run'/name.split('-')[0]/'checkpoint.pt')
module.source_checkpoint_sha=checkpoint_sha
if __name__=='__main__':module.main()
