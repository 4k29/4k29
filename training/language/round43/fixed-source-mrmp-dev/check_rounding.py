"""Full raw-selected FP32 versus exported generation on frozen fresh DEV only."""
import argparse,hashlib,importlib.util,json,pathlib,sys
D=pathlib.Path(__file__).resolve().parent;R=D.parent;read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--model',type=pathlib.Path,required=True);p.add_argument('--checkpoint',type=pathlib.Path,required=True);p.add_argument('--generation',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();result=R/'continue-10000/result.json';assert result.exists()and read(result)['completedRun']and read(result)['completedSteps']==10000,'Fixed exposed diagnostic waits for actual10000 completion'
sys.path.insert(0,str(R.parent/'round10'));spec=importlib.util.spec_from_file_location('raw_ev',R.parent/'round10/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev);ev.torch.set_num_threads(1)
g=read(a.generation);assert g['modelFileSha256']==sha(a.model)and g['probeSha256']==sha(D/'probes.json')and len(g['rows'])==5
cp=ev.torch.load(a.checkpoint,map_location='cpu',weights_only=False);assert cp['step']==10000 and cp['beststep']==g['training']['bestStep'];m=ev.Decoder(cp['config']);m.load_state_dict(cp['beststate']);m.eval();rounded,export=ev.load_model(a.model);rows=[];refs=[]
for i,row in enumerate(g['rows']):
 raw=ev.generate(m,row['prefix'],export['tokenizer'],192);same=all(raw[k]==row[k]for k in ['text','tokens','eos','validUtf8','validTokens','inputTokens']);rows.append(dict(id=row['id'],prefix=row['prefix'],**raw,sameAsExport=same))
 if i<4:
  x=ev.torch.tensor([[ev.SPECIALS['bos']]+ev.encode_stream(row['prefix'],export['tokenizer'])])
  with ev.torch.no_grad():err=float((m(x)[0,-1]-rounded(x)[0,-1]).abs().max())
  refs.append(dict(id=row['id'],maxAbsoluteLogitError=err))
out=dict(checkpointSha256=sha(a.checkpoint),modelSha256=sha(a.model),sourceGenerationSha256=sha(a.generation),evaluatorSha256=sha(pathlib.Path(__file__)),actualRetainedUpdates=10000,selectedStep=cp['beststep'],matchingSequences=sum(r['sameAsExport']for r in rows),totalSequences=5,completeRawVersusExportGenerationParity=all(r['sameAsExport']for r in rows),rows=rows,references=refs,additionalOptimizerUpdates=0,noOutputRepair=True,notTest=True);a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['rows','references']}))
