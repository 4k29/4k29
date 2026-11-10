"""Reuse prior exact-FP32 three-prefix/four-position engineering probe, no production edits."""
from mix_runtime import *
sys.path.insert(0,str(V/'diverse-foundation'))
import parity_terminal as mod
mod.N=P
mod.load=lambda name:torch.load(SCRATCH/'LR3-401.pt',map_location='cpu',weights_only=False)
mod.source_checkpoint_sha=lambda name:sha(SCRATCH/'LR3-401.pt')
if __name__=='__main__':mod.main()
