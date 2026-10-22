"""Fixed native mid-dialogue DEV; raw own generation, never TEST/selector."""
import pathlib,json,hashlib,sys,argparse,importlib.util,time
D=pathlib.Path(__file__).resolve().parent;R=D.parents[1];sys.path.insert(0,str(R.parent/'round10'));spec=importlib.util.spec_from_file_location('original_raw_evaluator',R.parent/'round10/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev);ev.torch.set_num_threads(1)
p=argparse.ArgumentParser();p.add_argument('--model',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();probes=json.loads((D/'probes.json').read_text());assert len(probes['probes'])==8
m,export=ev.load_model(a.model);out=dict(modelFileSha256=sha(a.model),training=export['training'],partition='additional-exposed-content-native-DEV-not-TEST',probeSha256=sha(D/'probes.json'),evaluatorSha256=sha(pathlib.Path(__file__)),rawEvaluatorSha256=sha(R.parent/'round10/evaluate.py'),evaluationThreads=1,maxNewTokens=192,usedForWeightSelection=False,rows=[],references=[])
for row in probes['probes']:
 start=time.monotonic();tokens=[ev.SPECIALS['bos']]+ev.encode_stream(row['prefix'],export['tokenizer']);assert len(tokens)==row['prefixTokens']<=64
 result=ev.generate(m,row['prefix'],export['tokenizer'],192);out['rows'].append(dict(**row,**result,elapsedSeconds=time.monotonic()-start));print(json.dumps(dict(id=row['id'],**result),ensure_ascii=False),flush=True)
for row in out['rows'][:4]:
 tokens=[ev.SPECIALS['bos']]+ev.encode_stream(row['prefix'],export['tokenizer'])
 with ev.torch.no_grad():z=m(ev.torch.tensor([tokens]))[0,-1]
 out['references'].append(dict(id=row['id'],tokens=tokens,logits=z.tolist()))
a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
