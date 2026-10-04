"""Compare steady and distilled 10,000-update models; export a qualifying checkpoint."""
import argparse
import os
import pathlib
import subprocess
import tempfile

root = pathlib.Path(__file__).resolve().parent.parent
parser = argparse.ArgumentParser()
parser.add_argument('--corpus', default='/tmp/4k29-transformer-corpus.json')
parser.add_argument('--directory')
parser.add_argument('--steps', type=int, default=10000)
parser.add_argument('--minimum-steps', type=int, default=10000)
args = parser.parse_args()
folder = pathlib.Path(args.directory or tempfile.mkdtemp(prefix='4k29-neural-'))
folder.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2')
for name,learning_rate in [('steadyA',0.0003),('steadyB',0.00015),('steadyC',0.00002)]:
    extra=['--initialize-model',str(root/'training/transformer-teacher.js'),'--distill','2.0'] if name=='steadyC' else []
    subprocess.run([os.sys.executable,str(root/'training/train-transformer.py'),'--corpus',args.corpus,'--steps',str(args.steps),'--minimum-steps',str(args.minimum_steps),'--seed','2941','--dropout','0.12','--learning-rate',str(learning_rate),'--warmup','1000','--output',str(folder/(name+'.js')),'--artifacts-prefix',str(folder/name),*extra],env=env,check=True)
subprocess.run(['node',str(root/'training/select-transformer.mjs'),str(folder),'steadyA','steadyB','steadyC','--minimum-updates='+str(args.minimum_steps)],check=True)
