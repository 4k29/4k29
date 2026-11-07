"""Check actual saved before/after inputs and generation budgets, not just names of panels."""
import pathlib,json,hashlib
D=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 labels=['initialA','A-6459','B-6459'];counts={};refs={}
 for folder in ['evaluation','panels','daily-prose']:
  sets=[]
  for label in labels:
   p=D/folder/f'{label}.json';refs[f'{folder}/{label}']=sha(p);r=read(p)
   sets.append(r['cases']if folder!='panels'else r['legacy']+r['grounded36']+r['context12'])
  assert len({len(s)for s in sets})==1
  for aligned in zip(*sets):
   base=aligned[0]
   for c in aligned[1:]:
    assert c['prefix']==base['prefix']and c['maxNewTokens']==base['maxNewTokens']
    if'id'in c and'id'in base:assert c['id']==base['id']
  counts[folder]=len(sets[0])
 # Subsequent self-history tokens must differ between models and are not pairwise forced.
 for i in range(4):
  a=[read(D/'panels'/f'{label}.json')['self_history'][i]for label in labels]
  assert a[0]['prefix']==a[1]['prefix']==a[2]['prefix']
 result=dict(exact_saved_prefix_and_budget_match=True,models=labels,case_counts=counts,initial_self_history_episode_prompts_equal=4,later_self_history='actual own generated tokens; intentionally not teacher-forced to match another model',artifact_sha256=refs,optimizer_updates=0)
 (D/'PAIRING_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print('Actual saved prefixes/budgets match',counts)
if __name__=='__main__':main()
