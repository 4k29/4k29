"""Only own completed character weights; new blocks initially act as identity."""
import hashlib,json,pathlib
import torch
ROOT=pathlib.Path(__file__).resolve().parent;PARENT=ROOT.parent/'round6';VOCAB_PARENT=ROOT.parent/'round5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def initialize(model,tokenizer):
    policy=read(ROOT/'experiment-policy.json')
    for relative,expected in policy['frozenParentFiles'].items():
        if sha(PARENT/relative)!=expected:raise ValueError('Own frozen parent changed: '+relative)
    path=PARENT/'character-continue-10000/checkpoint.pt';result=read(path.parent/'result.json');saved=torch.load(path,map_location='cpu',weights_only=False)
    if not result['completedRun'] or saved['step']!=result['completedSteps'] or saved['step']!=10000:raise ValueError('Completed own parent required')
    if sorted({int(s['step']) for s in saved['optimizer']['state'].values()})!=[10000]:raise ValueError('Real parent optimizer counters differ')
    if saved['beststep']!=result['bestStep'] or not result['ownParentOnly'] or not result['ownRandomInitializedLineage']:raise ValueError('Own selected character lineage required')
    if any(result[k] for k in ['externalWeights','externalTokenizer','externalInferenceAPI']):raise ValueError('Outside weights forbidden')
    config=saved['config'];current=model.config
    if any(current[k]!=v for k,v in config.items() if k not in ['layers','vocabulary']):raise ValueError('Unsupported own architecture change')
    if current['layers']!=8 or config['layers']!=4 or current['vocabulary']<config['vocabulary']:raise ValueError('Expected4-to8 blocks and vocabulary extension')
    previous=read(VOCAB_PARENT/'unicode-bpe-4503/tokenizer.json')
    if tokenizer['bytes'][:len(previous['bytes'])]!=previous['bytes'] or tokenizer['merges'][:len(previous['merges'])]!=previous['merges']:raise ValueError('Parent character IDs/ranks changed')
    state=model.state_dict()
    with torch.no_grad():
        state['token.weight'].zero_();state['token.weight'][:config['vocabulary']].copy_(saved['beststate']['token.weight'])
        for key,value in saved['beststate'].items():
            if key!='token.weight':state[key].copy_(value)
        for block in model.blocks[config['layers']:]:
            block.proj.weight.zero_();block.proj.bias.zero_();block.fc2.weight.zero_();block.fc2.bias.zero_()
    return dict(parentCheckpointSha256=sha(path),parentCompletedSteps=10000,parentSelectedChildSteps=saved['beststep'],parentSelectedWeightLineageUpdates=result['parentSelectedSteps']+saved['beststep'],parentLayers=config['layers'],parentVocabulary=config['vocabulary'],parentTrainerSha256=sha(PARENT/'train.py'),ownParentOnly=True,ownRandomInitializedLineage=True,identityNewResidualBlocks=True,newTokenRowsInitiallyZero=True,parentTokenIdsAndRanksRetained=True,randomInitialization=False,optimizerReset=True,seedReset=True)
