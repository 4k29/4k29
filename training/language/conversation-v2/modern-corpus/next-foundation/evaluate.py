"""Frozen full-vocabulary generation and NLL on exposed diagnostic suites only."""
import pathlib,sys,argparse,time,collections
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent.parent))
from next_runtime import *
from prose_decode import greedy

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--arm',choices=['A','B'],required=True);parser.add_argument('--step',type=int,required=True);args=parser.parse_args();out=D/'evaluation'/f'{args.arm}-{args.step}.json';assert not out.exists(),'Do not overwrite prior outputs';plan=read(D/'PLAN.json');protocol=read(ROOT/plan['evaluation_path']);torch.set_num_threads(2);torch.use_deterministic_algorithms(True);start=time.time()
 if args.step==0:model,_,_,_=starting(args.arm);checkpoint=dict(kind='PR104'+args.arm+'6459 own reached weights, new AdamW; B has own-random-origin history',step=0)
 else:
  path=RUN/args.arm/f'checkpoint-{args.step:05d}.pt';receipt=read(RUN/args.arm/f'receipt-{args.step:05d}.json');assert sha(path)==receipt['checkpoint_sha256'];obj=torch.load(path,weights_only=False);assert obj['plan_sha256']==sha(D/'PLAN.json');model,_,_=restore_isolated(obj['trajectory']);checkpoint=dict(path=str(path.relative_to(ROOT)),sha256=receipt['checkpoint_sha256'],step=args.step)
 model.eval();pieces=[bytes.fromhex(s)for s in read(N.parent/'data/tokenizer.json')['bytes']];totals=collections.defaultdict(lambda:[0.,0]);cases=[]
 with torch.inference_mode():
  for key,rows in [('old_dev_windows',protocol['old_dev_windows']),('caption_dev',protocol['caption_dev']),('maff_dev',protocol['maff_dev'])]:
   for i in range(0,len(rows),4):
    batch=rows[i:i+4];x,y=legacy.pack(batch);log=model(x)
    for j,r in enumerate(batch):
     value=float(torch.nn.functional.cross_entropy(log[j],y[j],ignore_index=-100,reduction='sum'));panel=r.get('panel',key);totals[panel][0]+=value;totals[panel][1]+=int(y[j].ne(-100).sum())
  for c in protocol['cases']:
   g=greedy(model,c['prefix'],pieces,max_new=128);g['decoder_legacy_stopReason']=g['stopReason'];g['stopReason']='genuine-end-unit-token2'if g['eos']else'fixed-max-new-tokens';cases.append(dict(**{k:v for k,v in c.items()if k!='text'},source_reference_text=c.get('text'),**g));print(args.arm,args.step,c['panel'],c['id'],'EOS',g['eos'],flush=True)
 panels={panel:dict(cases=sum(c['panel']==panel for c in cases),EOS=sum(c['eos']for c in cases if c['panel']==panel),repeat4=sum(c['repeated4gram']is not None for c in cases if c['panel']==panel))for panel in sorted({c['panel']for c in cases})}
 summary=dict(checkpoint=checkpoint,NLL={k:dict(nll=v[0]/v[1],targets=v[1])for k,v in totals.items()},panels=panels,seconds=time.time()-start,optimizer_updates=0,evaluation_protocol_sha256=sha(ROOT/plan['evaluation_path']),semantic_success='Needs full reading; not inferred from NLL/EOS/repeat alone',all_DEV_exposed_diagnostic=True,independent_human_evaluation=False)
 write(out,dict(summary=summary,cases=cases));write(out.with_name(out.stem+'-summary.json'),summary);print(summary,flush=True)
if __name__=='__main__':main()
