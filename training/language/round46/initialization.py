"""Restore our own latest optimizer-aligned Round28 weights; no foreign models."""
import hashlib,json,pathlib,torch
ROOT=pathlib.Path(__file__).resolve().parent
PARENT=ROOT.parent/'round28'
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
    assert saved['step']==10000 and saved['config']==model.config
    assert sorted(set(int(s['step']) for s in saved['optimizer']['state'].values()))==[20000]
    assert sha(PARENT/'multiview/tokenizer.json')==policy['sourceHashes']['word-bpe-512/tokenizer.json']
    model.load_state_dict(saved['model'],strict=True)
    assert all(torch.isfinite(p).all() for p in model.parameters())
    return dict(parentCheckpointSha256=sha(cp),parentSelectedLineageUpdates=59000,parentWeightSelection='Latest optimizer-aligned state, not beststate',parentOptimizerUpdates=20000,parentSeenTargetTokens=saved['seen_tokens'],parentSeenTargetUtf8Bytes=saved['seen_bytes'],initialization='Our Round28 latest model + AdamW moments + Torch/Python RNG; hold terminal learning rate',externalWeights=False)
