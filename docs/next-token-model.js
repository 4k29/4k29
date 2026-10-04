// Small conditional statistical language model. It predicts tokens from up to
// three preceding tokens, the relation, the language and the requested style.
const totals=new WeakMap();
const scopeIndices=new WeakMap();
function conditional(model,scope,history,next){
 if(!scopeIndices.has(model))scopeIndices.set(model,new Map(model.scopes.map((s,i)=>[s,i])));
 const scopeId=scopeIndices.get(model).get(scope);
 let weighted=0,totalWeight=0;
 for(const [order,weight] of [[0,.1],[1,.2],[2,.3],[3,.4]]){
  const entry=model.counts[scopeId+'|'+(order?history.slice(-order).join(','):'')];
  if(!entry)continue;
  let total=totals.get(entry);if(total===undefined){total=Object.values(entry).reduce((s,n)=>s+n,0);totals.set(entry,total);}
  weighted+=weight*((entry[next]||0)+.08)/(total+.08*model.vocabulary.length);totalWeight+=weight;
 }
 return totalWeight?weighted/totalWeight:1/model.vocabulary.length;
}
export function nextTokenProbability(model,{language,kind,style='polite'},history,next){
 const id=typeof next==='number'?next:model.vocabulary.indexOf(next);
 return .65*conditional(model,language+':'+kind+':*',history,id<0?2:id)+.35*conditional(model,language+':*:'+style,history,id<0?2:id);
}
export function predictNextTokens(model,context,history,allowed){
 const candidates=allowed.map(token=>({token,probability:nextTokenProbability(model,context,history,token)}));
 const sum=candidates.reduce((n,c)=>n+c.probability,0);
 return candidates.map(c=>({...c,constrainedProbability:c.probability/(sum||1)})).sort((a,b)=>b.probability-a.probability||a.token-b.token);
}
export function sequenceLikelihood(model,context,tokens){
 const history=[0,0,0];let logProbability=0;
 for(const token of [...tokens,1]){logProbability+=Math.log(nextTokenProbability(model,context,history,token));history.push(token);}
 return {logProbability,meanLogProbability:logProbability/(tokens.length+1),tokens:tokens.length+1};
}
