import {questionTokens} from './intent-retrieval.js';
// Browser-local examples teach phrasing, never facts or finished answers.
// Rebuild from the journal on each lookup so review/deletion applies immediately.
export class LocalLearning{
 constructor(data,records=()=>[]){this.data=data;this.records=records;}
 examples(){
  const valid=new Set(this.data.facts.map(f=>f.id)),unique=new Map();
  for(const r of this.records()){
   if(!r.learningEligible||r.learned||r.needsReview||r.unanswered||!r.factIds?.length||!r.factIds.every(id=>valid.has(id)))continue;
   const terms=new Set(questionTokens(r.question));if(terms.size<3)continue;
   const key=[...terms].sort().join('|'),label=[...r.factIds].sort().join('|');
   const previous=unique.get(key);
   if(previous&&previous.label!==label){previous.conflict=true;continue;}
   if(!previous)unique.set(key,{terms,label,factIds:[...r.factIds],intent:r.intents?.[0]||'local-phrasing'});
  }
  return [...unique.values()].filter(e=>!e.conflict);
 }
 retrieve(question){
  const terms=new Set(questionTokens(question));if(terms.size<3)return null;
  const ranked=new Map();
  for(const example of this.examples()){
   const common=[...terms].filter(t=>example.terms.has(t)).length;
   // Require coverage on both sides; a short topic is not a detailed question.
   if(common/terms.size<.85||common/example.terms.size<.75)continue;
   const score=2*common/(terms.size+example.terms.size);
   const previous=ranked.get(example.label);
   if(!previous||score>previous.score)ranked.set(example.label,{...example,score});
  }
  const matches=[...ranked.values()].sort((a,b)=>b.score-a.score),best=matches[0];
  if(!best||best.score<.88||best.score-(matches[1]?.score||0)<.12)return null;
  return {factIds:best.factIds,intent:best.intent,confidence:best.score};
 }
}
