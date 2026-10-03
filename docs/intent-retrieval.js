import {intentExamples} from './intent-examples.js?v=20261003-article-topics-4';
import {semanticText,semanticModel} from './intent-model.js?v=20261003-article-topics-4';
const ignored=new Set(['あなた','君','知りたい','教えて','ください','説明','tell','me','you','your','what','which','how','do','does','the','a','an','is','are','about','to','for','in','of','can']);
export function questionTokens(text){
 text=semanticText(text.normalize('NFKC').toLowerCase()).replace(/(?:教えて|知りたい|聞きたい|聞かせて|ください|あなた|ですか|ますか|について)/g,'');
 const result=[];
 for(const match of text.matchAll(/[a-z][a-z0-9_-]*|[ぁ-んァ-ヶ一-龠ー]+/g)){
  const word=match[0];if(ignored.has(word))continue;
  if(/^[a-z]/.test(word)){result.push('w:'+word.replace(/(?:ing|s)$/,''));continue;}
  for(const size of [2,3])for(let i=0;i<=word.length-size;i++)result.push('j:'+word.slice(i,i+size));
 }
 return result;
}
const meaningWeights={role:1.5,activity:1.2,interest:1.2,brand:1.4,create:1.2,how:1.8,ai:1.4,responsibility:2.1,design:1.2,values:1.8,article:1.4,subject:2.2,link:2.2,where:1.8,site:1.2,chat:1.4,implementation:2,mechanism:2,privacy:2.2};
export function meaningVector(text){
 const canonical=semanticText(text),concepts=new Set(Object.entries(semanticModel.concepts).filter(([,pattern])=>pattern.test(canonical)).map(([id])=>id));
 const weights=new Map();
 for(const [id,weight] of Object.entries(meaningWeights)){
  if(!concepts.has(id)||id==='subject'&&!concepts.has('article'))continue;
  weights.set('meaning:'+id,weight);
 }
 if(concepts.has('article')&&concepts.has('subject'))weights.set('request:article-subject',3);
 if(concepts.has('article')&&(concepts.has('link')||concepts.has('where')))weights.set('request:article-read',3);
 if(concepts.has('create')&&concepts.has('how'))weights.set('request:creation-process',3);
 if(concepts.has('ai')&&concepts.has('responsibility'))weights.set('request:ai-responsibility',3);
 return {weights,norm:Math.hypot(...weights.values())};
}
function cosine(a,b){let dot=0;for(const [term,weight] of a.weights)dot+=weight*(b.weights.get(term)||0);return dot/(a.norm*b.norm||1);}
const documents=intentExamples.flatMap(intent=>intent.examples.map(example=>({intent,terms:questionTokens(example),meaning:meaningVector(example)})));
const frequencies=new Map();for(const d of documents)for(const term of new Set(d.terms))frequencies.set(term,(frequencies.get(term)||0)+1);
const idf=term=>Math.log((documents.length+1)/((frequencies.get(term)||0)+1))+1;
function vector(terms){const counts=new Map();for(const t of terms)counts.set(t,(counts.get(t)||0)+1);const weights=new Map([...counts].map(([t,n])=>[t,(1+Math.log(n))*idf(t)]));const norm=Math.hypot(...weights.values());return {weights,norm};}
for(const document of documents)document.vector=vector(document.terms);
export function retrieveIntent(text){
 const query=vector(questionTokens(text)),meaning=meaningVector(text);if(!query.norm)return null;
 const ranks=new Map();
 for(const document of documents){const lexical=cosine(query,document.vector),semantic=cosine(meaning,document.meaning);const score=(meaning.norm&&document.meaning.norm)? .8*lexical+.2*semantic : lexical;const list=ranks.get(document.intent)||[];list.push(score);ranks.set(document.intent,list);}
 const ranked=[...ranks].map(([intent,scores])=>{scores.sort((a,b)=>b-a);return {intent,score:scores[0]*.85+(scores[1]||0)*.15};}).sort((a,b)=>b.score-a.score);
 const best=ranked[0];if(!best||best.score<.46||best.score-(ranked[1]?.score||0)<.07)return null;
 return {factIds:best.intent.facts,intent:best.intent.id,confidence:best.score};
}
