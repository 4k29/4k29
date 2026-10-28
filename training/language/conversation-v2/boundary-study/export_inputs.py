from common import *

def main():
 enc=Encoder(json.loads((V/'data/tokenizer.json').read_text()));rows=[]
 for panel,path in [('native24',V/'epoch1/content-dev.json'),('provided23',V/'response-data/final/active-dev.json')]:
  for c in json.loads(path.read_text())['cases']:
   pre=c['prefixTokens']if panel=='native24'else[1,3]+enc(c['prompt'])+[2,4];rows.append(dict(id=c['id'],panel=panel,prompt=c.get('prompt',c.get('inputText',c.get('prefixText',''))),prefix_tokens=pre,source_path=str(path.relative_to(N.parents[3])),source_sha256=sha(path)))
 d=json.loads((V/'grounded-objective/data.json').read_text());plan=json.loads((V/'grounded-objective/PLAN.json').read_text());selected=set(plan['evaluation']['dev_ids'])
 for c in d['dev']:
  if c['id']in selected:rows.append(dict(id=c['id'],panel='grounded36',prompt=c['prompt'],prefix_tokens=c['prefix']))
 write(N/'EVALUATION_INPUTS.json',dict(cases=rows,role_contract='Historical numeric humanA/B roles retained unchanged for old exposed diagnostic prompts; standalone prose has own paragraph boundaries',other_inputs='Primary exact prefixes in TOKEN_BOUNDARY_PROTOCOL and each case; self-history includes every actual prefix; human32 cases preserve exact prefix; no synthetic input attributed to human original'))
if __name__=='__main__':main()
