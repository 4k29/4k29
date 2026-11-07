"""Read own archived or active states; never update parameters."""
from study_runtime import *
def state(name):
 if name=='base-0':return source()
 arm,n=name.split('-');n=int(n);manifest=P/'artifacts'/name/'checkpoint.json'
 if manifest.exists():return legacy.loader.load_checkpoint(manifest,read(manifest)['sha256'])
 path=P/'private/run'/arm/'checkpoint.pt';obj=torch.load(path,map_location='cpu',weights_only=False);assert obj['active_cursor']==n and integrity(obj)==obj['state_integrity_sha256'];return obj

def load(name):
 obj=state(name);return restore_isolated(obj['trajectory'])[0],0 if name=='base-0'else obj['active_cursor']
