"""Fixed TRAIN versus article-disjoint DEV response diagnostic, not adoption."""
import argparse,gzip,json
from runtime import H,V,torch,snapshot,restore_isolated,sha
from prose_decode import greedy
def main():
 p=argparse.ArgumentParser();p.add_argument('--model',required=True);a=p.parse_args();torch.set_num_threads(2);torch.use_deterministic_algorithms(True)
 data=json.loads((H/'qa-data.json').read_text());schedule=json.load(gzip.open(H/'response-schedule.json.gz','rt'));train=[r['id']for b in schedule[:4]for r in b['control']];btrain={r['id']for b in schedule for r in b['treatment'][:2]};cases=[dict(r,panel='TRAIN16',trained_in_rehearsal=r['id']in btrain)for r in data['train']if r['id']in train]+[dict(r,panel='DEV32')for r in data['dev'][:32]];assert len(cases)==48
 protocol=dict(case_ids=[r['id']for r in cases],max_new=64,decoding='greedy full vocabulary, original own decoder',scope='Fixed before response updates, after foundation outputs; TRAIN probes versus exposed article-disjoint DEV; no human independent TEST; exact substring is necessary candidate only',source_sha256=sha(H/'qa-data.json'))
 path=H/'RESPONSE_PROBE_PROTOCOL.json'
 if path.exists():assert json.loads(path.read_text())==protocol
 else:path.write_text(json.dumps(protocol,indent=2)+'\n')
 out=H/'evaluation'/(a.model+'-response-probe.json');assert not out.exists();model,_,_=restore_isolated(snapshot(a.model)['trajectory']);model.eval();pieces=[bytes.fromhex(x)for x in json.loads((V/'data/tokenizer.json').read_text())['bytes']];rows=[]
 with torch.no_grad():
  for r in cases:
   seq=r['sequence'];L=len(r['prefix']);logits=model(torch.tensor([seq[:-1]]))[0,L-1:];loss=torch.nn.functional.cross_entropy(logits,torch.tensor(r['answer_ids']),reduction='sum');g=greedy(model,r['prefix'],pieces,max_new=64);rows.append(dict(id=r['id'],panel=r['panel'],trained_in_rehearsal=r.get('trained_in_rehearsal',False),input=r['prompt'],prefix=r['prefix'],reference=r['answer'],reference_tokens=r['answer_ids'],reference_nll_sum=float(loss),necessary_string_candidate=r['answer']in g['text'],**g))
 out.write_text(json.dumps(dict(model=a.model,cases=rows,optimizer_updates=0,independent_native_human_evaluation=False),ensure_ascii=False,indent=2)+'\n');print(a.model,'response probe saved',flush=True)
if __name__=='__main__':main()
