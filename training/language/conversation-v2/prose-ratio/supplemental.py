"""Resolve additional diagnostic traces for the unchanged PR #133 reference."""
from run import ROOT, PREV, evaluate, git_checkpoint, read, restore

if __name__=='__main__':
    model,_=restore('A',git_checkpoint(PREV/'artifacts/A-2950'))
    evaluate(model,[r for r in read(ROOT/'DEV.json') if r['panel']=='independent'],'A-2950-regression34')
