"""Measure a comma typography control with unchanged next-token labels."""
import sys
from probe import ROOT, BASE, OLD, read, write

sys.path[:0] = [str(OLD),str(BASE)]
from run_budget import start, parent, torch
from new_tokenizer import Encoder

def main():
    tokenizer = read(BASE/'data/tokenizer.json')
    pieces = list(map(bytes.fromhex,tokenizer['bytes']))
    encode = Encoder(tokenizer)
    model,_,_ = start(parent)
    model.eval()
    cases=[]
    calls=0
    with torch.inference_mode():
        for site in read(ROOT/'SITES.json'):
            original=site['prefix']+site['replaced']
            left=b''.join(pieces[t] for t in site['prefix']).decode()
            suffix=b''.join(pieces[t] for t in site['replaced']).decode()
            reference=site['reference']
            new_text=left[:-1]+{'、':'，','，':'、'}[left[-1]]+suffix
            new=encode(new_text)
            full=encode(new_text+b''.join(pieces[t] for t in reference).decode())
            if full!=new+reference or len(full)>256:
                cases.append(dict(id=site['id'],status='excluded_boundary_or_context'))
                continue
            after=reference[:32]
            losses=[]
            for prefix in (original,new):
                logits=model(torch.tensor([(prefix+after)[:-1]]))[0,len(prefix)-1:].double()
                calls+=1
                logits=logits.log_softmax(-1)
                losses.append([-float(logits[j,t]) for j,t in enumerate(after)])
            cases.append(dict(id=site['id'],status='scored',variant=new_text,
                prefix_original=original,prefix_variant=new,gold=after,nll_original=losses[0],nll_variant=losses[1]))
    write('TYPOGRAPHY.json',dict(checkpoint=300,forwards=calls,optimizer_calls=0,cases=cases))

if __name__=='__main__':
    main()
