import importlib.util,json,pathlib,sys,torch,random,hashlib
root=pathlib.Path('/workspace/4k29/training/language/diagnostics/learnability-20261026')
spec=importlib.util.spec_from_file_location('assay_runtime',root/'assay_runtime.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
p=json.loads((root/'candidate-panel.json').read_text())
rows=[dict(r,prefixTokens=r['conditions']['correct']['prefixTokens'],wrongPrefixTokens=r['conditions']['mismatched']['prefixTokens'],targetTokens=r['goldTokens']) for r in p['cases'] if r['group']=='fit']
model,opt,rng=m.load_initial();before=m.digest(dict(model=model.state_dict(),optimizer=opt.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate()))
private=random.Random();private.setstate(rng.getstate());order=list(range(64));private.shuffle(order)
loss,rec=m.response_ce(model,[rows[i] for i in order[:8]],'A');loss.backward();gs=[p.grad for p in model.parameters()];flat=torch.cat([g.detach().reshape(-1) for g in gs])
f32=torch.linalg.vector_norm(flat);f64=torch.linalg.vector_norm(flat.double());per32=torch.linalg.vector_norm(torch.stack([torch.linalg.vector_norm(g.detach()) for g in gs]));per64=torch.linalg.vector_norm(torch.stack([torch.linalg.vector_norm(g.detach().double()) for g in gs]));clip=torch.nn.utils.clip_grad_norm_(model.parameters(),1.,error_if_nonfinite=True)
res=dict(loss=float(loss),finite=bool(torch.isfinite(flat).all()),elements=flat.numel(),catFloat32=float(f32),catFloat64=float(f64),perTensorFloat32=float(per32),perTensorFloat64=float(per64),actualClipReturned=float(clip),originalAssertionPassed=bool(torch.allclose(f32,clip,atol=2e-5,rtol=2e-5)),clipVsFloat64RelativeError=float((clip.double()-f64).abs()/f64),catFloat32VsFloat64RelativeError=float((f32.double()-f64).abs()/f64),optimizerUpdates=0)
opt.zero_grad(set_to_none=True);after=m.digest(dict(model=model.state_dict(),optimizer=opt.state_dict(),torchRng=torch.get_rng_state(),pythonRng=rng.getstate()));res['modelAdamRngUnchanged']=before==after
pathlib.Path('/workspace/assay-norm-audit.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps(res))
