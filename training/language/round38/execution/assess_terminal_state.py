"""Read-only terminal-state diagnosis, same fixed inputs/greedy192, no selection change.
Official NLL-selected assessment remains primary. Never train or repair outputs.
"""
import pathlib,json,hashlib,sys,importlib.util,subprocess,datetime
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';O=E/'terminal-state-diagnostic';repo=R.parents[2];read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result=R/'continue-10000/result.json';assert result.exists()and read(result)['completedRun']and read(result)['completedSteps']==10000,'Terminal diagnostic waits for actual10000 completion'
if (O/'mechanical-complete.json').exists():raise SystemExit('Already assessed; inspect instead of duplicating')
inputs={'original17':E/'new-validation.json','daily12':E/'daily-new-python.json','native8':E/'content-native-dev/new-python.json','mrmp5':R/'fixed-source-mrmp-dev/probes.json'};assert all(p.exists()for p in inputs.values()),'Complete missing primary evaluation first, no training restart'
plan=read(E/'terminal-diagnostic-plan.json')
for group,path in inputs.items():
 data=read(path);items=data['probes']if group=='mrmp5'else data['rows'];digest=hashlib.sha256(json.dumps([dict(id=x['id'],prefix=x['prefix'])for x in items],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest();assert digest==plan['promptListSha256'][group]
import torch
torch.set_num_threads(1);cp_path=R/'continue-10000/checkpoint.pt';cp=torch.load(cp_path,map_location='cpu',weights_only=False);assert cp['step']==10000 and read(result)['checkpointSha256']==sha(cp_path);assert sorted({int(x['step'])for x in cp['optimizer']['state'].values()})==[30000];O.mkdir(exist_ok=True)
identity=dict(actualTerminalUpdates=10000,terminalOptimizerCounter=30000,originalTrialSelectedStep=cp['beststep'],checkpointSha256=sha(cp_path),terminalCommonDevNll=cp['history'][-1]['validation']['nllPerUtf8Byte'],officialSelectedCommonDevNll=cp['bestloss'],terminalWeightLineageUpdates=59000+cp['step'],noOptimizerOrLearningChange=True,notUsedForSelection=True,notNewTest=True,codeSha256=sha(pathlib.Path(__file__)))
if all(torch.equal(v,cp['beststate'][k])for k,v in cp['model'].items()):
 (O/'mechanical-complete.json').write_text(json.dumps(dict(**identity,terminalAndSelectedWeightsExactlyEqual=True,duplicateGenerationAvoided=True,additionalOptimizerUpdates=0,semanticReadingUsesPrimarySameWeightsResults=True),indent=2)+'\n');print('Terminal and selected arrays exactly equal; primary generation already covers terminal');raise SystemExit
# Same own seven-decimal export operation. Header identifies latest, not official beststate.
tok=read(R/'multiview/tokenizer.json');params=sum(t.numel()for t in cp['model'].values());assert params==4655808;assert all(t.dtype==torch.float32 and torch.isfinite(t).all()for t in cp['model'].values())
training=dict(**cp['settings'],completedRun=True,completedSteps=10000,requestedSteps=10000,evaluatedStep=10000,originalTrialSelectedStep=cp['beststep'],weightsKind='latest model state; NOT NLL-selected beststate',parameters=params,checkpointSha256=sha(cp_path),selection='Exploratory terminal-state assessment; original selector unchanged')
export=dict(version='round38-terminal-actual10000-'+sha(cp_path)[:12],config=cp['config'],tokenizer=tok,training=training,tensors={k:dict(shape=list(t.shape),data=[round(float(x),7)for x in t.flatten()])for k,t in cp['model'].items()});modelpath=O/'model.js';modelpath.write_text('export const dialogueModel='+json.dumps(export,ensure_ascii=False,separators=(',',':'))+';\n');del export
sys.path.insert(0,str(R.parent/'round10'));spec=importlib.util.spec_from_file_location('own_terminal_evaluator',R.parent/'round10/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev);rounded,exp=ev.load_model(modelpath);raw_model=ev.Decoder(cp['config']);raw_model.load_state_dict(cp['model']);raw_model.eval();statuses={};summaries={}
for group,path in inputs.items():
 base=read(path);originalrows=base['probes']if group=='mrmp5'else base['rows'];expected={'original17':17,'daily12':12,'native8':8,'mrmp5':5}[group];assert len(originalrows)==expected
 out=dict(modelFileSha256=sha(modelpath),modelVersion=exp['version'],training=training,partition='validation'if group=='original17'else group+' exposed DEV; terminal diagnostic NOT TEST',evaluationThreads=1,maxNewTokens=192,evaluatorSha256=sha(pathlib.Path(__file__)),rawEvaluatorSha256=sha(R.parent/'round10/evaluate.py'),fixedInputFileSha256=sha(path),usedForWeightSelection=False,rows=[],references=[]);rawrows=[];differences=[];rawrefs=[]
 for item in originalrows:
  fields={k:item[k]for k in ['id','prefix','site','group']if k in item};a=ev.generate(rounded,item['prefix'],tok,192);b=ev.generate(raw_model,item['prefix'],tok,192);same=all(a[k]==b[k]for k in ['text','tokens','eos','validUtf8','validTokens','inputTokens']);out['rows'].append(dict(**fields,**a));rawrows.append(dict(**fields,**b,sameAsExport=same))
  if not same:
   x=b['tokens']+([ev.SPECIALS['eos']]if b['eos']else []);y=a['tokens']+([ev.SPECIALS['eos']]if a['eos']else []);j=next((i for i,(u,v)in enumerate(zip(x,y))if u!=v),min(len(x),len(y)));prefix=[ev.SPECIALS['bos']]+ev.encode_stream(item['prefix'],tok)+x[:j]
   with ev.torch.no_grad():p=raw_model(ev.torch.tensor([prefix]))[0,-1];q=rounded(ev.torch.tensor([prefix]))[0,-1]
   differences.append(dict(id=item['id'],firstDifferentGeneratedPosition=j,rawToken=x[j]if j<len(x)else None,exportToken=y[j]if j<len(y)else None,maxAbsoluteLogitError=float((p-q).abs().max())))
 for item in out['rows'][:4]:
  x=[ev.SPECIALS['bos']]+ev.encode_stream(item['prefix'],tok)
  with ev.torch.no_grad():z=rounded(ev.torch.tensor([x]))[0,-1];r=raw_model(ev.torch.tensor([x]))[0,-1]
  rawrefs.append(dict(id=item['id'],maxAbsoluteLogitError=float((r-z).abs().max()),argmaxEqual=int(r.argmax())==int(z.argmax())))
  out['references'].append(dict(id=item['id'],tokens=x,logits=z.tolist()))
 gen=O/f'{group}-python.json';gen.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');(O/f'{group}-unrounded.json').write_text(json.dumps(dict(**identity,sourceGenerationSha256=sha(gen),modelSha256=sha(modelpath),matchingSequences=sum(r['sameAsExport']for r in rawrows),totalSequences=expected,differences=differences,references=rawrefs,rows=rawrows,additionalOptimizerUpdates=0),ensure_ascii=False,indent=2)+'\n')
 with (O/f'{group}-parity.log').open('ab',buffering=0)as log:status=subprocess.run(['node',str(R.parent/'round10/evaluate_js.mjs'),str(modelpath),str(gen),str(O/f'{group}-javascript.json')],cwd=repo,stdout=log,stderr=subprocess.STDOUT).returncode
 statuses[group]=status;summaries[group]=dict(rawExportMatchingSequences=sum(r['sameAsExport']for r in rawrows),total=expected,rawExportDifferences=differences,javascriptExitCode=status);print('Terminal diagnosis mechanical group complete',group,flush=True)
record=dict(**identity,terminalAndSelectedWeightsExactlyEqual=False,modelSha256=sha(modelpath),javascriptExitCodes=statuses,numerical=summaries,all42RoundedAndRawFullOutputsSaved=True,semanticReadingPending=True,noSemanticScoreGuessed=True,additionalOptimizerUpdates=0,utc=datetime.datetime.now(datetime.timezone.utc).isoformat());(O/'mechanical-complete.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
