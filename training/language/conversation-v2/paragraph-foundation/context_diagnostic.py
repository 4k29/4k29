"""Fixed TRAIN-only conditional-history diagnostic; zero optimizer updates."""
import argparse,hashlib
from study_runtime import *
from load_model import load
import context_preserving

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--freeze',action='store_true');ap.add_argument('--model');a=ap.parse_args();protocol=P/'CONTEXT_DIAGNOSTIC_PROTOCOL.json';corpus,schedule=load_data()
 if a.freeze:
  assert not protocol.exists();refs=[r for b in schedule['arms']['B']for r in b if r['start']%256 and r['length']>=17];refs.sort(key=lambda r:hashlib.sha256(('paragraph-conditional-history-v1|'+corpus[r['record']]['id']+'|'+str(r['start'])).encode()).hexdigest());chosen=refs[:32];assert len(chosen)==32
  write(protocol,dict(refs=chosen,selection='Fixed32 hash-ranked batch-split B TRAIN rows; >=16 target positions. Not DEV or TEST.',source_corpus_sha256=sha(P/'corpus.jsonl.gz'),schedule_sha256=sha(P/'schedule.json.gz'),purpose='Compare actual identical teacher positions with shortened row history versus restored original256-window prefix; includes changed position layout. No language success or checkpoint selection.',generation_outputs_used_for_selection=False,updates=0,tolerance=2e-5));return
 assert a.model;out=P/'context-diagnostic'/(a.model+'.json');assert not out.exists();out.parent.mkdir(exist_ok=True);p=read(protocol);assert sha(P/'corpus.jsonl.gz')==p['source_corpus_sha256'];torch.set_num_threads(2);torch.use_deterministic_algorithms(True);model,_=load(a.model);model.eval();rows=[];totals={k:[0.,0]for k in ['shortened','restored']}
 with torch.inference_mode():
  for ref in p['refs']:
   x,y=pack(windows(corpus,[ref]));xx,yy,meta=context_preserving.pack(corpus,[ref],torch);targets=y[y.ne(-100)];assert torch.equal(targets,yy[yy.ne(-100)]);lo=model(x);hi=model(xx);n=len(targets);lost=meta[0]['prefix_only_positions'];short=float(torch.nn.functional.cross_entropy(lo[0,:n],targets,reduction='sum'));restored=float(torch.nn.functional.cross_entropy(hi[0,lost:lost+n],targets,reduction='sum'))
   begin=meta[0]['original_window_start'];full=corpus[ref['record']]['tokens'][begin:begin+257];oracle=model(torch.tensor([full[:-1]],dtype=torch.long))[0,lost:lost+n];error=float((oracle-hi[0,lost:lost+n]).abs().max());assert error<=p['tolerance']
   for name,v in [('shortened',short),('restored',restored)]:totals[name][0]+=v;totals[name][1]+=n
   rows.append(dict(record_id=corpus[ref['record']]['id'],start=ref['start'],targets=n,restored_prefix_tokens=lost,shortened_nll=short/n,restored_nll=restored/n,original_window_logit_max_error=error))
 write(out,dict(model=a.model,protocol_sha256=sha(protocol),rows=rows,weighted_NLL={k:v[0]/v[1]for k,v in totals.items()},common_targets=totals['shortened'][1],original_window_score_equivalence_verified=True,actual_optimizer_updates=0,no_new_condition_training=True,not_generalization=True,interpretation='Lower teacher-forced NLL alone is not coherent free generation; this isolates input-conditioning/position-layout sensitivity on TRAIN positions.'))
 print(json.dumps(read(out)['weighted_NLL']))
if __name__=='__main__':main()
