"""Own autoregressive generation on fixed human DEV native openings; no optimizer."""
import pathlib,json,hashlib,importlib.util,sys,time
O=pathlib.Path(__file__).resolve().parent;R=O.parents[1];B=R.parent;sys.path.insert(0,str(B/'round10'));spec=importlib.util.spec_from_file_location('native_raw_eval',B/'round10/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev);ev.torch.set_num_threads(1);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();protocol=json.loads((O/'protocol.json').read_text())
for name,modelpath in [('adopted25',B/'round25/continue-10000/model.js'),('human30round28',B/'round28/continue-10000/model.js'),('interim10round29',R/'execution/interim-daily-2100/model.js')]:
 model,export=ev.load_model(modelpath);rows=[]
 for p in protocol['probes']:
  ids=[ev.SPECIALS['bos']]+ev.encode_stream(p['prefix'],export['tokenizer']);assert len(ids)<=model.config['context'];start=time.monotonic();g=ev.generate(model,p['prefix'],export['tokenizer'],192);rows.append(dict(**p,**g,elapsedSeconds=time.monotonic()-start));print(json.dumps(dict(model=name,id=p['id'],eos=g['eos'],tokens=len(g['tokens'])),ensure_ascii=False),flush=True)
 record=dict(model=name,modelFileSha256=sha(modelpath),protocolSha256=sha(O/'protocol.json'),evaluatorSha256=sha(pathlib.Path(__file__)),rawEvaluatorSha256=sha(B/'round10/evaluate.py'),developmentOnly=True,testUsed=False,checkpointSelectionUsed=False,optimizerUpdates=0,generationConditions=protocol['generation'],rows=rows)
 (O/(name+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
