import {intentExamples} from './intent-examples.js';
import {semanticText} from './intent-model.js';
const ignored=new Set(['あなた','君','知りたい','教えて','ください','説明','tell','me','you','your','what','which','how','do','does','the','a','an','is','are','about','to','for','in','of','can']);
function tokens(text){
 text=semanticText(text.normalize('NFKC').toLowerCase()).replace(/(?:教えて|知りたい|聞きたい|聞かせて|ください|あなた|ですか|ますか|について)/g,'');
 const result=[];
 for(const match of text.matchAll(/[a-z][a-z0-9_-]*|[ぁ-んァ-ヶ一-龠ー]+/g)){
  const word=match[0];if(ignored.has(word))continue;
  if(/^[a-z]/.test(word)){result.push('w:'+word.replace(/(?:ing|s)$/,''));continue;}
  for(const size of [2,3])for(let i=0;i<=word.length-size;i++)result.push('j:'+word.slice(i,i+size));
 }
 return result;
}
const documents=intentExamples.flatMap(intent=>intent.examples.map(example=>({intent,terms:tokens(example)})));
const frequencies=new Map();for(const d of documents)for(const term of new Set(d.terms))frequencies.set(term,(frequencies.get(term)||0)+1);
const idf=term=>Math.log((documents.length+1)/((frequencies.get(term)||0)+1))+1;
function vector(terms){const counts=new Map();for(const t of terms)counts.set(t,(counts.get(t)||0)+1);const weights=new Map([...counts].map(([t,n])=>[t,(1+Math.log(n))*idf(t)]));const norm=Math.hypot(...weights.values());return {weights,norm};}
for(const document of documents)document.vector=vector(document.terms);
export function retrieveIntent(text){
 const query=vector(tokens(text));if(!query.norm)return null;
 const ranks=new Map();
 for(const document of documents){let dot=0;for(const [term,weight] of query.weights)dot+=weight*(document.vector.weights.get(term)||0);const score=dot/(query.norm*document.vector.norm||1);const list=ranks.get(document.intent)||[];list.push(score);ranks.set(document.intent,list);}
 const ranked=[...ranks].map(([intent,scores])=>{scores.sort((a,b)=>b-a);return {intent,score:scores[0]*.85+(scores[1]||0)*.15};}).sort((a,b)=>b.score-a.score);
 const best=ranked[0];if(!best||best.score<.46||best.score-(ranked[1]?.score||0)<.07)return null;
 return {factIds:best.intent.facts,intent:best.intent.id,confidence:best.score};
}
