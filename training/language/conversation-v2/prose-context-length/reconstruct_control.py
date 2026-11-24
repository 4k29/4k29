"""Recover only the missing archived-control observation points."""
import json
from train import prior, ROOT, OLD, read, save, torch

def main():
    initial={n:p.detach().clone() for n,p in prior.lr.previous.initial('initial').named_parameters()}
    m,o,_=prior.start(prior.parent)
    ledger=read(OLD/'LEDGER.json')
    folder=ROOT/'control'
    folder.mkdir(exist_ok=False)
    prior.ROOT=folder
    for k in range(301,501):
        row=prior.update(m,o,k,initial,'control_reconstruction')
        assert row==ledger[k-301],k
        if k in (400,500):
            rng=torch.get_rng_state().clone()
            prior.generate(m,k)
            assert torch.equal(rng,torch.get_rng_state())
            print(k,flush=True)
    save(folder/'RECONSTRUCTION.json',dict(matches=list(range(301,501)),optimizer_calls=200,
        archived_primary_terminal=True,source_ledger=prior.decay.sha(OLD/'LEDGER.json')))

if __name__=='__main__':
    main()
