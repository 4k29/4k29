"""Recover the high-rate 200-update state and run the fixed diagnostics."""
from run import ROOT,SOURCE,broad,previous,engine,read,save,update

def diagnose(model):
    old=engine.batch_for
    try:
        engine.batch_for=lambda *_:broad.diagnostic_batch
        return engine.diagnosis(model)
    finally:
        engine.batch_for=old

model,opt,_=previous.restore(SOURCE/'artifacts/C-100')
ledger=read(SOURCE/'C-ledger.json')
for k in range(101,201):
    row=update(model,opt,k)
    assert all(row[key]==value for key,value in ledger[k-1].items())
save(ROOT/'A-200-grad.json',diagnose(model))
model,_,_=previous.restore(ROOT/'artifacts/B-200')
save(ROOT/'B-200-grad.json',diagnose(model))
save(ROOT/'MIDPOINT_RECEIPT.json',dict(A_reconstruction_calls=100,B_reconstruction_calls=0,diagnostic_optimizer_calls=0))
