// Rule-based composition: facts, aliases and routing are editable in profile.json.
const grammar={
 ja:{name:['名前は','といいます'],role:['です','として過ごしています'],tool:['を活用して開発しています','を使って制作しています'],workflow:['という流れで改善を重ねます','の順で制作を進めます'],responsibility:['は自分で担っています','を自分で考え、確認しています'],preference:['を大切にしています','を意識しています'],interest:['に関心があります','に興味を持っています'],activity:['をしています','に取り組んでいます'],product:['を愛用しています','が愛用製品です'],writing:['について記事を書いています','をテーマに執筆しています'],siteStack:['でこの自己紹介サイトを実装しています','がこのサイトの技術構成です'],siteEngine:['で回答を組み立てています','を使ってこのチャットを実装しています'],privacy:['は外部に送信しません','を外部に送らず、ブラウザ内で扱っています']},
 en:{name:['My name is ','You can call me '],role:['I am ','I am currently '],tool:['I develop with ','I make things with '],workflow:['My process is ','I work through '],responsibility:['I handle ','I take care of '],preference:['I care about ','I value '],interest:['I am interested in ','My interests include '],activity:['My activities include ','I spend time on '],product:['I use ','My go-to product is '],writing:['I write about ','My articles cover '],siteStack:['This profile site is built with ','This site uses '],siteEngine:['This chat composes answers with ','The dialogue engine uses '],privacy:['This site does not send outside the browser: ','This site keeps the following inside the browser: ']}
};
function normalized(text){return text.normalize('NFKC').toLowerCase().replace(/[\s　]+/g,' ').trim();}
function matches(text,word){word=normalized(word);return /^[a-z0-9_ ]+$/.test(word)?new RegExp(`(?:^|[^a-z0-9_])${word.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?:$|[^a-z0-9_])`,'i').test(text):text.includes(word);}
function join(values,language){if(language==='ja')return values.join('、');if(values.length<2)return values[0];return values.slice(0,-1).join(', ')+' and '+values.at(-1);}
export class Conversation{
 constructor(data){this.data=data;this.reset();}
 reset(){this.history=[];this.lastTopics=[];this.lastFactIds=[];this.seen=new Map();this.lastReplies=[];this.turn=0;}
 detect(text){return this.data.topics.map(topic=>({id:topic.id,score:topic.keywords.reduce((n,key)=>n+(matches(text,key)?(key.length>2?2:1):0),0)})).filter(t=>t.score>0).sort((a,b)=>b.score-a.score).slice(0,3).map(t=>t.id);}
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
  const text=normalized(question),language=/[ぁ-んァ-ヶ一-龠]/.test(text)?'ja':'en';
  const follow=/もっと|詳しく|それ|その|他には|続き|ほか|他は|more|else|that|continue|detail/.test(text);
  const overview=/^(こんにちは|こんばんは|おはよう|やあ|よろしく|hello|hi|hey|自己紹介(?:して)?|紹介して|あなたについて(?:教えて)?|どんな人(?:ですか)?|about you|introduce yourself)[!！?？。\s]*$/.test(text);
  const unknown=(this.data.unknownPatterns||[]).some(pattern=>new RegExp(pattern,'i').test(text));
  let topics=this.detect(text),selected=[];
  if(!unknown){
   const routes=(this.data.routes||[]).filter(route=>route.keywords.some(key=>matches(text,key)));
   const priority=Math.max(0,...routes.map(route=>route.priority||0));
   const routedIds=new Set(routes.filter(route=>(route.priority||0)===priority).flatMap(route=>route.factIds));
   const targeted=this.data.facts.filter(f=>[...(f.aliases||[]),...(f.tags||[])].some(key=>matches(text,key)));
   if(overview){topics=['identity','development','interests'];}
   else if(routedIds.size){selected=this.data.facts.filter(f=>routedIds.has(f.id));const routedTopics=new Set(selected.map(f=>f.topic));selected.push(...targeted.filter(f=>!routedTopics.has(f.topic)));}
   else if(targeted.length){selected=targeted;}
   if(!topics.length&&follow&&this.lastTopics.length)topics=[...this.lastTopics];
   if(!selected.length&&topics.length){
    for(const topic of topics){const facts=this.data.facts.filter(f=>f.topic===topic);
     facts.sort((a,b)=>(this.seen.get(a.id)||0)-(this.seen.get(b.id)||0));selected.push(...facts.slice(0,topic==='identity'?2:3));}
   }
  }
  let output=this.data.unknownReply||'すみません、よく分かりません';
  if(selected.length){
   topics=[...new Set(selected.map(f=>f.topic))];
   const groups=new Map();for(const fact of selected){const relation=fact[language].relation;if(!groups.has(relation))groups.set(relation,[]);groups.get(relation).push(fact);}
   const compose=variant=>{const clauses=Array.from(groups.values(),(group,i)=>this.sentence(group,language,variant+i));if(variant%2&&clauses.length>1)clauses.push(clauses.shift());return clauses.join('\n');};
   output=compose(this.turn);if(this.lastReplies.includes(output))output=compose(this.turn+1);
   for(const fact of selected)this.seen.set(fact.id,(this.seen.get(fact.id)||0)+1);
   this.lastTopics=topics;this.lastFactIds=selected.map(f=>f.id);
  }else{topics=[];this.lastTopics=[];this.lastFactIds=[];}
  const links=selected.filter(f=>f.url).map(f=>({label:f[language].value,url:f.url}));
  this.turn++;this.lastReplies.push(output);this.lastReplies=this.lastReplies.slice(-4);this.history.push({question,answer:output,topics,language});
  return {text:output,topics,language,links};
 }
}
