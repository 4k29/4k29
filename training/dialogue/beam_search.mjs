// Independent bounded search over model probabilities; no answers or grammar.
export function beamSearch({state,logits,advance,eos,beamSize=4,lengthPenalty=.6,maxSteps}){
 if(!Number.isInteger(beamSize)||beamSize<1||beamSize>16||!Number.isFinite(lengthPenalty)||lengthPenalty<0||!Number.isInteger(maxSteps)||maxSteps<0)throw RangeError('Invalid beam configuration');
 const norm=length=>((5+length)/6)**lengthPenalty;
 const ranked=(a,b)=>b.score-a.score||a.tokens.join(',').localeCompare(b.tokens.join(','),'en');
 let active=[{state,tokens:[],logProbability:0}],finished=[];
 for(let step=0;step<maxSteps&&active.length;step++){
  const candidates=[];
  for(const beam of active){
   const scores=logits(beam.state),maximum=Math.max(...scores);let denominator=0;
   for(const score of scores)denominator+=Math.exp(score-maximum);
   const logDenominator=maximum+Math.log(denominator),endProbability=beam.logProbability+scores[eos]-logDenominator;
   if(Number.isFinite(endProbability))finished.push({tokens:beam.tokens,eos:true,logProbability:endProbability,score:endProbability/norm(beam.tokens.length+1)});
   const top=[];
   for(let token=0;token<scores.length;token++){
    if(token===eos||!Number.isFinite(scores[token]))continue;
    const item={token,logProbability:beam.logProbability+scores[token]-logDenominator};let index=0;
    while(index<top.length&&(top[index].logProbability>item.logProbability||(top[index].logProbability===item.logProbability&&top[index].token<token)))index++;
    top.splice(index,0,item);if(top.length>beamSize)top.pop();
   }
   for(const item of top)candidates.push({parent:beam.state,tokens:[...beam.tokens,item.token],token:item.token,logProbability:item.logProbability,score:item.logProbability/norm(beam.tokens.length+1)});
  }
  finished.sort(ranked);finished=finished.slice(0,beamSize);candidates.sort(ranked);
  active=candidates.slice(0,beamSize).map(({parent,token,...beam})=>({...beam,state:advance(parent,token)}));
  // Future log probabilities cannot increase. The maximum allowed length gives
  // an optimistic bound for each retained branch, permitting a safe early exit.
  if(finished.length&&finished[0].score>=Math.max(...active.map(b=>b.logProbability/norm(maxSteps))))break;
 }
 if(finished.length)return finished[0];
 const candidates=active.map(({state,...b})=>({...b,eos:false,score:b.logProbability/norm(b.tokens.length)})).sort(ranked);
 return candidates[0]||{tokens:[],eos:false,logProbability:0,score:0};
}
