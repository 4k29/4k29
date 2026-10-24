"""Predeclared paired raw1000 daily DEV continuation; no updates or selection change."""
import pathlib,json,hashlib,sys,importlib.util,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';O=E/'paired-daily-generation-1000';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
O.mkdir(exist_ok=True);assert not(O/'complete.json').exists(),'Read existing output instead of rerun'
sys.path.insert(0,str(R.parent/'round10'));spec=importlib.util.spec_from_file_location('raw_ev',R.parent/'round10/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev);torch.set_num_threads(1);tok=read(R/'multiview/tokenizer.json');probe=E/'daily-probes.json';prompts=read(probe)['probes'];assert len(prompts)==12
checkpoints={f'round{n}':R.parent/f'round{n}/execution/retained-snapshots/1000/checkpoint.pt'for n in [39,40]};plan=dict(posthoc=False,reason='Inspect early meaning/loops separately from tiny humanDEV99 NLL difference; fixed final10000 assessment remains primary',actualUpdatesEach=1000,checkpoints={k:sha(p)for k,p in checkpoints.items()},probeSha256=sha(probe),maxNewTokens=192,rawFp32PythonOnly=True,noInterimJavascriptOrExportParityClaim=True,notNewTest=True,usedForWeightSelection=False,additionalOptimizerUpdates=0,codeSha256=sha(pathlib.Path(__file__)));(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
for label,path in checkpoints.items():
 cp=torch.load(path,map_location='cpu',weights_only=False);assert cp['step']==1000 and {int(x['step'])for x in cp['optimizer']['state'].values()}=={21000};m=ev.Decoder(cp['config']);m.load_state_dict(cp['model']);m.eval();rows=[]
 for p in prompts:
  g=ev.generate(m,p['prefix'],tok,192);rows.append(dict(**p,**g));print(label,p['id'],len(g['tokens']),g['eos'],flush=True)
 (O/f'{label}.json').write_text(json.dumps(dict(**plan,label=label,checkpointSha256=sha(path),rows=rows),ensure_ascii=False,indent=2)+'\n');del cp,m
lines=['# Paired actual1000 daily DEV: complete raw FP32 continuations','','Predeclared exposed development, not TEST or checkpoint selection. Same12 prefixes, own greedy192/raw Python FP32/one thread; no interim JS/export parity claim. No repair; reading pending.',''];old,new=read(O/'round39.json')['rows'],read(O/'round40.json')['rows']
for a,b in zip(old,new,strict=True):
 assert a['id']==b['id']and a['prefix']==b['prefix'];lines += [f"## {a['id']}",'','Full prefix:','```text',a['prefix'],'```','','R39 raw1000:','```text',a['text'],'```','','R40 raw1000:','```text',b['text'],'```','']
(O/'FULL_GENERATIONS.md').write_text('\n'.join(lines)+'\n');(O/'complete.json').write_text(json.dumps(dict(actualUpdatesEach=1000,outputs=24,semanticReadingPending=True,fullTextSha256=sha(O/'FULL_GENERATIONS.md'),planSha256=sha(O/'plan.json'),additionalOptimizerUpdates=0),indent=2)+'\n')
