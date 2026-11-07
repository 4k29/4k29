"""Zero-update comparison of standard FP32 and accurately reduced clipping.

This does not invoke train.run(), select conditions, or relax the frozen
2e-5 norm agreement criterion. Both widths use the identical human TRAIN draw.
"""
import json
import pathlib
import time

import torch

from core import (HERE, REPO, causal_ce, clip_grad_accurate, digest, initialize,
                  next_batch, open_tokens, pack, sha)


def main():
    original_plan = json.loads((HERE/'PREFLIGHT_PLAN.json').read_text())
    data_path = REPO/original_plan['dataPath']
    assert sha(data_path) == original_plan['dataSha256']
    data = json.loads(data_path.read_text());values,windows = open_tokens(data,'train')
    settings=original_plan['training']
    torch.set_num_threads(settings['threads']);torch.use_deterministic_algorithms(True)
    reports=[];started=time.monotonic()
    for name in ['small','medium']:
        model,optimizer,rng=initialize(original_plan['models'][name],settings)
        before=digest(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate()))
        torch_before=torch.get_rng_state().clone()
        private=type(rng)();private.setstate(rng.getstate())
        indices,_,_=next_batch(private,[],0,len(windows),settings['batch'])
        x,y,stats=pack(values,windows,indices,model.config['vocabulary'])
        batches=[]
        for j in range(2):
            optimizer.zero_grad(set_to_none=True)
            loss=causal_ce(model(x),y);loss.backward()
            gradients=[p.grad for p in model.parameters()]
            assert all(g is not None and bool(torch.isfinite(g).all())for g in gradients)
            original=[g.detach().clone()for g in gradients]
            flat=torch.cat([g.reshape(-1)for g in original])
            flat32=float(torch.linalg.vector_norm(flat))
            flat64=float(torch.linalg.vector_norm(flat.double()))
            tensor64=sum(float(g.double().square().sum())for g in original)**.5
            tensor32=float(torch.linalg.vector_norm(torch.stack([torch.linalg.vector_norm(g)for g in original])))
            clip32=float(torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True))
            standard_after=sum(float(g.double().square().sum())for g in gradients)**.5
            for p,g in zip(model.parameters(),original):p.grad.copy_(g)
            accurate=float(clip_grad_accurate(model.parameters(),1.))
            accurate_after=sum(float(g.double().square().sum())for g in gradients)**.5
            expected_coefficient=torch.tensor(min(1.,1./(flat64+1e-6)),dtype=torch.float32)
            maximum_scaling_error=max(float((g-reference*expected_coefficient).abs().max())for g,reference in zip(gradients,original))
            standard_matches=abs(clip32-flat64)<=2e-5+2e-5*abs(flat64)
            accurate_matches=abs(accurate-flat64)<=2e-5+2e-5*abs(flat64)
            assert accurate_matches and accurate_after<=1.+2e-5 and maximum_scaling_error<=2e-7
            batches.append(dict(batch=j,loss=float(loss.detach()),allGradientsFinite=True,
                flatFp32Norm=flat32,flatFp64Norm=flat64,perTensorFp32Norm=tensor32,perTensorFp64Norm=tensor64,
                standardClipReturnedNorm=clip32,standardClipRelativeError=abs(clip32-flat64)/flat64,
                standardPassesOriginalTolerance=standard_matches,standardClippedActualNormFp64=standard_after,
                accurateClipReturnedNorm=accurate,accurateClipRelativeError=abs(accurate-flat64)/flat64,
                accuratePassesOriginalTolerance=accurate_matches,accurateClippedActualNormFp64=accurate_after,
                maximumActualGradientScalingError=maximum_scaling_error))
        optimizer.zero_grad(set_to_none=True);torch.set_rng_state(torch_before)
        after=digest(dict(model=model.state_dict(),optimizer=optimizer.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate()))
        assert before==after
        reports.append(dict(model=name,parameters=sum(p.numel()for p in model.parameters()),indices=indices,
            batches=batches,modelOptimizerRngUnchanged=True,actualOptimizerUpdates=0,**stats))
        del model,optimizer,rng,original,gradients,flat
    output=dict(schemaVersion=1,scope='Independent zero-update norm audit before any new-series training',
        oldSourceHashes=original_plan['codeReceipts'],oldPreflightPlanSha256=sha(HERE/'PREFLIGHT_PLAN.json'),
        correctedSourceHashes={str(p.relative_to(REPO)):sha(p)for p in [HERE/'core.py',HERE/'train.py',pathlib.Path(__file__)]},
        dataSha256=sha(data_path),frozenAbsoluteTolerance=2e-5,frozenRelativeTolerance=2e-5,
        maxNormUnchanged=1.,clippingEpsilonUnchanged=1e-6,gradientDtypeUnchanged='float32',
        optimizerUpdates=0,reports=reports,elapsedSeconds=time.monotonic()-started,
        decision='Use FP64 global-L2 norm reduction and one common FP32 scaling coefficient in BOTH new-series widths; no legacy model/code modification')
    path=HERE/'independent-norm-audit.json'
    if path.exists():raise ValueError('Refuse audit receipt overwrite')
    path.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps(output,indent=2,allow_nan=False))


if __name__=='__main__':main()
