"""Exact prior content24/provided23/grounded36/context/self-history protocols."""
import importlib.util,pathlib,sys
from study_runtime import *
from load_model import load
OLD=P.parent/'diverse-foundation'
spec=importlib.util.spec_from_file_location('paragraph_retained_panels',OLD/'evaluate_panels.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.N=P;module.load=load;module.model_history=lambda name:read(P/'STATE_PREFLIGHT.json')['source_model_unique_updates']+(0 if name=='base-0'else int(name.split('-')[1]))
if __name__=='__main__':module.main()
