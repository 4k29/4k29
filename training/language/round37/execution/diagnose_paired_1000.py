"""Posthoc same-actual1000 raw-FP32 daily/native diagnostic; no selection or training."""
import pathlib,json,hashlib,sys,importlib.util,datetime,torch
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';O=E/'paired-development-1000';P=R.parent/'round36';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
O.mkdir(exist_ok=True);assert not (O/'complete.json').exists(),'Inspect saved evidence instead of repeating'
sys.path.insert(0,str(R.parent/'round10'));spec=importlib.util.spec_from_file_location('paired_raw_evaluator',R.parent/'round10/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev);torch.set_num_threads(1)
paths={'daily12':E/'daily-probes.json','native8':E/'content-native-dev/probes.json'};tok=read(R/'multiview/tokenizer.json');controls=read(E/'paired-control-snapshot-integrity.json');expected={x['actualUpdates']:x['checkpointSha256']for x in controls['controls']}
models={'retainedNewlineCeRound36':P/'execution/retained-paired-1000/checkpoint.pt','excludedNewlineCeRound37':E/'retained-paired-1000/checkpoint.pt'}
plan=dict(createdUtc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actualUpdatesEach=1000,posthoc=True,reason='Investigate whether paired TRAIN termination gains reflect contextual content on existing fixed DEV. Final10000 selected/terminal evaluation remains primary.',usedForCheckpointSelection=False,changeLearningConditions=False,modelMode='eval/no_grad raw own FP32, one thread',maxNewTokens=192,probes={k:dict(path=str(v.relative_to(R)),sha256=sha(v))for k,v in paths.items()},checkpoints={k:sha(v)for k,v in models.items()},evaluatorSha256=sha(R.parent/'round10/evaluate.py'),codeSha256=sha(pathlib.Path(__file__)),newTest=False,numericalScope='Raw Python FP32 only; no Py/JS or export-parity claim for this interim diagnostic')
(O/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');outputs=[]
for label,path in models.items():
 assert sha(path)==(expected[1000]if label=='retainedNewlineCeRound36'else read(E/'retained-paired-1000/snapshot.json')['checkpointSha256'])
 cp=torch.load(path,map_location='cpu',weights_only=False);assert cp['step']==1000 and sorted({int(x['step'])for x in cp['optimizer']['state'].values()})==[21000]
 model=ev.Decoder(cp['config']);model.load_state_dict(cp['model']);model.eval();assert model.config['context']==256
 for group,probe in paths.items():
  prompts=read(probe)['probes'];n={'daily12':12,'native8':8}[group];assert len(prompts)==n;out=O/f'{label}-{group}.json';assert not out.exists()
  rows=[]
  for item in prompts:
   result=ev.generate(model,item['prefix'],tok,192);rows.append(dict(**item,**result));print(json.dumps(dict(label=label,group=group,id=item['id'],tokens=len(result['tokens']),eos=result['eos'])),flush=True)
  d=dict(actualUpdates=1000,checkpointSha256=sha(path),probeSha256=sha(probe),tokenizerSha256=sha(R/'multiview/tokenizer.json'),maxNewTokens=192,rawFp32PythonOnly=True,usedForWeightSelection=False,notNewTest=True,rows=rows);out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');outputs.append(dict(label=label,group=group,path=str(out.relative_to(R)),sha256=sha(out),rows=n))
 del cp,model
(O/'complete.json').write_text(json.dumps(dict(actualUpdatesEach=1000,outputs=outputs,semanticReadingPending=True,additionalOptimizerUpdates=0,noChangeToOngoingTraining=True,planSha256=sha(O/'plan.json')),indent=2)+'\n');print('Paired40 fixed DEV state outputs saved; reading pending',flush=True)
