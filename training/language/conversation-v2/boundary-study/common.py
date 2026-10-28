import sys,pathlib,json
N=pathlib.Path(__file__).resolve().parent;V=N.parent;H=V/'foundation-stage';sys.path.insert(0,str(H))
from runtime import torch,initial,snapshot,restore_isolated,sha,save,record,digest,trajectory,causal_ce,clip_grad_accurate
from new_tokenizer import Encoder

def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
