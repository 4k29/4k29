"""Evaluate completed raw runs; freeze selection before opening fresh TEST.

This does not train, correct outputs or judge fluency. Explicit manual review
and the optimizer/reproducibility audit are separate steps after generation.
"""
import argparse,json,pathlib,subprocess,sys,time
ROOT=pathlib.Path(__file__).resolve().parent
REPO=ROOT.parents[2]
def read(p):return json.loads(p.read_text())
def run(args):subprocess.run(args,cwd=REPO,check=True)
def evaluate(model,part,out,likelihood=False):
    args=[sys.executable,str(ROOT/'evaluate.py'),'--model',str(model),'--partition',part,'--out',str(out),'--reference']
    if likelihood:args.append('--likelihood')
    run(args)
def parity(model,generation,out):run(['node',str(ROOT.parent/'evaluate_js.mjs'),str(model),str(generation),str(out)])
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--wait',action='store_true');args=parser.parse_args()
    complete=ROOT/'prefix-million/result.json';last_print=0
    while not complete.exists():
        if not args.wait:raise RuntimeError('Child has not completed')
        if time.monotonic()-last_print>=50:
            metrics=read(ROOT/'prefix-million/metrics.json');print(json.dumps(dict(waitingForCompleteExport=True,lastValidatedUpdate=metrics['history'][-1]['step'])),flush=True);last_print=time.monotonic()
        time.sleep(10)
    result=read(complete);assert result['completedRun'] and result['completedSteps']==10000
    choice=ROOT/'checkpoint-choice.json'
    if not choice.exists():run([sys.executable,str(ROOT/'select_checkpoint.py')])
    selected=ROOT/read(choice)['chosenRun'];baseline=ROOT/'baseline';baseline.mkdir(exist_ok=True)
    child=ROOT/'prefix-million'
    evaluate(child/'model.js','validation',child/'validation.json')
    parity(child/'model.js',child/'validation.json',child/'validation-js.json')
    evaluate(selected/'model.js','test',selected/'test.json',likelihood=True)
    parity(selected/'model.js',selected/'test.json',selected/'test-js.json')
    old=ROOT.parent/'paragraph-million/model.js'
    evaluate(old,'test',baseline/'test.json')
    parity(old,baseline/'test.json',baseline/'test-js.json')
    print(json.dumps(dict(generationAndJsParityCompleted=True,selectedRun=selected.name,manualReviewStillRequired=True)),flush=True)
if __name__=='__main__':main()
