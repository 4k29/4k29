// Standalone own Transformer inference. Questions and answers are token sequences;
// no profile, answer catalogue, grammar paths, or external API is read here.
import {createTokenizer} from './tokenizer.mjs';
import {beamSearch} from './beam_search.mjs';
export function createDialogueDecoder(model,{cachePrefixes=false,tokenizerAlgorithm='rank-loop'}={}){
 const tokenizer=createTokenizer(model.tokenizer,{algorithm:tokenizerAlgorithm}),D=model.config.dim,heads=model.config.heads,headDim=D/heads;
 const tensors=Object.fromEntries(Object.entries(model.tensors).map(([name,t])=>[name,{shape:t.shape,data:Float32Array.from(t.data)}]));
 const p=name=>{if(!tensors[name])throw Error('Missing tensor '+name);return tensors[name];};
 function linear(input,name){const w=p(name+'.weight'),b=p(name+'.bias').data,out=new Float32Array(w.shape[0]);for(let i=0;i<out.length;i++){let value=b[i];for(let j=0;j<input.length;j++)value+=w.data[i*input.length+j]*input[j];out[i]=value;}return out;}
 function norm(input,name){const w=p(name+'.weight').data,b=p(name+'.bias').data,out=new Float32Array(D);let mean=0,variance=0;for(const v of input)mean+=v/D;for(const v of input)variance+=(v-mean)**2/D;const scale=1/Math.sqrt(variance+model.config.epsilon);for(let i=0;i<D;i++)out[i]=(input[i]-mean)*scale*w[i]+b[i];return out;}
 function softmax(input){const out=new Float32Array(input.length),max=Math.max(...input);let sum=0;for(let i=0;i<input.length;i++)sum+=(out[i]=Math.exp(input[i]-max));for(let i=0;i<out.length;i++)out[i]/=sum;return out;}
 const empty=()=>({length:0,keys:Array.from({length:model.config.layers},()=>[]),values:Array.from({length:model.config.layers},()=>[]),hidden:null});
 function advance(state,token){
  if(state.length>=model.config.context)throw RangeError('Context exhausted; never truncate a question');
  if(!Number.isInteger(token)||token<0||token>=model.config.vocabulary)throw RangeError('Invalid token');
  const embedding=p('token.weight').data,position=p('position.weight').data;let x=new Float32Array(D);
  for(let i=0;i<D;i++)x[i]=embedding[token*D+i]+position[state.length*D+i];
  const keys=[],values=[];
  for(let layer=0;layer<model.config.layers;layer++){
   const name='blocks.'+layer,qkv=linear(norm(x,name+'.ln1'),name+'.qkv'),query=qkv.slice(0,D),key=qkv.slice(D,2*D),value=qkv.slice(2*D);
   keys[layer]=state.keys[layer].concat([key]);values[layer]=state.values[layer].concat([value]);const attention=new Float32Array(D);
   for(let head=0;head<heads;head++){
    const scores=new Float32Array(state.length+1),offset=head*headDim;
    for(let time=0;time<scores.length;time++){let sum=0;for(let i=0;i<headDim;i++)sum+=query[offset+i]*keys[layer][time][offset+i];scores[time]=sum/Math.sqrt(headDim);}
    const probabilities=softmax(scores);for(let i=0;i<headDim;i++){let sum=0;for(let time=0;time<scores.length;time++)sum+=probabilities[time]*values[layer][time][offset+i];attention[offset+i]=sum;}
   }
   const projected=linear(attention,name+'.proj');for(let i=0;i<D;i++)x[i]+=projected[i];const hidden=linear(norm(x,name+'.ln2'),name+'.fc1');
   for(let i=0;i<hidden.length;i++){const v=hidden[i];hidden[i]=0.5*v*(1+Math.tanh(Math.sqrt(2/Math.PI)*(v+0.044715*v**3)));}
   const mlp=linear(hidden,name+'.fc2');for(let i=0;i<D;i++)x[i]+=mlp[i];
  }
  return {length:state.length+1,keys,values,hidden:norm(x,'norm')};
 }
 function logits(state){const embedding=p('token.weight').data,out=new Float32Array(model.config.vocabulary);for(let token=0;token<out.length;token++){let sum=0;for(let i=0;i<D;i++)sum+=embedding[token*D+i]*state.hidden[i];out[token]=sum;}return out;}
 let cachedTokens=[],cachedStates=[empty()],lastPrefixReused=0;
 function clearCache(){cachedTokens=[];cachedStates=[empty()];lastPrefixReused=0;}
 function prefix(tokens){
  if(tokens.length>model.config.context)throw RangeError('Context exhausted; never truncate a question');
  for(const token of tokens)if(!Number.isInteger(token)||token<0||token>=model.config.vocabulary)throw RangeError('Invalid token');
  if(!cachePrefixes){let state=empty();for(const token of tokens)state=advance(state,token);return state;}
  let shared=0;while(shared<tokens.length&&shared<cachedTokens.length&&tokens[shared]===cachedTokens[shared])shared++;
  lastPrefixReused=shared;let state=cachedStates[shared];cachedStates=cachedStates.slice(0,shared+1);cachedTokens=tokens.slice();
  for(let i=shared;i<tokens.length;i++){state=advance(state,tokens[i]);cachedStates.push(state);}
  return state;
 }
 function generate(question,{history=[],maxNewTokens=model.config.context}={}){
  const input=tokenizer.prompt(question,history);if(input.length>=model.config.context)throw RangeError('Question/history exceeds context');
  let state=prefix(input);const tokens=[];let eos=false;
  for(let step=0;step<Math.min(maxNewTokens,model.config.context-input.length);step++){
   const scores=logits(state);let best=0;for(let i=1;i<scores.length;i++)if(scores[i]>scores[best])best=i;
   if(best===tokenizer.specials.eos){eos=true;break;}tokens.push(best);state=advance(state,best);
   if(cachePrefixes){cachedTokens.push(best);cachedStates.push(state);}
  }
  let validUtf8=true;try{tokenizer.decode(tokens,{fatal:true});}catch{validUtf8=false;}
  return {text:tokenizer.decode(tokens),tokens,eos,validUtf8,validTokens:validUtf8&&tokens.every(id=>id>=Object.keys(tokenizer.specials).length),inputTokens:input.length};
 }
 function generateBeam(question,{history=[],beamSize=4,lengthPenalty=.6,maxNewTokens=model.config.context}={}){
  if(beamSize===1)return generate(question,{history,maxNewTokens});
  const input=tokenizer.prompt(question,history);if(input.length>=model.config.context)throw RangeError('Question/history exceeds context');
  const result=beamSearch({state:prefix(input),logits,advance,eos:tokenizer.specials.eos,beamSize,lengthPenalty,maxSteps:Math.min(maxNewTokens,model.config.context-input.length)});
  let validUtf8=true;try{tokenizer.decode(result.tokens,{fatal:true});}catch{validUtf8=false;}
  return {text:tokenizer.decode(result.tokens),tokens:result.tokens,eos:result.eos,validUtf8,validTokens:validUtf8&&result.tokens.every(id=>id>=Object.keys(tokenizer.specials).length),inputTokens:input.length,beamSize,lengthPenalty,logProbability:result.logProbability,score:result.score};
 }
 function generateRaw(opening,{maxNewTokens=128}={}){
  // Preserve the original text exactly. No question roles, normalization or answer repair.
  const input=[tokenizer.specials.bos,...tokenizer.encode(opening)];
  if(input.length>=model.config.context)throw RangeError('Raw opening exceeds context');
  let state=prefix(input);const tokens=[];let eos=false;
  for(let step=0;step<Math.min(maxNewTokens,model.config.context-input.length);step++){
   const scores=logits(state);let best=0;for(let i=1;i<scores.length;i++)if(scores[i]>scores[best])best=i;
   if(best===tokenizer.specials.eos){eos=true;break;}tokens.push(best);state=advance(state,best);
   if(cachePrefixes){cachedTokens.push(best);cachedStates.push(state);}
  }
  let validUtf8=true;try{tokenizer.decode(tokens,{fatal:true});}catch{validUtf8=false;}
  return {text:tokenizer.decode(tokens),tokens,eos,validUtf8,validTokens:validUtf8&&tokens.every(id=>id>=Object.keys(tokenizer.specials).length),inputTokens:input.length};
 }
 return {tokenizer,generate,generateBeam,generateRaw,logits:tokens=>logits(prefix(tokens)),version:model.version,clearCache,cacheStats:()=>({enabled:cachePrefixes,reusedPrefixTokens:lastPrefixReused,storedTokens:cachedTokens.length,storedStates:cachedStates.length})};
}
