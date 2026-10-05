"""Held raw document likelihood and unrestricted continuations; no QA prompt.
Test cannot select weights/vocabulary. Greedy full vocabulary, no repair/filter.
"""
import argparse,gzip,hashlib,json,pathlib,time
import torch
from model import Decoder
from train import read,write,load_partition,measure
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'dialogue'))
from tokenizer import SPECIALS,encode_stream,decode
ROOT=pathlib.Path(__file__).resolve().parent

def load_model(path):
    source=gzip.decompress(path.read_bytes()).decode() if path.suffix=='.gz' else path.read_text()
    export=json.loads(source.split('export const dialogueModel=',1)[1].strip().removesuffix(';'))
    config={k:v for k,v in export['config'].items() if k!='semanticTasks'};model=Decoder(config)
    model.load_state_dict({k:torch.tensor(t['data']).reshape(t['shape']) for k,t in export['tensors'].items() if not k.startswith('semantic.')});model.eval();return model,export
@torch.no_grad()
def generate(model,opening,tokenizer,max_new=128):
    input=[SPECIALS['bos']]+encode_stream(opening,tokenizer);tokens=[];eos=False
    if len(input)>=model.config['context']:raise ValueError('Opening exceeds context')
    for _ in range(min(max_new,model.config['context']-len(input))):
        t=int(model(torch.tensor([input+tokens]))[0,-1].argmax())
        if t==SPECIALS['eos']:eos=True;break
        tokens.append(t)
    bytes_out=b''.join(bytes.fromhex(tokenizer['bytes'][t]) for t in tokens)
    try:bytes_out.decode('utf8');valid_utf8=True
    except UnicodeDecodeError:valid_utf8=False
    return dict(text=decode(tokens,tokenizer),tokens=tokens,eos=eos,validUtf8=valid_utf8,validTokens=valid_utf8 and all(t>=6 for t in tokens),inputTokens=len(input))
def repetition(text):
    # Diagnostic only. No decoding penalty/output changes; manual review remains primary.
    repeated=[]
    for width in range(2,97):
        for start in range(max(0,len(text)-width*3+1)):
            piece=text[start:start+width]
            if text[start:start+width*3]==piece*3:
                repeated.append(dict(start=start,width=width,piece=piece));break
    return repeated

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--model',type=pathlib.Path,required=True);parser.add_argument('--partition',choices=['validation','test'],required=True);parser.add_argument('--out',type=pathlib.Path,required=True);parser.add_argument('--likelihood',action='store_true');parser.add_argument('--reference',action='store_true');parser.add_argument('--threads',type=int,default=1);args=parser.parse_args()
    if args.threads<1:parser.error('threads must be positive')
    torch.set_num_threads(args.threads);model,export=load_model(args.model);policy=read(ROOT/'generation-policy.json');begun=time.monotonic()
    report=dict(modelVersion=export['version'],modelFileSha256=hashlib.sha256(args.model.read_bytes()).hexdigest(),config=export['config'],training=export['training'],partition=args.partition,evaluationThreads=args.threads,policySha256=hashlib.sha256((ROOT/'generation-policy.json').read_bytes()).hexdigest(),rows=[])
    if args.likelihood:
        merges=len(export['tokenizer']['merges']);kind='paragraph-bpe' if export['training'].get('paragraphSelectionsSha256') else 'bpe';directory=ROOT/f'{kind}-{merges}'
        if export['tokenizer']!=read(directory/'tokenizer.json'):raise ValueError('Tokenizer mismatch')
        info,values=load_partition(directory,args.partition);report['likelihood']=measure(model,info,values);report['likelihoodUnit']=info.get('unit','Whole source document, continuous masked-overlap windows');report['likelihoodDataDirectory']=directory.name
    for row in policy['probes'][args.partition]:
        t=time.monotonic();result=generate(model,row['prefix'],export['tokenizer'],policy['generation']['maxNewTokens'])
        joined=row['prefix']+result['text'];first_stop=result['text'].find('。')
        report['rows'].append(dict(**row,**result,joined=joined,observedFirstSentence=joined[:len(row['prefix'])+first_stop+1] if first_stop>=0 else None,repetitionDiagnostics=repetition(result['text']),elapsedSeconds=round(time.monotonic()-t,4)))
        print(json.dumps(dict(id=row['id'],prefix=row['prefix'],text=result['text'],eos=result['eos'],validTokens=result['validTokens']),ensure_ascii=False),flush=True)
    report['elapsedSeconds']=round(time.monotonic()-begun,3)
    if args.reference:
        report['references']=[]
        for row in report['rows'][:4]:
            tokens=[SPECIALS['bos']]+encode_stream(row['prefix'],export['tokenizer']);logits=model(torch.tensor([tokens]))[0,-1].detach()
            report['references'].append(dict(id=row['id'],tokens=tokens,logits=logits.tolist()))
    write(args.out,report)
if __name__=='__main__':main()
