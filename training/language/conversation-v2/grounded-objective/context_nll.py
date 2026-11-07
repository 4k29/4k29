"""Post-hoc fixed-weight context ablation on supplemental programmatic DEV only."""
import copy, json, pathlib, sys
H=pathlib.Path(__file__).resolve().parent;V=H.parent;sys.path.insert(0,str(V))
import torch
from checkpoint_io import load
from core import restore
from new_tokenizer import Encoder

def main():
    torch.set_num_threads(2)
    cases=json.loads((H/'CONTEXT_PROBE_PLAN.json').read_text())['cases']
    enc=Encoder(json.loads((V/'data/tokenizer.json').read_text()))
    settings=json.loads((V/'PLAN.json').read_text())['training']
    protocol=dict(scope='post-hoc supplemental DEV, not preregistered primary or TEST; no updates',
      target='same correct answer body+EOS for all three contexts',
      conditions=['correct supplied assumption','opposite assumption from same entity/slot pair','question alone'],
      length_limitations='same gold token count; free/absent prefix token lengths differ, no padding/cropping to conceal positional confound')
    (H/'CONTEXT_NLL_PROTOCOL.json').write_text(json.dumps(protocol,indent=2)+'\n')
    summary={}
    for name in ['full-512','response-512','full-extra','response-extra']:
        model,_,_=restore(copy.deepcopy(load(name)['trajectory']),settings);model.eval();rows=[]
        with torch.no_grad():
            for i,c in enumerate(cases):
                label='駐車場'if c['slot']=='parking'else'Wi-Fi'
                answer=label+('は無料で利用できます。'if c['free']else'はありません。')
                target=enc(answer)+[2]
                prompts={'correct':c['prompt'],'opposite':cases[i^1]['prompt'],'removed':'質問：'+c['prompt'].split('質問：')[-1]}
                losses={};lengths={};per_token={}
                for condition,prompt in prompts.items():
                    prefix=[1,3]+enc(prompt)+[2,4];seq=prefix+target
                    logits=model(torch.tensor([seq[:-1]]))[0,len(prefix)-1:]
                    loss=torch.nn.functional.cross_entropy(logits,torch.tensor(target),reduction='none')
                    losses[condition]=float(loss.mean());per_token[condition]=loss.tolist();lengths[condition]=len(prefix)
                rows.append(dict(case_index=i,answer=answer,target_ids=target,prefix_lengths=lengths,nll=losses,per_token_nll=per_token,
                    correct_advantage_over_opposite=losses['opposite']-losses['correct']))
        summary[name]=dict(cases=len(rows),correct_better_than_opposite=sum(r['correct_advantage_over_opposite']>0 for r in rows),
           mean_correct_advantage=sum(r['correct_advantage_over_opposite']for r in rows)/len(rows),
           mean_nll={c:sum(r['nll'][c]for r in rows)/len(rows)for c in ['correct','opposite','removed']})
        (H/'evaluation-extra'/(name+'-context-nll.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    (H/'evaluation-extra/context-nll-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
