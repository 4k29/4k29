import {knowledgeFacts} from './knowledge-data.js?v=20261004-transformer-5b';
const forbidden=/あなた|僕|俺|私|友達|先生|好き|推し|持って|所有|買った|契約して|最新|今日|ニュース|価格|値段|おすすめ|\b(?:your|my|you|own|bought|latest|today|price|recommend)\b/i;
const request=/とは|って何|ってなに|何ですか|どんな|意味|説明|について|違い|比較|仕組み|具体例|例を|\b(?:what|explain|describe|meaning|difference|compare|how)\b/i;
const removeRequests=/とは|って(?:何|なに|どんな(?:もの|こと|仕組み)?)|何ですか|何なの|何か|何|は何|ですか|について|教えて(?:ください|くれる|もらえる)?|説明(?:して(?:ください|くれる)?)?|意味|違い|比較|仕組み|具体例|例を|簡単に|わかりやすく|分かりやすく|ざっくり|詳しく|もう少し|短く|ひとことで|知りたい|お願い(?:します)?|ねえ|まず|の|と|を|は|って|及び|および|\b(?:what|is|are|a|an|the|explain|describe|meaning|difference|differences|between|and|compare|how|does|work|works|about|tell|me|please|briefly|simply|in|detail|with|examples?)\b|[\s、,\/?!？！。:：・（）()]/gi;
export function withPublicKnowledge(data){return {...data,facts:[...data.facts,...knowledgeFacts.filter(k=>!data.facts.some(f=>f.id===k.id))]};}
export function resolveKnowledge(text,data,context,matches){
 if(forbidden.test(text))return null;
 const facts=data.facts.filter(f=>f.topic==='general-knowledge');
 if(/^(?:それ|その話|そのこと|もう少し|もっと)?(?:について|を)?(?:詳しく|具体例|例を教えて)|^(?:tell me more|more details|give (?:me )?an example)$/.test(text)){
  const prior=facts.filter(f=>context.lastFactIds.includes(f.id));if(prior.length)return {factIds:prior.map(f=>f.id),topics:['general-knowledge'],unknown:false,intent:'knowledge-followup',mode:'knowledge-detail',learningEligible:false,contextDependent:true};
 }
 const literal=facts.filter(f=>(f.questions||[]).some(p=>new RegExp(p,'i').test(text)));
 const named=facts.filter(f=>(f.aliases||[]).some(alias=>matches(text,alias)));
 const candidates=literal.length?literal:named;
 if(!candidates.length)return null;
 let rest=text;
 for(const alias of candidates.flatMap(f=>f.aliases||[]).sort((a,b)=>b.length-a.length))rest=rest.replaceAll(alias.toLowerCase(),'');
 if(!literal.length&&(rest.replace(removeRequests,'')||!request.test(text)&&!context.explanationRequested))return null;
 return {factIds:candidates.map(f=>f.id),topics:['general-knowledge'],unknown:false,intent:'public-knowledge',mode:context.explanationRequested||/詳しく|具体例|例を|違い|比較|\b(?:detail|example|difference|compare)\b/.test(text)?'knowledge-detail':'knowledge',learningEligible:false};
}
