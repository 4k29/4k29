"""Frozen endpoints only; no optimizer, selection, output repair or TEST access."""
import argparse, hashlib, importlib.util, json, pathlib, sys
import torch

HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OLD=HERE.parent/'context-use-20261025'
sys.path.insert(0,str(OLD))
from diagnostic_core import teacher_forced, aggregate, greedy, generated_history_probe, repeated_ngram_onset
from run_diagnostic import sha, read, write, state_digest

def run(a):
    assert sha(a.panel)==a.panel_sha256 and sha(a.plan)==a.plan_sha256
    p=read(a.panel); plan=read(a.plan)
    assert plan['panelSha256']==a.panel_sha256
    for name,h in plan['codeReceipts'].items(): assert sha(ROOT/name)==h,name
    assert not a.output.exists()
    torch.set_num_threads(1); torch.use_deterministic_algorithms(True)
    spec=importlib.util.spec_from_file_location('own_model',ROOT/'training/language/model.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    checkpoint=(ROOT/'training/language/round46/continue-10000/best-aligned-checkpoint.pt') if a.endpoint=='baseline' else a.checkpoint
    assert checkpoint and checkpoint.is_file()
    if a.endpoint=='baseline': assert sha(checkpoint)=='d99f85f706d40702393410c05733274bcc59528c7c776ff9ba3cea74d2647f1d'
    saved=torch.load(checkpoint,map_location='cpu',weights_only=False)
    rng=torch.get_rng_state().clone()
    model=mod.Decoder(saved['config']); model.load_state_dict(saved['model']); model.eval(); torch.set_rng_state(rng)
    initial=state_digest(model.state_dict())
    tokenizer=ROOT/p['tokenizerPath']; assert sha(tokenizer)==p['tokenizerSha256']
    pieces=[bytes.fromhex(x) for x in read(tokenizer)['bytes']]
    tf=[]; gen=[]
    selected=set(plan['generationCaseIds'])
    a.output.mkdir(parents=True)
    for c in p['cases']:
        for cond in ['correct','mismatched']:
            d=c['conditions'][cond]; prefix=d['prefixTokens'];gold=c['goldTokens']
            assert prefix[0]==1 and len(prefix)<=64 and len(prefix)+192<=256
            assert b''.join(pieces[t] for t in prefix[1:])==d['prefixText'].encode()
            assert b''.join(pieces[t] for t in gold)==c['targetText'].encode()
            logits,scores=teacher_forced(model,prefix,gold)
            meta={'id':c['id'],'group':c['group'],'endpoint':a.endpoint,'condition':cond}
            tf.append({**meta,**scores,'aggregate':aggregate(scores['tokens'])})
            if c['id'] in selected:
                g=greedy(model,prefix,gold,logits,pieces,max_new=192)
                g['generatedHistoryProbe']=generated_history_probe(model,prefix,gold,g,scores['tokens'])
                g['repeated4gram']=repeated_ngram_onset(g['nonEosTokens'],4)
                gen.append({**meta,'prefixText':d['prefixText'],'targetText':c['targetText'],**g})
    assert initial==state_digest(model.state_dict()) and torch.equal(rng,torch.get_rng_state())
    write(a.output/'tf.json',tf);write(a.output/'generations.json',gen)
    write(a.output/'receipt.json',{'endpoint':a.endpoint,'checkpointSha256':sha(checkpoint),'modelDigest':initial,
        'panelSha256':a.panel_sha256,'planSha256':a.plan_sha256,'inferenceOptimizerUpdates':0,
        'tfRows':len(tf),'fullGenerations':len(gen),'modelAndTorchRngUnchanged':True,
        'torch':torch.__version__,'threads':1,'dtype':'float32','device':'cpu','newTestAccess':False,
        'scope':'Python raw FP32 only; no new JavaScript equivalence claim'})
    print(json.dumps(read(a.output/'receipt.json')))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--panel',type=pathlib.Path,required=True);ap.add_argument('--panel-sha256',required=True)
    ap.add_argument('--plan',type=pathlib.Path,required=True);ap.add_argument('--plan-sha256',required=True)
    ap.add_argument('--endpoint',choices=['baseline','A','B'],required=True);ap.add_argument('--checkpoint',type=pathlib.Path)
    ap.add_argument('--output',type=pathlib.Path,required=True);run(ap.parse_args())
