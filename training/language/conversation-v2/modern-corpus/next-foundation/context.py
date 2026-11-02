"""Unchanged nine-family teacher-history ablation on new own-model checkpoints."""
import pathlib,sys,importlib.util
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from next_runtime import *
spec=importlib.util.spec_from_file_location('retained_context',OLD/'context.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.D=D;module.load=load_study_model
if __name__=='__main__':module.main()
