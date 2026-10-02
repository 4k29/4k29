import {normalizeQuestion,splitQuestions,analyzeQuestion} from './question-analysis.js';
// Rule-based composition: facts, aliases and routing are editable in profile.json.
const grammar={
 ja:{name:['名前は','といいます'],role:['です','として過ごしています'],tool:['を活用して開発しています','を使って制作しています'],workflow:['という流れで改善を重ねます','の順で制作を進めます'],responsibility:['は自分で担っています','を自分で考え、確認しています'],preference:['を大切にしています','を意識しています'],interest:['に関心があります','に興味を持っています'],activity:['をしています','に取り組んでいます'],product:['を愛用しています','が愛用製品です'],writing:['について記事を書いています','をテーマに執筆しています'],siteStack:['でこの自己紹介サイトを実装しています','がこのサイトの技術構成です'],siteEngine:['で回答を組み立てています','を使ってこのチャットを実装しています'],privacy:['は外部に送信しません','を外部に送らず、ブラウザ内で扱っています']},
 en:{name:['My name is ','You can call me '],role:['I am ','I am currently '],tool:['I develop with ','I make things with '],workflow:['My process is ','I work through '],responsibility:['I handle ','I take care of '],preference:['I care about ','I value '],interest:['I am interested in ','My interests include '],activity:['My activities include ','I spend time on '],product:['I use ','My go-to product is '],writing:['I write about ','My articles cover '],siteStack:['This profile site is built with ','This site uses '],siteEngine:['This chat composes answers with ','The dialogue engine uses '],privacy:['This site does not send outside the browser: ','This site keeps the following inside the browser: ']}
};
function join(values,language){if(language==='ja')return values.join('、');if(values.length<2)return values[0];return values.slice(0,-1).join(', ')+' and '+values.at(-1);}
export class Conversation{
 constructor(data){this.data=data;this.reset();}
 reset(){this.history=[];this.lastTopics=[];this.lastFactIds=[];this.seen=new Map();this.lastReplies=[];this.turn=0;}
 sentence(facts,language,variant){
  const relation=facts[0][language].relation,value=join(facts.map(f=>f[language].value),language);
  if(relation==='xMain')return language==='ja'?`X（Twitter）のメインアカウントは${value}です。`:`My main X (Twitter) account is ${value}.`;
  if(relation==='xSecondary')return language==='ja'?`サブアカウントは${value}です。`:`My secondary account is ${value}.`;
  if(relation==='website')return language==='ja'?`${value}で記事を読めます。`:`You can read my articles at ${value}.`;
  const parts=grammar[language][relation],part=parts[variant%parts.length];
  if(language==='en')return part+value+'.';
  if(relation==='name')return variant%2===0?'名前は'+value+'です。':value+'といいます。';
  return value+part+'。';
 }
 respond(question){
  const text=normalizeQuestion(question),language=/[ぁ-んァ-ヶ一-龠]/.test(text)?'ja':'en';
  const analyses=splitQuestions(text,this.data).map(clause=>analyzeQuestion(clause,this.data,this));
  const ids=new Set(analyses.flatMap(a=>a.factIds));
  let selected=this.data.facts.filter(f=>ids.has(f.id)),topics=[];
  const hasUnknown=analyses.some(a=>a.unknown);
  let output=this.data.unknownReply||'すみません、よく分かりません';
  if(selected.length){
   topics=[...new Set(selected.map(f=>f.topic))];
   const groups=new Map();for(const fact of selected){const relation=fact[language].relation;if(!groups.has(relation))groups.set(relation,[]);groups.get(relation).push(fact);}
   const compose=variant=>{const clauses=Array.from(groups.values(),(group,i)=>this.sentence(group,language,variant+i));if(variant%2&&clauses.length>1)clauses.push(clauses.shift());return clauses.join('\n');};
   output=compose(this.turn);if(this.lastReplies.includes(output))output=compose(this.turn+1);
   if(hasUnknown)output+='\n'+(this.data.unknownReply||'すみません、よく分かりません');
   for(const fact of selected)this.seen.set(fact.id,(this.seen.get(fact.id)||0)+1);
   this.lastTopics=topics;this.lastFactIds=selected.map(f=>f.id);
  }else{topics=[];this.lastTopics=[];this.lastFactIds=[];}
  const links=selected.filter(f=>f.url).map(f=>({label:f[language].value,url:f.url}));
  this.turn++;this.lastReplies.push(output);this.lastReplies=this.lastReplies.slice(-4);this.history.push({question,answer:output,topics,language,factIds:selected.map(f=>f.id)});
  return {text:output,topics,language,links,factIds:selected.map(f=>f.id)};
 }
}
