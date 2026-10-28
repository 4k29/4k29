"""Reuse the existing raw-FP32 JS decoder; short fixed probes, no production edits."""
import copy, hashlib, importlib.util, json, pathlib, subprocess, sys
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from runtime import snapshot,initial
def load(name):return initial()if name=='initial'else snapshot(name)
from core import restore, digest
from parity import emit_binary, py_greedy
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def main():
    torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
    cases=json.loads((H/'prose-dev.json').read_text())['cases'][:3]
    protocol=dict(case_ids=[c['id']for c in cases],max_new_tokens=4,tolerance=2e-4,
      checkpoints=['foundation-lr','qa-only','qa-rehearsal'],
      scope='Post-training engineering check fixed before parity outputs; first three fixed prose prefixes, including BOS-free original fragments; at most four tokens. Not complete replies, native benchmarks, every hardware or new UI parity.',
      code_sha256={str(p.relative_to(H.parents[3])):sha(p)for p in [V/'parity.py',V/'parity.mjs',V.parent.parent/'dialogue/inference.mjs']})
    write(H/'PARITY_ADDITIONAL_PROTOCOL.json',protocol)
    summary={};settings=json.loads((V/'PLAN.json').read_text())['training']
    for name in protocol['checkpoints']:
        folder=H/'parity-additional'/name
        if folder.exists():raise RuntimeError('Never overwrite previous parity results')
        folder.mkdir(parents=True)
        state=load(name)['trajectory'];model,_,_=restore(copy.deepcopy(state),settings);model.eval();before=digest(model.state_dict());rng=torch.get_rng_state().clone()
        binary=folder/'weights.f32';specs,count=emit_binary(state['model'],binary)
        tok=json.loads((V/'data/tokenizer.json').read_text());metadata=folder/'weights-metadata.json'
        write(metadata,dict(binaryPath=str(binary),bytes=count*4,binarySha256=sha(binary),tensors=specs,config=state['config'],tokenizer=tok,checkpointSha256=json.loads(((V/'epoch1/medium/archive/checkpoint.pt.chunks.json')if name=='initial'else(H/'run'/name/'archive/checkpoint.json')).read_text())['sha256']))
        py=[];req=[]
        with torch.inference_mode():
            for c in cases:
                assert len(c['prefix'])+4<=256
                g=py_greedy(model,c['prefix'],4);py.append(dict(id=c['id'],generation=g))
                req.append(dict(id=c['id'],prefixTokens=c['prefix'],pythonHistoryInputs=[r['inputTokens']for r in g['steps']]))
        write(folder/'python.json',py);write(folder/'request.json',dict(metadataPath=str(metadata),expectedRunnerSha256=sha(V/'parity.mjs'),maxNewTokens=4,cases=req))
        proc=subprocess.run(['node',str(V/'parity.mjs'),str(folder/'request.json'),str(folder/'javascript.json')],capture_output=True,text=True)
        (folder/'node.log').write_text(proc.stdout+proc.stderr);assert proc.returncode==0
        js=json.loads((folder/'javascript.json').read_text());assert js['rawBinaryExactVerified']and js['binarySha256']==sha(binary)
        rows=[];departures=0
        for p,j in zip(py,js['rows'],strict=True):
            self_tokens=j['independentAutoregression']['tokensIncludingEos'];departures+=p['generation']['tokensIncludingEos']!=self_tokens
            for a,b in zip(p['generation']['steps'],j['referencePythonHistoryScores'],strict=True):
                assert a['inputTokens']==b['inputTokens'];error=max(abs(x-y)for x,y in zip(a['logits'],b['logits'],strict=True))
                rows.append(dict(id=p['id'],position=a['position'],maximum_absolute_logit_error=error,argmax_equal=a['argmax']==b['argmax'],python_gap=a['topTwoLogitGap'],javascript_gap=b['topTwoLogitGap']))
        assert before==digest(model.state_dict())and torch.equal(rng,torch.get_rng_state())
        summary[name]=dict(comparison_positions=len(rows),max_absolute_logit_error=max(r['maximum_absolute_logit_error']for r in rows),tolerance=2e-4,tolerance_exceedances=sum(r['maximum_absolute_logit_error']>2e-4 for r in rows),same_history_argmax_disagreements=sum(not r['argmax_equal']for r in rows),independent_short_generation_divergences=departures,optimizer_updates=0,complete_reply_parity_established=False)
        write(folder/'receipt.json',dict(**summary[name],comparisons=rows));binary.unlink();write(H/'parity-additional-summary.json',summary);print(name,summary[name],flush=True)
if __name__=='__main__':main()
