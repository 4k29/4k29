"""Reuse exact old response/multiturn protocols, writing only the new series folder."""
import pathlib,sys,importlib.util
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from next_runtime import *
spec=importlib.util.spec_from_file_location('retained_panels',OLD/'evaluate_panels.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.N=D;module.load=load_study_model
module.model_history=lambda name:read(D/'INITIAL_REFERENCES.json')['sources'][name.split('-')[0]]['base_model_unique_updates']+int(name.split('-')[1])
if __name__=='__main__':module.main()
