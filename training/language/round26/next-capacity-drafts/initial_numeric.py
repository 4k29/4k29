"""Future FFN capacity numerical preflight only; zero model optimizer updates."""
import pathlib,sys,json,hashlib,subprocess
REPO=pathlib.Path('/workspace/4k29');B=REPO/'training/language';OUT=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(B/'round25'));import train as t
sys.path.insert(0,str(B/'round24/next-candidate-drafts'));from capacity import expand_ffn_weights
sys.path.insert(0,str(B/'round10'));from evaluate import generate,load_model,encode_stream,SPECIALS
t.torch.set_num_threads(1);t.torch.use_deterministic_algorithms(True);t.torch.manual_seed(2049)
cp=t.torch.load(B/'round11/continue-10000/checkpoint.pt',map_location='cpu',weights_only=False);cfg=dict(cp['config'],hidden=1536);m=t.Decoder(cfg);expand_ffn_weights(m,cp);m.eval();old=t.Decoder(cp['config']);old.load_state_dict(cp['model']);old.eval()
index,values=t.load_partition(B/'round25/multiview','train');tok=t.read(B/'round25/multiview/tokenizer.json');vocab=[bytes.fromhex(x) for x in tok['bytes']];doc=next(x for x in index['rows'] if x['variant']==0 and x['length']==257);x,_=t.pack([doc],values,256);probes=[]
with t.torch.no_grad():
 for width in [32,64,128,256]:
  a,b=old(x[:,:width]),m(x[:,:width]);error=float((a-b).abs().max());assert error<=.0002;probes.append(dict(length=width,maxAbsoluteLogitError=error,allArgmaxEqual=bool(t.torch.equal(a.argmax(-1),b.argmax(-1)))))
state_hash=hashlib.sha256()
for name,tensor in m.state_dict().items():state_hash.update(name.encode()+b'\0');state_hash.update(tensor.detach().numpy().tobytes())
training=dict(wordMerges=512,parameters=7021248,completedSteps=0,parentCheckpointSha256=t.sha(B/'round11/continue-10000/checkpoint.pt'),preparationOnly=True)
model_path=OUT/'initial-model.js';t.export_model(m,m.state_dict(),tok,cfg,training,model_path);rounded,export=load_model(model_path);rows=[];refs=[];raw=[];errors=[]
for i,doc in enumerate([d for d in index['documents'] if d['variant']==0][:2]):
 full=values[doc['offset']+1:doc['offset']+doc['length']-1];opening=b''.join(vocab[int(v)] for v in full).decode('utf8')[:40];result=generate(rounded,opening,tok,8);raw_result=generate(m,opening,tok,8);ids=[SPECIALS['bos']]+encode_stream(opening,tok)
 with t.torch.no_grad():a=m(t.torch.tensor([ids]))[0,-1];b=rounded(t.torch.tensor([ids]))[0,-1]
 rows.append(dict(id='train-only-preflight-'+str(i),prefix=opening,**result));refs.append(dict(id=rows[-1]['id'],tokens=ids,logits=b.tolist()));raw.append(dict(id=rows[-1]['id'],prefix=opening,**raw_result));errors.append(float((a-b).abs().max()))
python_path=OUT/'initial-python.json';t.write(python_path,dict(rows=rows,references=refs,maxNewTokens=8,trainingOnly=True,preparationOnly=True,additionalOptimizerUpdates=0,modelSha256=t.sha(model_path)))
with (OUT/'initial-js.log').open('w') as log:status=subprocess.run(['node',str(B/'round10/evaluate_js.mjs'),str(model_path),str(python_path),str(OUT/'initial-javascript.json')],stdout=log,stderr=subprocess.STDOUT).returncode
js=t.read(OUT/'initial-javascript.json');assert js['modelSha256']==t.sha(model_path)
record=dict(preparationOnly=True,usedByRound26=False,additionalExperimentalOptimizerUpdates=0,optimizerInstantiated=False,initialFunctionProbes=probes,config=cfg,rawInitialModelStateSha256=state_hash.hexdigest(),parentCheckpointSha256=t.sha(B/'round11/continue-10000/checkpoint.pt'),capacityCodeSha256=t.sha(B/'round24/next-candidate-drafts/capacity.py'),tokenizerSha256=t.sha(B/'round25/multiview/tokenizer.json'),modelExportSha256=t.sha(model_path),pythonProbeSha256=t.sha(python_path),javascriptProbeSha256=t.sha(OUT/'initial-javascript.json'),scriptSha256=t.sha(pathlib.Path(__file__)),nodeExitCode=status,pythonJavascriptCompleteParity=js['completeGenerationParity'],maxReferenceLogitError=max(r['maxAbsoluteError'] for r in js['references']),toleranceUnchanged=.0002,rawVsRoundedReferenceErrors=errors,rawVsRoundedCompleteParity=all(all(a[k]==b[k] for k in ['text','tokens','eos','validUtf8','validTokens','inputTokens']) for a,b in zip(raw,rows,strict=True)),rawUnroundedRows=raw,noDevelopmentOrTestRead=True,noOutputRepair=True)
t.write(OUT/'initial-numeric-result.json',record);print(json.dumps({k:v for k,v in record.items() if k not in ['rawUnroundedRows','config','initialFunctionProbes']}))
if status:raise SystemExit(status)
