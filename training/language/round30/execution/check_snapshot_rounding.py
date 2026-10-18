"""Read-only full raw/export parity for an immutable inference snapshot."""
import pathlib,json,hashlib,sys,importlib.util,argparse
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R.parent/'round10'));spec=importlib.util.spec_from_file_location('raw_eval',R.parent/'round10/evaluate.py');ev=importlib.util.module_from_spec(spec);spec.loader.exec_module(ev);ev.torch.set_num_threads(1)
p=argparse.ArgumentParser();p.add_argument('--snapshot',type=pathlib.Path,required=True);p.add_argument('--generation',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True);a=p.parse_args();read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();s=ev.torch.load(a.snapshot/'selected-inference-weights.pt',map_location='cpu',weights_only=False);m=ev.Decoder(s['config']);m.load_state_dict(s['state']);m.eval();rounded,export=ev.load_model(a.snapshot/'model.js');g=read(a.generation);assert g['modelFileSha256']==sha(a.snapshot/'model.js');rows=[];errors=[]
for i,row in enumerate(g['rows']):
 raw=ev.generate(m,row['prefix'],export['tokenizer'],192);same=all(raw[k]==row[k] for k in ['text','tokens','eos','validUtf8','validTokens','inputTokens']);rows.append(dict(id=row['id'],prefix=row['prefix'],**raw,sameAsRounded=same))
 if i<4:
  x=ev.torch.tensor([[ev.SPECIALS['bos']]+ev.encode_stream(row['prefix'],export['tokenizer'])])
  with ev.torch.no_grad():error=float((m(x)[0,-1]-rounded(x)[0,-1]).abs().max())
  errors.append(dict(id=row['id'],maxAbsoluteError=error))
out=dict(sourceGenerationSha256=sha(a.generation),snapshotWeightsSha256=sha(a.snapshot/'selected-inference-weights.pt'),selectedStep=s['selectedStep'],actualRetainedUpdates=s['actualRetainedUpdates'],matchingSequences=sum(x['sameAsRounded'] for x in rows),totalSequences=len(rows),completeRawVersusRoundedGenerationParity=all(x['sameAsRounded'] for x in rows),rows=rows,references=errors,additionalOptimizerUpdates=0,outputRepair=False)
a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['rows','references']}))
