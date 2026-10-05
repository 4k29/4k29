import {neuralModel as model} from './neural-model.js?v=20261005-topic-language-1';

// GPT-style decoder inference: learned embeddings, causal multi-head attention,
// residual connections, pre-layer normalization, GELU MLP and a tied softmax head.
// Incremental K/V states are immutable and bounded by a small LRU cache.
const parameters=Object.fromEntries(Object.entries(model.tensors).map(([name,tensor])=>[name,{shape:tensor.shape,data:Float32Array.from(tensor.data)}]));
const cache=new Map(),limit=512,D=model.config.dim,heads=model.config.heads,headDim=D/heads;
function parameter(name){const p=parameters[name];if(!p)throw Error('Missing neural parameter '+name);return p;}
function linear(input,name){
 const weight=parameter(name+'.weight'),bias=parameter(name+'.bias').data,out=new Float32Array(weight.shape[0]),width=weight.shape[1];
 for(let i=0;i<out.length;i++){let sum=bias[i];for(let j=0;j<width;j++)sum+=weight.data[i*width+j]*input[j];out[i]=sum;}
 return out;
}
function norm(input,name){
 const weight=parameter(name+'.weight').data,bias=parameter(name+'.bias').data,out=new Float32Array(D);
 let mean=0,variance=0;for(const value of input)mean+=value/D;for(const value of input)variance+=(value-mean)**2/D;
 const scale=1/Math.sqrt(variance+model.config.epsilon);
 for(let i=0;i<D;i++)out[i]=(input[i]-mean)*scale*weight[i]+bias[i];return out;
}
function softmax(logits){
 const out=new Float32Array(logits.length),max=Math.max(...logits);let sum=0;
 for(let i=0;i<out.length;i++){out[i]=Math.exp(logits[i]-max);sum+=out[i];}
 for(let i=0;i<out.length;i++)out[i]/=sum;return out;
}
function emptyState(){return {length:0,keys:Array.from({length:model.config.layers},()=>[]),values:Array.from({length:model.config.layers},()=>[])};}
function advance(state,token){
 if(state.length>=model.config.context)throw Error('Neural context exceeded');
 if(!Number.isInteger(token)||token<0||token>=model.vocabulary.length)throw Error('Invalid neural token');
 const embedding=parameter('token.weight').data,position=parameter('position.weight').data;
 let x=new Float32Array(D);for(let i=0;i<D;i++)x[i]=embedding[token*D+i]+position[state.length*D+i];
 const keys=[],values=[];
 for(let layer=0;layer<model.config.layers;layer++){
  const name='blocks.'+layer,qkv=linear(norm(x,name+'.ln1'),name+'.qkv'),query=qkv.slice(0,D),key=qkv.slice(D,2*D),value=qkv.slice(2*D);
  keys[layer]=[...state.keys[layer],key];values[layer]=[...state.values[layer],value];
  const attention=new Float32Array(D);
  for(let head=0;head<heads;head++){
   const scores=new Float32Array(state.length+1),offset=head*headDim;
   for(let step=0;step<scores.length;step++){let score=0;for(let i=0;i<headDim;i++)score+=query[offset+i]*keys[layer][step][offset+i];scores[step]=score/Math.sqrt(headDim);}
   const probabilities=softmax(scores);
   for(let i=0;i<headDim;i++){let sum=0;for(let step=0;step<scores.length;step++)sum+=probabilities[step]*values[layer][step][offset+i];attention[offset+i]=sum;}
  }
  const projected=linear(attention,name+'.proj');for(let i=0;i<D;i++)x[i]+=projected[i];
  const hidden=linear(norm(x,name+'.ln2'),name+'.fc1');
  for(let i=0;i<hidden.length;i++){const v=hidden[i];hidden[i]=.5*v*(1+Math.tanh(Math.sqrt(2/Math.PI)*(v+.044715*v**3)));}
  const mlp=linear(hidden,name+'.fc2');for(let i=0;i<D;i++)x[i]+=mlp[i];
 }
 return {length:state.length+1,keys,values,hidden:norm(x,'norm')};
}
function put(key,state){cache.set(key,state);while(cache.size>limit)cache.delete(cache.keys().next().value);return state;}
function stateFor(context,history){
 const id=context.language+':'+context.kind+':'+(context.style||'polite')+':'+(context.specification??''),key=id+'|'+history.join(',');
 if(cache.has(key)){const state=cache.get(key);cache.delete(key);cache.set(key,state);return state;}
 if(history.length)return put(key,advance(stateFor(context,history.slice(0,-1)),history.at(-1)));
 const controls=[0,model.controls.language[context.language],model.controls.kind[context.kind],model.controls.style[context.style||'polite']];
 if(context.specification!==undefined)controls.push(context.specification);
 let state=emptyState();for(const token of controls)state=advance(state,token);return put(key,state);
}
export function neuralLogits(context,history=[]){
 const state=stateFor(context,history.slice(-(model.config.context-(context.specification===undefined?4:5))));
 if(!state.logits){
  const weight=parameter('token.weight').data,logits=new Float32Array(model.vocabulary.length);
  for(let token=0;token<logits.length;token++){let value=0;for(let i=0;i<D;i++)value+=weight[token*D+i]*state.hidden[i];logits[token]=value;}
  state.logits=logits;
 }
 return state.logits;
}
export function neuralDistribution(context,history=[]){
 const trimmed=history.slice(-(model.config.context-(context.specification===undefined?4:5))),state=stateFor(context,trimmed);
 if(!state.probabilities)state.probabilities=softmax(neuralLogits(context,trimmed));return state.probabilities;
}
export function predictNeuralNextTokens(context,history,allowed){
 const probabilities=neuralDistribution(context,history),sum=allowed.reduce((s,id)=>s+probabilities[id],0);
 return allowed.map(token=>({token,probability:probabilities[token],constrainedProbability:probabilities[token]/(sum||1)})).sort((a,b)=>b.probability-a.probability||a.token-b.token);
}
export function neuralSequenceLikelihood(context,tokens){
 let logProbability=0;const history=[];
 for(const token of [...tokens,1]){logProbability+=Math.log(Math.max(1e-30,neuralDistribution(context,history)[token]));history.push(token);}
 return {logProbability,meanLogProbability:logProbability/(tokens.length+1),tokens:tokens.length+1};
}
export const neuralVersion=model.version;
export const neuralArchitecture='causal-transformer';
export function clearNeuralCache(){cache.clear();}
export function neuralCacheInfo(){return {size:cache.size,limit};}
