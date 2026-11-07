"""Fixed MRMP human DEV, already exposed since R32, after actual10000 only; never TEST or a selector."""
import argparse,hashlib,importlib.util,json,pathlib,sys,time
D=pathlib.Path(__file__).resolve().parent;R=D.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
p=argparse.ArgumentParser();p.add_argument('--model',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args()
result=R/'continue-10000/result.json'
assert result.exists() and read(result)['completedRun'] and read(result)['completedSteps']==10000,'Fixed exposed diagnostic waits for actual10000 completion'
assert a.model.resolve()in {(R/'continue-10000/model.js').resolve(),(R.parent/'round38/continue-10000/model.js').resolve()}
probes=read(D/'probes.json');assert probes['selectionPolicySha256']==sha(D/'policy.json') and probes['sourceManifestSha256']==sha(D/'source-manifest.json');assert probes['onlyDevelopmentTokenized'] and probes['notTest'] and len(probes['probes'])==probes['actualContexts']==5
identity=dict(modelFileSha256=sha(a.model),probeSha256=sha(D/'probes.json'),evaluatorSha256=sha(pathlib.Path(__file__)),rawEvaluatorSha256=sha(R.parent/'round10/evaluate.py'))
if a.out.exists():
 old=read(a.out);assert all(old[k]==v for k,v in identity.items());assert len(old['rows'])==5;print('Exact existing frozen fresh DEV outputs reused');raise SystemExit
sys.path.insert(0,str(R.parent/'round10'));spec=importlib.util.spec_from_file_location('own_raw_evaluator',R.parent/'round10/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev);ev.torch.set_num_threads(1)
m,export=ev.load_model(a.model);assert sha(R/'multiview/tokenizer.json')==probes['tokenizerSha256'];out=dict(**identity,training=export['training'],partition='fixed MRMP source DEV, already exposed since R32; not TEST',evaluationThreads=1,maxNewTokens=192,sourceRepository=probes['sourceRepository'],sourceCommit=probes['sourceCommit'],independentSpeakerCombinationFamilies=1,distinctPublicSpeakerIds=3,notIndependentFiveSpeakers=True,usedForWeightSelection=False,originalStrictGatesChanged=False,modelTrainingUpdates=0,rows=[],references=[])
for row in probes['probes']:
 tokens=[ev.SPECIALS['bos']]+ev.encode_stream(row['prefix'],export['tokenizer']);assert len(tokens)==row['prefixTokens']<=64;start=time.monotonic();g=ev.generate(m,row['prefix'],export['tokenizer'],192);out['rows'].append(dict(**row,**g,elapsedSeconds=time.monotonic()-start));print(json.dumps(dict(id=row['id'],**g),ensure_ascii=False),flush=True)
for row in out['rows'][:4]:
 tokens=[ev.SPECIALS['bos']]+ev.encode_stream(row['prefix'],export['tokenizer'])
 with ev.torch.no_grad():z=m(ev.torch.tensor([tokens]))[0,-1]
 out['references'].append(dict(id=row['id'],tokens=tokens,logits=z.tolist()))
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
