"""Supplementary daily DEV: raw FP32 vs selected7-decimal export, full outputs kept."""
import hashlib,importlib.util,json,pathlib,sys
R=pathlib.Path(__file__).resolve().parents[2];E=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'round10'))
spec=importlib.util.spec_from_file_location('daily_raw_rounding',R.parent/'round10/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev);ev.torch.set_num_threads(1)
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'developmentOnly':True,'reservedTestRead':False,'additionalOptimizerUpdates':0,'generationConditionsChanged':False,'models':{}}
for name,root in [('new',E)]:
 saved=ev.torch.load(root/'selected-inference-weights.pt',map_location='cpu',weights_only=False);m=ev.Decoder(saved['config']);m.load_state_dict(saved['state']);m.eval();rounded,export=ev.load_model(root/'model.js');g=read(E/'daily-python.json');tok=export['tokenizer']
 assert g['modelFileSha256']==sha(root/'model.js') and g['maxNewTokens']==192 and g['evaluationThreads']==1
 assert saved['selectedStep']==export['training']['bestStep'];assert len(g['rows'])==12
 rows=[];differences=[];references=[];matches=0
 for row in g['rows']:
  raw=ev.generate(m,row['prefix'],tok,192);rows.append(dict(id=row['id'],prefix=row['prefix'],group=row['group'],**raw))
  same=all(raw[k]==row[k] for k in ['text','tokens','eos','validUtf8','validTokens','inputTokens']);matches+=same
  if not same:
   a=raw['tokens']+([ev.SPECIALS['eos']] if raw['eos'] else []);b=row['tokens']+([ev.SPECIALS['eos']] if row['eos'] else []);index=next(i for i,(x,y) in enumerate(zip(a,b)) if x!=y)
   prefix=[ev.SPECIALS['bos']]+ev.encode_stream(row['prefix'],tok)+a[:index]
   with ev.torch.no_grad():x=m(ev.torch.tensor([prefix]))[0,-1];y=rounded(ev.torch.tensor([prefix]))[0,-1]
   differences.append(dict(id=row['id'],firstDifferentGeneratedPosition=index,commonInputTokens=prefix,rawNextToken=a[index],roundedNextToken=b[index],rawTopTwoGap=float(ev.torch.topk(x,2).values.diff().abs()[0]),roundedTopTwoGap=float(ev.torch.topk(y,2).values.diff().abs()[0]),maxAbsoluteLogitError=float((x-y).abs().max())))
  if len(references)<4:
   prefix=[ev.SPECIALS['bos']]+ev.encode_stream(row['prefix'],tok)
   with ev.torch.no_grad():x=m(ev.torch.tensor([prefix]))[0,-1];y=rounded(ev.torch.tensor([prefix]))[0,-1]
   references.append(dict(id=row['id'],maxAbsoluteLogitError=float((x-y).abs().max()),argmaxEqual=int(x.argmax())==int(y.argmax())))
 raw_path=E/f'daily-{name}-unrounded.json';raw_path.write_text(json.dumps(dict(rawSelectedWeightsSha256=sha(root/'selected-inference-weights.pt'),selectedStep=saved['selectedStep'],roundedModelSha256=g['modelFileSha256'],roundedGenerationSha256=sha(E/'daily-python.json'),maxNewTokens=192,evaluationThreads=1,rows=rows),ensure_ascii=False,indent=2)+'\n')
 report['models'][name]=dict(matchingSequences=matches,total=12,differences=differences,references=references,unroundedGenerationSha256=sha(raw_path),allRawFullOutputsRetained=True,allRawUtf8Valid=all(x['validUtf8'] for x in rows),selectedStep=saved['selectedStep'])
(E/'daily-rounding-comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({n:{'matchingSequences':v['matchingSequences'],'differences':v['differences']} for n,v in report['models'].items()}))
