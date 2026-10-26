"""Independent, zero-update first-epoch endpoint and exposure audit."""
import hashlib,json,pathlib,sys
import torch
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent))
from eval_chunk_loader import load_chunks
from core import exact,digest,sha

def audit(name):
    receipt=json.loads((HERE/name/'receipt.json').read_text())
    source=load_chunks(HERE.parent/'pilot'/name/'checkpoint.pt.chunks.json')['trajectory']
    saved=load_chunks(pathlib.Path(receipt['checkpointManifest']));state=saved['trajectory']
    history=state['history'];order=state['order'];used=[i for row in history for i in row['windowIndices']]
    assert receipt['status']=='completed-first-train-epoch'
    assert state['cursor']==len(order)==len(used)==len(set(used))==13878
    assert used==order and sorted(used)==list(range(13878))
    assert state['uniqueUpdates']==len(history)==3470
    assert exact(history[:512],source['history']) and exact(order,source['order'])
    assert exact(state['pythonRng'],source['pythonRng'])
    assert len(history[-1]['windowIndices'])==2
    assert all(len(x['windowIndices'])==4 for x in history[:-1])
    assert all(x['learningRate']==3e-5 for x in history[512:])
    assert sum(x['targetTokens']for x in history)==2816905
    assert sum(x['targetTokens']for x in history[512:])==2401584
    expected_actual=3052 if name=='medium' else 2960
    assert receipt['actualContinuationUpdates']==expected_actual
    assert receipt['retainedContinuationUpdates']==2958
    assert receipt['cumulativeActualOptimizerUpdates']==514+expected_actual
    assert receipt['resumeAudit']['allModelAdamRngSamplerHistoryBitwiseEqual']
    events=[json.loads(x)for x in (HERE/name/'optimizer-ledger.jsonl').read_text().splitlines()]
    assert len(events)==2*expected_actual
    for i in range(expected_actual):
        before,after=events[2*i:2*i+2]
        assert before['event']=='before-step' and after['event']=='after-step'
        assert before['actualUpdate']==after['actualUpdate']==i+1
        assert before['uniqueUpdate']==after['uniqueUpdate']
    expected_replay=94 if name=='medium' else 2
    assert sum(x['event']=='after-step'and x['replay'] for x in events)==expected_replay
    assert all(bool(torch.isfinite(x).all()) for x in state['model'].values())
    states=state['optimizer']['state']
    assert len(states)==len(state['model'])
    assert all(float(s['step'])==3470 for s in states.values())
    assert all(bool(torch.isfinite(s[k]).all()) for s in states.values()for k in ['exp_avg','exp_avg_sq'])
    assert all(bool((s['exp_avg_sq']>=0).all())for s in states.values())
    assert all(g['lr']==3e-5 for g in state['optimizer']['param_groups'])
    lost=history[2560:2652] if name=='medium' else []
    lost_targets=sum(x['targetTokens']for x in lost)
    pilot_replay=sum(x['targetTokens']for x in history[2:4])
    continuation_replay=sum(x['targetTokens']for x in history[514:516])
    return dict(model=name,passed=True,allRetainedWindowsExactlyOnce=True,original512HistoryUnchanged=True,
        samplerOrderAndRngInherited=True,terminalRetainedUpdates=3470,actualContinuationUpdates=expected_actual,
        cumulativeActualUpdates=514+expected_actual,targetTokens=2816905,newTargetTokens=2401584,
        lostCompletedUpdates=92 if name=='medium' else 0,lostCompletedTargetTokens=lost_targets,
        originalPilotReplayTargetTokens=pilot_replay,continuationAuditReplayTargetTokens=continuation_replay,
        actualNewProcessedTargets=2401584+continuation_replay+lost_targets,
        actualCumulativeProcessedTargets=2816905+pilot_replay+continuation_replay+lost_targets,
        lostStateBitwiseComparisonAvailable=False if name=='medium' else None,
        finalBatch=2,adamFiniteAndSecondMomentsNonnegative=True,actualLedgerConsistent=True,
        checkpointSha256=receipt['checkpointSha256'],terminalTrajectoryDigest=digest(state),
        auditOptimizerUpdates=0)

if __name__=='__main__':
    result=[audit(name)for name in sys.argv[1:]]
    out=HERE/'training-audit.json'
    if out.exists():raise ValueError('Refuse audit overwrite')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
