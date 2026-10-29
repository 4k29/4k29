"""Aggregate recorded probability trajectories without decoding or changing checkpoints."""
import pathlib,json,statistics,math
D=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def main():
 result={}
 for name in ['initialA','A-6459','B-6459']:
  r=read(D/'probabilities'/f'{name}.json');rows=r['cases'];bands={}
  for lo,hi in [(0,8),(8,32),(32,64),(64,128)]:
   tokens=[s for c in rows for s in c['steps']if lo<=s['position0']<hi];p={k:statistics.mean(s[k]for s in tokens)for k in ['p_EOS','p_previous16','p_whitespace','p_newline','p_digits']}if tokens else{}
   bands[f'{lo}:{hi}']=dict(actual_surviving_generated_positions=len(tokens),cases_reaching_band=sum(len(c['steps'])>lo for c in rows),mean_probabilities=p)
  first=[c['repeated4gram']['completion']for c in rows if c['repeated4gram']];paired={}
  for lo,hi in [(0,8),(8,32),(32,64),(64,128)]:
   tokens=[s for c in rows for s in c['steps']if lo<=s['position0']<hi and'gold'in s]
   paired[f'{lo}:{hi}']=dict(paired_positions=len(tokens),gold_NLL_correct=statistics.mean(-math.log(max(s['p_gold_correct'],1e-40))for s in tokens)if tokens else None,gold_NLL_self=statistics.mean(-math.log(max(s['p_gold_self'],1e-40))for s in tokens)if tokens else None)
  result[name]=dict(trajectory_bands=bands,paired_gold_bands=paired,mechanical_repeat_completion_position0_median=statistics.median(first)if first else None,repeated_cases=len(first),case_count=len(rows),endpoint_summary=r['summary']['endpoint_summary'])
 out=dict(models=result,optimizer_updates=0,scope='All main45 saved trajectories, unlike old24-only first8 summary. Conditional on surviving actual EOS; later bands/cross-model means are censored, not matched full-population causal effects. p_previous16 is mass on distinct token IDs in last16 generated tokens, not semantic repetition. Mechanical4gram completion is not semantic failure onset. Gold alternative continuations need not be unique. Context-only differences do not prove understanding.')
 (D/'FAILURE_ANALYSIS.json').write_text(json.dumps(out,indent=2)+'\n');print('Aggregated existing raw trajectories; zero new inference or updates')
if __name__=='__main__':main()
