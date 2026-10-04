import {rankAnswerFacts} from './answer-priority.js?v=20261004-transformer-5';
import {linksForFact} from './answer-links.js?v=20261004-transformer-5';
import {createSentenceRenderer} from './predictive-generator.js?v=20261004-transformer-5';
import {conversationalJapanese} from './response-voice.js?v=20261004-transformer-5';
function list(values,language){
 if(language==='ja')return values.length===2?values.join('と'):values.length>2?values.join('、'):values[0]||'';
 return values.length<2?values[0]||'':values.slice(0,-1).join(', ')+' and '+values.at(-1);
}
function sentence(facts,language,variant,renderer,hobbies,favoriteType=null){
 const relation=facts[0][language].relation,value=list(facts.map(f=>f[language].value),language);
 let kind=hobbies&&relation==='activity'?'hobbies':relation,label='';
 if(favoriteType){kind='favoriteThing';label=language==='ja'?({brand:'ブランド',drama:'ドラマ',manga:'漫画'})[favoriteType]||'もの':({brand:'brands',drama:'dramas',manga:'manga'})[favoriteType]||'things';}
 if(relation==='product'){
  if(['earphones','headphones'].includes(facts[0].category)){kind='audio';label=language==='ja'?(facts[0].category==='earphones'?'イヤホン':'ヘッドホン'):(facts[0].category==='earphones'?'earbuds':'headphones');}
  if(facts[0].category==='running-app')kind='runningApp';
  if(facts[0].category==='running-shoes')kind='runningShoes';
 }
 if(relation==='articleLink')return facts.map(f=>renderer.render('articleLink',language,f[language].value,'',variant)).join('\n');
 return renderer.render(kind,language,relation==='favorite'&&language==='ja'?'「'+value+'」':value,label,variant);
}
export function composeAnswer(facts,analyses,language,variant=0,options={}){
 facts=rankAnswerFacts(facts,analyses);
 const modes=analyses.filter(a=>!a.unknown).map(a=>a.mode);
 if(modes.length&&modes.every(mode=>mode==='value-only'))return facts.map(f=>f[language].shortName||f[language].value).join('\n');
 if(modes.length&&modes.every(mode=>mode==='url-only'))return facts.filter(f=>f.url).map(f=>f.url).join('\n');
 const renderer=options.renderer||createSentenceRenderer(options),groups=new Map();
 const interests=facts.filter(f=>f[language].relation==='interest');
 for(const fact of facts){
  let key=fact[language].relation;
  const request=analyses.find(a=>a.factIds?.includes(fact.id));
  if(key==='interest'&&['apple','nothing','openai'].includes(fact.id)&&['favorites','favorite-brands'].includes(request?.mode))key='favoriteThing:brand';
  else if(key==='favoriteThing')key+=':'+(fact.favoriteCategory||'things');
  if(key==='product'&&fact.category)key+=':'+fact.category;
  if(key==='interest'&&interests.length>3)key+=':'+(['apple','nothing','openai'].includes(fact.id)?'brands':'fields');
  if(key==='preference'&&facts.length>1)key+=':'+fact.id;
  key=analyses.findIndex(a=>a.factIds?.includes(fact.id))+':'+key;
  if(!groups.has(key))groups.set(key,[]);groups.get(key).push(fact);
 }
 const ordered=[...groups.values()],clauses=[];
 for(let i=0;i<ordered.length;i++){
  const group=ordered[i],relation=group[0][language].relation;
  const requests=analyses.filter(a=>group.some(f=>a.factIds?.includes(f.id))),hobbies=requests.some(a=>a.mode==='hobbies');
  if(requests.some(a=>['favorite-actor','favorite-protagonist'].includes(a.mode))){
   const field=requests.some(a=>a.mode==='favorite-actor')?'actor':'protagonist';
   for(const fact of group){const value=fact.publicDetails[field][language],label=language==='ja'?(field==='actor'?'主演':'主人公'):(field==='actor'?'lead actor':'protagonist');clauses.push(language==='ja'?fact[language].value+'の'+label+'は'+value+(options.style==='friendly'?'だよ。':'です。'):'The '+label+' of '+fact[language].value+' is '+value+'.');}
   continue;
  }
  if(requests.some(a=>a.mode==='favorite-detail')&&group.every(f=>f[language].overview)){
   for(const fact of group){const text=fact[language].overview.detail;clauses.push(language==='ja'&&options.style==='friendly'?conversationalJapanese(text):text);}
   continue;
  }
  if(relation==='knowledge'){
   const detailed=options.length==='detail'||requests.some(a=>a.mode==='knowledge-detail');
   const audioCategories=new Set(group.filter(f=>f.specification).map(f=>f.category));let lastCategory=null;
   for(const fact of group){
    if(audioCategories.has('earphones')&&audioCategories.has('headphones')&&fact.category!==lastCategory){clauses.push(language==='ja'?(fact.category==='earphones'?'イヤホン':'ヘッドホン'):(fact.category==='earphones'?'Earbuds':'Headphones'));lastCategory=fact.category;}
    let text=fact[language][detailed?'detail':'answer'];if(language==='ja'&&options.style==='friendly')text=conversationalJapanese(text);clauses.push(renderer.render('knowledge',language,text,'',variant+i));
   }
   continue;
  }
  const favoriteType=group.find(f=>f.favoriteCategory)?.favoriteCategory||(['favorites','favorite-brands'].some(mode=>requests.some(a=>a.mode===mode))&&group.every(f=>['apple','nothing','openai'].includes(f.id))?'brand':null);
  if(relation==='activity'&&group.every(f=>f.id==='tecirc')&&!hobbies&&requests.some(a=>a.intent==='article-subjects')&&facts.some(f=>f[language].relation==='writing'))continue;
  if(relation==='activity'&&!hobbies&&group.some(f=>f.id==='tecirc')){
   const text=language==='ja'?(options.style==='friendly'?'Tecircで記事を書いているよ。':'Tecircで記事を書いています。'):'I write articles at Tecirc.';
   clauses.push(renderer.render('knowledge',language,text,'',variant+i));
   const other=group.filter(f=>f.id!=='tecirc');if(other.length)clauses.push(sentence(other,language,variant+i,renderer,false));continue;
  }
  if(relation==='website'&&clauses.some(clause=>clause.includes(group[0][language].value)))continue;
  // Per-clause output restrictions do not leak into other requests.
  const restricted=requests.length&&requests.every(a=>['value-only','url-only'].includes(a.mode));
  let clause=requests.length&&requests.every(a=>a.mode==='value-only')?group.map(f=>f[language].shortName||f[language].value).join('\n'):requests.length&&requests.every(a=>a.mode==='url-only')?group.filter(f=>f.url).map(f=>f.url).join('\n'):sentence(group,language,variant+i,renderer,hobbies,favoriteType);
  if(!restricted&&favoriteType&&(options.length!=='brief'||requests.some(a=>a.mode==='favorite-detail'))){
   const detailed=options.length==='detail'||options.length!=='brief'&&requests.some(a=>a.mode==='favorite-detail');
   const summaries=group.map(f=>f[language].overview?.[detailed?'detail':'brief']).filter(Boolean).map(text=>language==='ja'&&options.style==='friendly'?conversationalJapanese(text):text);
   if(summaries.length)clause+='\n'+summaries.join('\n');
  }
  if(relation==='favorite'){const links=linksForFact(group[0],analyses);if(links.length)clause+='\n'+links.map(l=>l.label).join(' / ');}
  if(relation==='privacy'&&group[0][language].storage)clause+=' '+group[0][language].storage;
  if(language==='ja'&&relation==='interest'&&!favoriteType&&interests.length>3&&interests.some(f=>['apple','nothing','openai'].includes(f.id))&&interests.some(f=>!['apple','nothing','openai'].includes(f.id)))clause=(group.some(f=>['apple','nothing','openai'].includes(f.id))?'企業やブランドでは、':'分野では、')+clause;
  if(language==='ja'&&relation==='preference'&&clauses.length&&ordered[i-1][0][language].relation==='preference')clause='また、'+clause;
  clauses.push(clause);
 }
 return clauses.join('\n');
}
