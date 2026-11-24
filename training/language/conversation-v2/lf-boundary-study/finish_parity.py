"""Finish cached valid Python probe after sparse-checkout JS dependency repair; no Py forward replay."""
from lf_runtime import *
import subprocess
folder=P/'parity-terminal/LF1-579';assert not(folder/'receipt.json').exists()
(folder/'node.log').rename(folder/'node-initial-launch-failure.log')
proc=subprocess.run(['node',str(V/'parity.mjs'),str(folder/'request.json'),str(folder/'javascript.json')],capture_output=True,text=True);(folder/'node.log').write_text(proc.stdout+proc.stderr);assert proc.returncode==0
py=read(folder/'python.json');js=read(folder/'javascript.json');metadata=read(folder/'weights-metadata.json');binary=folder/'weights.f32';assert js['rawBinaryExactVerified'] and js['binarySha256']==sha(binary)==metadata['binarySha256']
rows=[];departures=0
for p,j in zip(py,js['rows'],strict=True):
 departures+=p['generation']['tokensIncludingEos']!=j['independentAutoregression']['tokensIncludingEos']
 for a,b in zip(p['generation']['steps'],j['referencePythonHistoryScores'],strict=True):
  assert a['inputTokens']==b['inputTokens'];error=max(abs(x-y) for x,y in zip(a['logits'],b['logits'],strict=True));rows.append(dict(id=p['id'],position=a['position'],max_logit_error=error,argmax_equal=a['argmax']==b['argmax']))
summary=dict(comparison_positions=len(rows),max_absolute_logit_error=max(r['max_logit_error'] for r in rows),tolerance=2e-4,tolerance_exceedances=sum(r['max_logit_error']>2e-4 for r in rows),same_history_argmax_disagreements=sum(not r['argmax_equal'] for r in rows),independent_short_generation_divergences=departures,optimizer_updates=0,Python_forwards=sum(len(x['generation']['steps']) for x in py),Python_forward_replays=0,JS_initial_failed_module_launch=1,JS_initial_failed_launch_logit_queries=0,complete_reply_parity_established=False,scope='Three prior exposed prefixes, up to four tokens, raw FP32; not long generation or all hardware')
write(folder/'receipt.json',dict(**summary,comparisons=rows,repair='Restored existing bpe_heap.mjs dependency in sparse scratch; cached Python logits and binary reused'));write(P/'parity-terminal-summary.json',summary);binary.unlink();print(json.dumps(summary))
