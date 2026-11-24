"""Python/JS loss-mask arithmetic check; NOT whole-model numerical equivalence."""
import json,math,pathlib,subprocess,hashlib
P=pathlib.Path(__file__).resolve().parent
x=dict(logits=[[1.25,-.5,2.0],[3.0,.1,-2],[.2,.4,.6],[0.0,1.0,-1]],target=[2,0,1,0],full_mask=[1,1,1,0],reply_mask=[0,1,1,0])
def ce(mask):
 terms=[]
 for z,t,active in zip(x['logits'],x['target'],mask):
  a=max(z);lp=math.log(sum(math.exp(v-a)for v in z))+a;terms.append((lp-z[t])*active)
 return sum(terms)/sum(mask)
py=[ce(x['full_mask']),ce(x['reply_mask'])]
js='const x=JSON.parse(process.argv[1]);const ce=m=>x.logits.reduce((s,z,i)=>{let a=Math.max(...z);return s+m[i]*(Math.log(z.reduce((q,v)=>q+Math.exp(v-a),0))+a-z[x.target[i]])},0)/m.reduce((s,v)=>s+v,0);process.stdout.write(JSON.stringify([ce(x.full_mask),ce(x.reply_mask)]));'
b=subprocess.check_output(['node','-e',js,json.dumps(x)],text=True);other=json.loads(b);assert max(abs(a-b)for a,b in zip(py,other))<1e-12
r=dict(passed=True,scope='synthetic masked CE arithmetic only, no model forward or whole-model equivalence claim',python=py,javascript=other,max_abs_diff=max(abs(a-b)for a,b in zip(py,other)),mask_denominators=[3,2],input=x,actual_optimizer_calls=0,model_forwards=0)
(P/'NUMERICAL_CONTRACT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
