"""Retain PR104 reached weights; reset Adam equally to isolate starting weights.
Fresh refers to the own-random-origin lineage, not a new random reset this task.
"""
import pathlib,sys,json,hashlib
N=pathlib.Path(__file__).resolve().parent;D=N/'next-foundation';OLD=N.parent/'diverse-foundation';sys.path.insert(0,str(OLD));import common as old

def main():
 old.torch.set_num_threads(2);states={};refs={}
 for arm in ['A','B']:
  manifest=OLD/'run'/arm/'archive-06459/checkpoint.json';meta=json.loads(manifest.read_text());obj=old.loader.load_checkpoint(manifest,meta['sha256']);states[arm]=obj['trajectory'];refs[arm]=dict(manifest=str(manifest.relative_to(N.parents[3])),checkpoint_sha256=meta['sha256'],source_study_cursor=6459,base_model_unique_updates=states[arm]['uniqueUpdates'],source_Adam_steps=sorted({int(v['step'])for v in states[arm]['optimizer']['state'].values()}),use='model weights/config only; optimizer intentionally reset equally; source checkpoint unchanged')
 same=old.torch.equal(states['A']['torchRng'],states['B']['torchRng']);assert same
 payload=dict(sources=refs,common_dropout_rng_source='PR104B6459; sourceA/B Torch RNG equality verified',torch_rng_bytes=states['B']['torchRng'].tolist(),private_python_rng_state=states['B']['pythonRng'],source_torch_rngs_equal=same,optimizer_initialization='New AdamW for both; .9/.999,eps1e-8,weight_decay.05,LR<=3e-5',fresh_lineage='B originated from own random seed41029 in PR104 and already processed4,871,648targets; this task preserves that learning and does not call it an untrained model',historical_learning='A also has earlier3470 RP updates; equal additional token budget is not equal cumulative history',optimizer_updates=0)
 (D/'INITIAL_REFERENCES.json').write_text(json.dumps(payload,indent=2)+'\n');print('Terminal weights preserved; counters',{a:r['base_model_unique_updates']for a,r in refs.items()},'common RNG',same)
if __name__=='__main__':main()
