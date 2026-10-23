import pathlib,time,io,json,hashlib,torch
R=pathlib.Path('/workspace/4k29/training/language/round39');E=R/'execution';torch.set_num_threads(1);wanted={200,1000,5000};done=set()
while True:
 p=R/'continue-10000/checkpoint.pt'
 if not p.exists():time.sleep(5);continue
 raw=p.read_bytes();cp=torch.load(io.BytesIO(raw),weights_only=False,map_location='cpu');step=cp['step']
 if step in wanted and step not in done:
  assert {int(s['step'])for s in cp['optimizer']['state'].values()}=={20000+step};out=E/'retained-snapshots'/str(step);out.mkdir(parents=True,exist_ok=True);dest=out/'checkpoint.pt'
  if dest.exists():assert hashlib.sha256(dest.read_bytes()).digest()==hashlib.sha256(raw).digest()
  else:dest.write_bytes(raw)
  (out/'identity.json').write_text(json.dumps(dict(actualUpdates=step,checkpointSha256=hashlib.sha256(raw).hexdigest(),fullAlignedModelOptimizerAndRng=True,additionalOptimizerUpdates=0),indent=2)+'\n');done.add(step)
 if step>=10000:break
 time.sleep(8)
