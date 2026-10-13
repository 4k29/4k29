"""Continue only the manifest-bound own checkpoint, with a fresh optimizer."""
import hashlib,json,pathlib,torch
ROOT=pathlib.Path(__file__).resolve().parent
PARENT=ROOT.parent/'round10'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def initialize(model,tokenizer,ancestor=None):
    policy=json.loads((ROOT/'policy.json').read_text())
    manifest=PARENT/'reproducibility-manifest.json'
    assert sha(manifest)==policy['parentManifestSha256']
    for row in json.loads(manifest.read_text())['files']:
        assert sha(PARENT/row['path'])==row['sha256'],row['path']
    cp=PARENT/'word-512-continue-10000/checkpoint.pt'
    assert sha(cp)==policy['parentCheckpointSha256']
    saved=torch.load(cp,map_location='cpu',weights_only=False)
    assert saved['step']==10000 and saved['beststep']==10000
    assert saved['config']==model.config
    assert sha(PARENT/'word-bpe-512/tokenizer.json')==policy['sourceHashes']['word-bpe-512/tokenizer.json']
    model.load_state_dict(saved['beststate'],strict=True)
    assert all(torch.isfinite(p).all() for p in model.parameters())
    return dict(parentCheckpointSha256=sha(cp),parentSelectedLineageUpdates=39000,initialization='Our round10 best weights, unchanged vocabulary and architecture; fresh AdamW',externalWeights=False)
