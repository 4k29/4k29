// Rank only facts already accepted by the intent/unknown-attribute guards.
const priorities={
 'identity-overview':{name:120,role:110,tool:70,activity:50},
 'article-subjects':{writing:120,website:65,activity:10},
 'article-read':{articleLink:120},
 'creative-process':{tool:110,workflow:100,responsibility:70},
 'creative-division':{responsibility:120,tool:90},
 'human-contribution':{responsibility:120,tool:90}
};
export function answerEvidence(fact,analyses){
 const index=analyses.findIndex(a=>a.factIds?.includes(fact.id));
 const analysis=analyses[index]||{},relation=fact.ja.relation;
 const direct=analysis.factIds?.includes(fact.id)?100:0;
 const relevance=priorities[analysis.intent]?.[relation]||50;
 const focus=(analysis.mode==='hobbies'&&relation==='activity'?40:0)+(fact.category==='earphones'&&analysis.factIds?.includes('headphones')?1:0);
 return {clause:index<0?analyses.length:index,direct,relevance,focus,score:direct+relevance+focus};
}
export function rankAnswerFacts(facts,analyses){
 return facts.map((fact,index)=>({fact,index,evidence:answerEvidence(fact,analyses)})).sort((a,b)=>a.evidence.clause-b.evidence.clause||b.evidence.score-a.evidence.score||a.index-b.index).map(entry=>entry.fact);
}
function similarity(a,b){
 const grams=text=>new Set(Array.from({length:Math.max(0,text.length-2)},(_,i)=>text.slice(i,i+3)));
 const left=grams(a),right=grams(b);let common=0;for(const g of left)if(right.has(g))common++;
 return common/(left.size+right.size-common||1);
}
export function chooseWording(compose,turn,previous,{quality=()=>0}={}){
 if(!previous.length)return compose(turn);
 const unique=new Map();
 for(let i=0;i<24;i++){
  const text=compose(turn+i);if(unique.has(text))continue;
  const repeated=previous.includes(text)?1000:0;
  const similarityPenalty=previous.slice(-3).reduce((sum,reply,index)=>sum+similarity(text,reply)*(index+1),0);
  unique.set(text,{text,score:repeated+similarityPenalty+i*.005-.3*quality(text)});
 }
 return [...unique.values()].sort((a,b)=>a.score-b.score)[0].text;
}
