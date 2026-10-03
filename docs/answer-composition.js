import {rankAnswerFacts} from './answer-priority.js?v=20261003-weights-5';
// Assemble explanatory sentences from registered values. Variants change wording, never facts or logical order.
const ja={
 tool:['を制作に活用しています','を使って制作しています','を開発に使っています','を活用して開発しています','を制作のツールとして使っています','で制作を進めています'],
 responsibility:['は自分で担っています','を担当しています','は自分の担当です','を自分で行っています','は自分で担当しています','は自分が担う部分です'],
 preference:['を大切にしています','を重視しています','を意識しています','を制作で大切にしています','を大事にしています','を念頭に置いて制作しています'],
 interest:['に関心があります','に興味があります','に興味を持っています','に関心を持っています','が気になっています','への関心があります'],
 product:['を使っています','を愛用しています','を普段使っています','が愛用品です','が使っている製品です','を使う製品として選んでいます'],
 writing:['について記事を書いています','をテーマに執筆しています','について書いています','が記事で扱っているテーマです','についての記事を執筆しています','を題材に記事を書いています'],
 siteStack:['でこの自己紹介サイトを実装しています','がこのサイトの技術構成です'],
 siteEngine:['で回答を組み立てています','を使ってこのチャットを実装しています','を用いて返答を構成しています','でこのチャットの返答を作っています'],
 privacy:['は外部に送信しません','を外部に送らず、ブラウザ内で扱っています']
};
const en={name:['My name is ','You can call me ','I go by ','The name I use is '],role:['I am ','I am currently '],tool:['I develop with ','I make things with '],workflow:['My process is ','I work through '],responsibility:['I handle ','I take care of '],preference:['I care about ','I value '],interest:['I am interested in ','My interests include ','I have an interest in ','I am drawn to '],activity:['My activities include ','I spend time on '],product:['I use ','My go-to product is '],writing:['I write about ','My articles cover ','The subjects I write about are ','My writing focuses on '],siteStack:['This profile site is built with ','This site uses '],siteEngine:['This chat composes answers with ','The dialogue engine uses '],privacy:['This site does not send outside the browser: ','This site keeps the following inside the browser: '],favorite:['My favorite is ','The person I like is ','My favorite person is ','My pick is '],subscription:['My subscriptions are ','I subscribe to ','The services I subscribe to are ','The subscriptions I use are ']};
function list(values,language){if(language==='ja')return values.length===2?values.join('と'):values.length>2?values.slice(0,-1).join('、')+'、'+values.at(-1):values[0]||'';if(values.length<2)return values[0]||'';return values.slice(0,-1).join(', ')+' and '+values.at(-1);}
function sentence(facts,language,variant){
 const relation=facts[0][language].relation,value=list(facts.map(f=>f[language].value),language);
 if(relation==='product'&&facts.every(f=>f.category==='running-app'))return language==='ja'?['ランニング用のアプリは、'+value+'です。','ランニング用のアプリとして、'+value+'を使っています。','使っているランニングアプリは、'+value+'です。',value+'がランニング用のアプリです。'][variant%4]:'My running app is '+value+'.';
 if(relation==='product'&&facts.every(f=>f.category==='running-shoes'))return language==='ja'?['ランニング用の靴は、'+value+'です。','ランニングでは、'+value+'をシューズとして使っています。','ランニングシューズは、'+value+'を使っています。',value+'がランニング用の靴です。'][variant%4]:'I use '+value+' for running.';
 if(relation==='xMain')return language==='ja'?`X（Twitter）のメインアカウントは${value}です。`:`My main X (Twitter) account is ${value}.`;
 if(relation==='xSecondary')return language==='ja'?`サブアカウントは${value}です。`:`My secondary account is ${value}.`;
 if(relation==='articleLink')return facts.map(f=>language==='ja'?[`「${f.ja.value}」を読めます。`,`該当する記事は「${f.ja.value}」です。`,`「${f.ja.value}」の記事はこちらです。`,`こちらの記事を案内できます：${f.ja.value}`][variant%4]:`You can read “${f.en.value}”.`).join('\n');
 if(relation==='website')return language==='ja'?[`${value}から記事を選んで読めます。`,`${value}に記事をまとめています。`,`記事は${value}で探せます。`,`記事を読むなら、${value}をご覧ください。`][variant%4]:`You can read my articles at ${value}.`;
 if(language==='en'){const parts=en[relation];if(relation==='product'&&variant%parts.length===1&&facts.length>1)return 'My go-to products are '+value+'.';return parts[variant%parts.length]+value+'.';}
 if(relation==='name')return ['名前は'+value+'です。',value+'といいます。',value+'です。','呼び名は'+value+'です。','名前は'+value+'といいます。',value+'という名前です。'][variant%6];
 if(relation==='role')return [value+'です。','現在は'+value+'です。',value+'として過ごしています。'][variant%3];
 if(relation==='workflow')return ['進め方は「'+value+'」です。',value+'の順で制作を進めます。',value+'という手順で制作します。',value+'の流れで試しながら改善しています。','制作は「'+value+'」という流れです。','制作では、'+value+'の順に進めています。'][variant%6];
 if(relation==='activity')return [value+'に取り組んでいます。',value+'をしています。','活動として'+value+'に取り組んでいます。','取り組んでいる活動は、'+value+'です。','活動には、'+value+'があります。',value+'が活動の内容です。'][variant%6];
 if(relation==='favorite')return ['推しは'+value+'です。',value+'が推しです。','好きな人は'+value+'です。','推しの名前は'+value+'です。','好きな人として挙げているのは'+value+'です。',value+'が好きな人です。'][variant%6];
 if(relation==='subscription')return ['契約しているサブスクは、'+value+'です。','サブスクとして'+value+'を契約しています。','利用しているサブスクは、'+value+'です。',value+'をサブスクとして利用しています。','サブスクの契約は、'+value+'です。','契約中のサービスは、'+value+'です。'][variant%6];
 const parts=ja[relation];return value+parts[variant%parts.length]+'。';
}
export function composeAnswer(facts,analyses,language,variant){
 facts=rankAnswerFacts(facts,analyses);
 const modes=analyses.filter(a=>!a.unknown).map(a=>a.mode);
 if(modes.length&&modes.every(mode=>mode==='value-only'))return facts.map(f=>f[language].value).join('\n');
 if(modes.length&&modes.every(mode=>mode==='url-only'))return facts.filter(f=>f.url).map(f=>f.url).join('\n');
 const groups=new Map();
 for(const fact of facts){let key=fact[language].relation;if(key==='product'&&['running-shoes','running-app'].includes(fact.category))key+=':'+fact.category;if(key==='interest'&&facts.filter(f=>f[language].relation==='interest').length>3)key+=':'+(['apple','nothing','openai'].includes(fact.id)?'brands':'fields');if(key==='preference'&&facts.length>1)key+=':'+fact.id;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(fact);}
 const ordered=[...groups.values()];
 // Answer article-content questions with their subject first, then the publication/link context.

 const clauses=[];
 for(let i=0;i<ordered.length;i++){
  const group=ordered[i],relation=group[0][language].relation;
  if(relation==='activity'&&group.every(f=>f.id==='tecirc')&&!modes.includes('hobbies')&&analyses.some(a=>a.intent==='article-subjects')&&facts.some(f=>f[language].relation==='writing'))continue;
  if(relation==='website'&&clauses.some(clause=>clause.includes(group[0][language].value)))continue;
  let clause=sentence(group,language,variant+i);
  if(relation==='activity'&&modes.includes('hobbies')){const value=list(group.map(f=>f[language].value),language);clause=language==='ja'?['趣味は、'+value+'です。',value+'が趣味です。','趣味として'+value+'をしています。','趣味には、'+value+'があります。','楽しんでいる趣味は、'+value+'です。','趣味については、'+value+'を挙げています。'][variant%6]:'My hobbies include '+value+'.';}
  if(relation==='favorite'){const links=(group[0].links||[]).filter(l=>modes.includes('favorite-youtube')?l.channel==='youtube':modes.includes('favorite-x')?l.channel==='x':true);if(links.length)clause+='\n'+links.map(l=>l.label).join(' / ');}
  if(relation==='privacy'&&group[0][language].storage)clause+=' '+group[0][language].storage;
  if(language==='ja'&&relation==='interest'&&groups.has('interest:brands')&&groups.has('interest:fields'))clause=(group.some(f=>['apple','nothing','openai'].includes(f.id))?'企業やブランドでは、':'分野では、')+clause;
  if(language==='ja'&&relation==='preference'&&clauses.length&&ordered[i-1][0][language].relation==='preference')clause='また、'+clause;
  clauses.push(clause);
 }
 return clauses.join('\n');
}
