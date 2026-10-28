from common import *
from runtime import pack
from runtime import snapshot as historical_snapshot

def snapshot(name):
 path=N/'run'/name/'checkpoint.pt'
 if path.exists():return torch.load(path,map_location='cpu',weights_only=False)
 from runtime import loader
 p=N/'run'/name/'archive/checkpoint.json';return loader.load_checkpoint(p,json.loads(p.read_text())['sha256'])
