"""Exact legacy response inputs are unchanged; save them explicitly beside new prose inputs."""
from common import *
enc=Encoder(read(V/'data/tokenizer.json'));dp=read(V/'grounded-objective/data.json');by={r['id']:r for r in dp['dev']};oldplan=read(V/'grounded-objective/PLAN.json');native=read(V/'epoch1/content-dev.json')['cases'];provided=read(V/'response-data/final/active-dev.json')['cases'];panels={}
panels['grounded36']=[dict(id=i,prefix=by[i]['prefix'],prompt=by[i]['prompt'],program_teacher=by[i]['answer'],task=by[i]['task'])for i in oldplan['evaluation']['dev_ids']]
panels['native24']=native
panels['provided23']=[dict(id=r['id'],prompt=r['prompt'],prefix=[1,3]+enc(r['prompt'])+[2,4],source_case=r)for r in provided]
panels['context12']=read(V/'grounded-objective/CONTEXT_PROBE_PLAN.json')['cases']
write(P/'EVALUATION_INPUTS.json',dict(prose=read(P/'DEV_PROTOCOL.json'),legacy=panels,source_sha256={str(p.relative_to(ROOT)):sha(p)for p in [V/'grounded-objective/data.json',V/'grounded-objective/PLAN.json',V/'epoch1/content-dev.json',V/'response-data/final/active-dev.json',V/'grounded-objective/CONTEXT_PROBE_PLAN.json']},independent_TEST=False,independent_human_evaluation=False,semantic_roles='Legacy humanAB role IDs retained as exposed diagnostics; no claim of newly trained assistant-role contract'))
print('Exact old response inputs and new prose inputs saved')
