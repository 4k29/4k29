"""Recover the interrupted fixed-mean arm from its complete step-200 state."""
from decay import ROOT,old,lr,restore,archive,read,save,update,evaluate,validate
import math

validate()
initial={n:p.detach().clone() for n,p in lr.previous.initial('initial').named_parameters()}
model,optimizer,state=restore(ROOT/'artifacts/C-200')
prior=read(ROOT/'C-ledger.json')
assert state['history']==old[:150]+prior[:50] and len(prior)==100
ledger=prior[:50]
for k in range(201,301):
    row=update(model,optimizer,'C',k,initial,observe=True)
    row['path_from_150']=math.fsum(x['delta'] for x in ledger)+row['delta']
    if k<=250:assert row==prior[k-151]
    ledger.append(row)
save(ROOT/'C-ledger.json',ledger)
archive(model,optimizer,300,old[:150]+ledger,ROOT/'artifacts/C-300')
evaluate(model,'C',300,initial)
save(ROOT/'C-receipt.json',dict(retained=150,witness_calls=2,confirmed_reconstruction_calls=50,
     confirmed_total_calls=202,interrupted_unlogged_calls='unknown, 0–50 after the last durable ledger'))
