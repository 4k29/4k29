// Assemble explanatory sentences from registered values. Variants change wording, never facts or logical order.
const ja={
 tool:['を制作に活用しています','を使って制作しています','を開発に使っています','を活用して開発しています'],
 responsibility:['は自分で担っています','を担当しています','は自分の担当です','を自分で行っています'],
 preference:['を大切にしています','を重視しています','を意識しています','を制作で大切にしています'],
 interest:['に関心があります','に興味があります','に興味を持っています','が関心のある分野です'],
 product:['を使っています','を愛用しています','を普段使っています','が愛用品です'],
 writing:['について記事を書いています','をテーマに執筆しています'],
 siteStack:['でこの自己紹介サイトを実装しています','がこのサイトの技術構成です'],
 siteEngine:['で回答を組み立てています','を使ってこのチャットを実装しています'],
 privacy:['は外部に送信しません','を外部に送らず、ブラウザ内で扱っています']
};
const en={name:['My name is ','You can call me '],role:['I am ','I am currently '],tool:['I develop with ','I make things with '],workflow:['My process is ','I work through '],responsibility:['I handle ','I take care of '],preference:['I care about ','I value '],interest:['I am interested in ','My interests include '],activity:['My activities include ','I spend time on '],product:['I use ','My go-to product is '],writing:['I write about ','My articles cover '],siteStack:['This profile site is built with ','This site uses '],siteEngine:['This chat composes answers with ','The dialogue engine uses '],privacy:['This site does not send outside the browser: ','This site keeps the following inside the browser: '],favorite:['My favorite is '],subscription:['My subscriptions are ']};
function list(values,language){if(language==='ja')return values.join('、');if(values.length<2)return values[0]||'';return values.slice(0,-1).join(', ')+' and '+values.at(-1);}
function sentence(facts,language,variant){
 const relation=facts[0][language].relation,value=list(facts.map(f=>f[language].value),language);
 if(relation==='xMain')return language==='ja'?`X（Twitter）のメインアカウントは${value}です。`:`My main X (Twitter) account is ${value}.`;
 if(relation==='xSecondary')return language==='ja'?`サブアカウントは${value}です。`:`My secondary account is ${value}.`;
 if(relation==='website')return language==='ja'?`${value}で記事を読めます。`:`You can read my articles at ${value}.`;
 if(language==='en'){const parts=en[relation];return parts[variant%parts.length]+value+'.';}
 if(relation==='name')return ['名前は'+value+'です。',value+'といいます。',value+'です。','呼び名は'+value+'です。'][variant%4];
 if(relation==='role')return value+'です。';
 if(relation==='workflow')return ['進め方は「'+value+'」です。',value+'の順で制作を進めます。',value+'という手順で制作します。',value+'の流れで試しながら改善しています。'][variant%4];
 if(relation==='activity')return ['活動は、'+value+'です。',value+'に取り組んでいます。',value+'をしています。','普段の活動は、'+value+'です。'][variant%4];
 if(relation==='favorite')return '推しは'+value+'です。';
 if(relation==='subscription')return facts.length===1?value+'を契約しています。':'契約しているサブスクは、'+value+'です。';
 const parts=ja[relation];return value+parts[variant%parts.length]+'。';
}
export function composeAnswer(facts,analyses,language,variant){
 const modes=analyses.filter(a=>!a.unknown).map(a=>a.mode);
 if(modes.length&&modes.every(mode=>mode==='value-only'))return facts.map(f=>f[language].value).join('\n');
 if(modes.length&&modes.every(mode=>mode==='url-only'))return facts.filter(f=>f.url).map(f=>f.url).join('\n');
 const groups=new Map();
 for(const fact of facts){let key=fact[language].relation;if(key==='interest'&&facts.filter(f=>f[language].relation==='interest').length>3)key+=':'+(['apple','nothing','openai'].includes(fact.id)?'brands':'fields');if(key==='preference'&&facts.length>1)key+=':'+fact.id;if(!groups.has(key))groups.set(key,[]);groups.get(key).push(fact);}
 const ordered=[...groups.values()];
 // Answer article-content questions with their subject first, then the publication/link context.
 if(analyses.some(a=>a.intent==='article-subjects'))ordered.sort((a,b)=>(a[0][language].relation==='writing'?-1:0)-(b[0][language].relation==='writing'?-1:0));
 const clauses=[];
 for(let i=0;i<ordered.length;i++){
  const group=ordered[i],relation=group[0][language].relation;
  if(relation==='website'&&clauses.some(clause=>clause.includes(group[0][language].value)))continue;
  let clause=sentence(group,language,variant+i);
  if(relation==='privacy'&&group[0][language].exception)clause+=' '+group[0][language].exception;
  if(language==='ja'&&relation==='interest'&&groups.has('interest:brands')&&groups.has('interest:fields'))clause=(group.some(f=>['apple','nothing','openai'].includes(f.id))?'企業やブランドでは、':'分野では、')+clause;
  if(language==='ja'&&relation==='preference'&&clauses.length&&ordered[i-1][0][language].relation==='preference')clause='また、'+clause;
  clauses.push(clause);
 }
 return clauses.join('\n');
}
