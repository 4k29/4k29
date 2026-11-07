"""Restore our own latest optimizer-aligned Round11 weights; no foreign models."""
import hashlib,json,pathlib,torch
from capacity import expand_ffn_weights
ROOT=pathlib.Path(__file__).resolve().parent
PARENT=ROOT.parent/'round11'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def initialize(model,tokenizer,ancestor=None):
    policy=json.loads((ROOT/'policy.json').read_text())
    manifest=PARENT/'execution/artifact-manifest.json'
    assert sha(manifest)==policy['parentManifestSha256']
    for row in json.loads(manifest.read_text())['files']:
        assert sha(PARENT/row['path'])==row['sha256'],row['path']
    cp=PARENT/'continue-10000/checkpoint.pt'
    assert sha(cp)==policy['parentCheckpointSha256']
    saved=torch.load(cp,map_location='cpu',weights_only=False)
    assert saved['step']==10000 and saved['config']['hidden']==768 and model.config['hidden']==1536
    assert {k:v for k,v in saved['config'].items() if k!='hidden'}=={k:v for k,v in model.config.items() if k!='hidden'}
    assert sorted(set(int(s['step']) for s in saved['optimizer']['state'].values()))==[10000]
    assert sha(PARENT/'multiview/tokenizer.json')==policy['sourceHashes']['word-bpe-512/tokenizer.json']
    expand_ffn_weights(model,saved)
    fingerprint=hashlib.sha256()
    for name,tensor in model.state_dict().items():fingerprint.update(name.encode()+b'\0');fingerprint.update(tensor.numpy().tobytes())
    assert fingerprint.hexdigest()==policy['capacity']['initialRawStateSha256']
    assert all(torch.isfinite(p).all() for p in model.parameters())
    return dict(parentCheckpointSha256=sha(cp),parentSelectedLineageUpdates=49000,newCoordinatesInitialLineageUpdates=0,newCoordinatesAdamWTensorCounter=10000,capacityChange='Only FFN hidden768→1536; old coordinate weights/moments retained; new incoming own random features and zero outgoing/moments',parentWeightSelection='Latest optimizer-aligned state, not beststate',parentOptimizerUpdates=10000,parentSeenTargetTokens=saved['seen_tokens'],parentSeenTargetUtf8Bytes=saved['seen_bytes'],initialization='Our Round11 latest model + AdamW moments + Torch/Python RNG; hold terminal learning rate',externalWeights=False)
