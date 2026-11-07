import argparse
from eval_runtime import *
from prose_decode import greedy

def main():
 p=argparse.ArgumentParser();p.add_argument('--model',default='initial');a=p.parse_args();torch.set_num_threads(2);base=initial()if a.model=='initial'else snapshot(a.model);model,_,_=restore_isolated(base['trajectory']);model.eval();pieces=[bytes.fromhex(s)for s in json.loads((V/'data/tokenizer.json').read_text())['bytes']];cases=json.loads((N/'paragraph-dev.json').read_text())['cases'];rows=[]
 for c in cases:rows.append(dict(**c,**greedy(model,c['prefix'],pieces,max_new=128)))
 out=N/'evaluation';out.mkdir(exist_ok=True);path=out/(a.model+'-paragraphs.json');assert not path.exists();write(path,dict(model=a.model,cases=rows,scope='Existing three exposed DEV components, new paragraph task, not TEST or independent native-human evaluation',optimizer_updates=0));print(a.model,'paragraph DEV saved',flush=True)
if __name__=='__main__':main()
