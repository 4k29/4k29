"""Reuse prior exact-FP32 three-prefix/four-position engineering probe, no production edits."""
from lf_runtime import *
sys.path.insert(0,str(V/'diverse-foundation'))
import parity_terminal as mod
mod.N=P
mod.load=lambda name:torch.load(SCRATCH/'LF1-579.pt',map_location='cpu',weights_only=False)
mod.source_checkpoint_sha=lambda name:sha(SCRATCH/'LF1-579.pt')
if __name__=='__main__':mod.main()
