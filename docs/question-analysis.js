import {resolveEntities} from './answer-entities.js';
import {retrieveIntent} from './intent-retrieval.js';
import {semanticText,resolveSemanticIntent} from './intent-model.js';
// Local retrieval only: query scopes and evidence come from the editable profile.
export function normalizeQuestion(text){return String(text).normalize('NFKC').toLowerCase().replace(/[\s　]+/g,' ').trim();}
export function matchesKeyword(text,word){
 word=normalizeQuestion(word);
 if(word==='サブ'.toLowerCase())return /サブ(?:垢|アカ|のアカ|だけ|は|が|を|って|について|と|$)/i.test(text);
 if(word==='メイン'.toLowerCase())return /メイン(?:垢|アカ|のアカ|だけ|は|が|を|って|について|と|$)/i.test(text);
 return /^[a-z0-9_ ]+$/.test(word)?new RegExp(`(?:^|[^a-z0-9_])${word.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?:$|[^a-z0-9_])`,'i').test(text):text.includes(word);
}
const followOnly=/^(?:それ|その話|そのこと|それについて|その話について)?(?:を|は)?(?:もっと|詳しく|もう少し|他には|ほかには|他は|ほかは|続き|続けて|教えて|聞かせて|説明して|知りたい|お願い|お願いし?ます|について|何|は|\s|[?？!！。])*$/;
export function isFollowUp(text){return Boolean(text)&&((followOnly.test(text)&&/それ|その|もっと|詳しく|他|ほか|続|もう少し/.test(text))||/^(?:more|tell me more|anything else|what else|continue|details|about that)[?.!\s]*$/.test(text));}
function standalone(text,data){return data.facts.some(f=>[...(f.aliases||[]),...(f.tags||[])].some(k=>matchesKeyword(text,k)))||data.unknownPatterns.some(p=>new RegExp(p,'i').test(text))||/趣味|興味|関心|メイン|サブ|hobb|interest/.test(text)||resolveSemanticIntent(text,{lastFactIds:[]}).factIds.length>0;}
export function splitQuestions(text,data){
 const sentences=text.split(/[?？!！。;；\n]+|、(?:あと|それから|それと)|\b(?:also|and then)\b/).map(s=>s.trim()).filter(Boolean);
 const result=[];
 for(const sentence of sentences){
  // Split coordinated requests only if both sides independently identify a subject.
  // Preserve lexical compounds such as 人とコンピューター.
  if(/(?:と|や).+以外|(?:and|or).+except/.test(sentence)){result.push(sentence);continue;}
  const pieces=sentence.split(/、|(?:それと|それから)|\s+and\s+|と(?=(?:あなた|君|きみ|趣味|名前|年齢|職業|誕生日|住所|好きな|愛用|サブ|メイン|写真|ランニング|開発|興味|プライバシー|このサイト))/);
  if(pieces.length>1&&pieces.every(p=>standalone(p,data)))result.push(...pieces.map(p=>p.trim()));else result.push(sentence);
 }
 return result;
}
export function analyzeQuestion(text,data,context){
 if(/^(?:検索|けんさく|search)\s*[:：\s]|(?:を|について)(?:検索|けんさく|ググって)|(?:検索|けんさく)して|\bsearch (?:for|the web)\b/i.test(text))return {factIds:[],topics:[],unknown:true};
 text=semanticText(text);
 if(!/この(?:サイト|ページ|チャット)|自己紹介サイト|this (?:site|page|chat)/.test(text)&&(/web|ウェブ|ホームページ|website|サイト/.test(text)&&/開発|制作|作|build|make|develop/.test(text)||/^(?:web|ウェブ|website)$/.test(text)))return {factIds:[],topics:[],unknown:true};
 const historyReference=text.match(/^(最初|(?:[1-9][0-9]*)つ前|(?:[1-9][0-9]*)回前)の(?:話|質問|回答|答え)(?:について)?(?:もう一度|もう一回|詳しく|教えて|は|を|何|\s)*$/);
 if(historyReference){
  const index=historyReference[1]==='最初'?0:context.history.length-Number.parseInt(historyReference[1],10);
  const entry=context.history[index];const ids=entry?.factIds||[];
  return {factIds:ids,topics:entry?.topics||[],unknown:!ids.length};
 }
 const referenceLink=/^(?:それ|その|さっき|前の).*(?:リンク|url|link)/.test(text);
 const follow=isFollowUp(text),overview=/^(?:こんにちは|こんばんは|おはよう|やあ|よろしく|hello|hi|hey|自己紹介(?:して)?|紹介して|あなたについて(?:教えて)?|どんな人(?:ですか)?|about you|introduce yourself)[!！?？。\s]*$/.test(text);
 const unsupportedSubject=/(?:私|僕|俺|わたし|友達|友人|先生)の(?:名前|趣味|職業|興味|仕事|イヤホン|ヘッドホン|サブスク|契約|推し)|\bmy (?:name|job|hobbies|interests)\b/.test(text);
 const unsupportedRank=/(?:一番|いちばん|最も|一位|ランキング).*(?:好き|興味|関心|大切|重視)|(?:好き|興味|大切).*(?:一番|最も)|(?:どの会社で|どの会社に|どこの会社|勤務先|勤め先)/.test(text);
 const unregisteredAudio=/イヤホン|earphones?|earbuds?|earpods?/i.test(text)&&!data.facts.some(f=>f.category==='earphones');
 const unregisteredSubscriptions=/サブスク|subscription|契約.*(?:サービス|有料)/i.test(text)&&!data.facts.some(f=>f.topic==='subscriptions');
 const unregisteredRunningDetail=/(?:ランニング|ジョギング|走る|走って|running|\brun\b).*(?:どこ|どちら|場所|コース|ルート|何キロ|距離|ペース|何時|時間|大会)|(?:どこ|どちら|場所|コース|ルート).*(?:走|ランニング|ジョギング|running|\brun\b)/.test(text);
 const unknown=unregisteredRunningDetail||unregisteredAudio||unregisteredSubscriptions||unsupportedSubject||unsupportedRank||data.unknownPatterns.some(pattern=>new RegExp(pattern,'i').test(text));
 if(unknown)return {factIds:[],topics:[],unknown:true};
 const entity=resolveEntities(text,data,context,matchesKeyword);
 if(entity)return {...entity,learningEligible:!follow&&!referenceLink&&!/^(?:それ|その|さっき|前に|前の)/.test(text)&&!entity.unknown};
 if(referenceLink){const facts=data.facts.filter(f=>context.lastFactIds.includes(f.id)&&f.url);return {factIds:facts.map(f=>f.id),topics:facts.map(f=>f.topic),unknown:!facts.length};}
 let search=text;
 const exclude=new Set();
 for(const f of data.facts)for(const alias of f.aliases||[]){
  const key=normalizeQuestion(alias);
  if(search.includes(key+'以外')||search.includes(key+'を除')||search.includes('except '+key)||search.includes('other than '+key)){
   exclude.add(f.id);search=search.replace(key+'以外','').replace(key+'を除いて','').replace('except '+key,'').replace('other than '+key,'');
  }
 }
 const topics=data.topics.map(t=>({id:t.id,score:t.keywords.reduce((n,k)=>n+(matchesKeyword(search,k)?Math.min(4,normalizeQuestion(k).length):0),0)})).filter(t=>t.score>0).sort((a,b)=>b.score-a.score).map(t=>t.id);
 const routes=data.routes.filter(r=>(r.keywords||[]).some(k=>matchesKeyword(search,k))||(r.matchPatterns||[]).some(p=>new RegExp(p,'i').test(search)));
 // Priority is local to a fact's subject, so a secondary-account request cannot suppress a separate hobby request.
 const ranked=new Map();
 for(const route of routes)for(const id of route.factIds){const f=data.facts.find(f=>f.id===id);if(!f)continue;ranked.set(f.topic,Math.max(ranked.get(f.topic)||0,route.priority||0));}
 const routed=new Set(routes.flatMap(r=>r.factIds.filter(id=>{const f=data.facts.find(f=>f.id===id);return f&&(r.priority||0)===(ranked.get(f.topic)||0);})));
 const targeted=data.facts.filter(f=>[...(f.aliases||[]),...(f.tags||[])].some(k=>matchesKeyword(search,k)));
 let selected=data.facts.filter(f=>routed.has(f.id));
 const routedTopics=new Set(selected.map(f=>f.topic));
 selected.push(...targeted.filter(f=>!routedTopics.has(f.topic)));
 const semantic=resolveSemanticIntent(search,context,targeted);
 const retrieval=semantic.priority<60&&!targeted.length?retrieveIntent(search):null;
 const learned=!follow&&!referenceLink&&semantic.priority<60&&!targeted.length&&!retrieval?context.learner?.retrieve(search):null;
 if(learned){semantic.factIds=learned.factIds;semantic.intent=learned.intent;semantic.priority=65;semantic.confidence=learned.confidence;}
 if(retrieval){semantic.factIds=retrieval.factIds;semantic.intent=retrieval.intent;semantic.priority=65;semantic.confidence=retrieval.confidence;}

 if(semantic.factIds.length&&(semantic.priority>=60||!selected.length||semantic.intent==='identity-overview'))selected=semantic.factIds.map(id=>data.facts.find(f=>f.id===id)).filter(Boolean);
 if(/以外/.test(text)&&/活動|趣味|何(?:を)?して/.test(text)){
  selected=data.facts.filter(f=>f.topic==='activities');
  const excludedText=text.slice(0,text.indexOf('以外'));
  for(const f of selected)if((f.aliases||[]).some(a=>matchesKeyword(excludedText,a)))exclude.add(f.id);
 }
 if(overview&&!selected.length)selected=data.facts.filter(f=>['name','student','workflow','tecirc','photo','running'].includes(f.id));
 if(follow&&!selected.length){
  const last=new Set(context.lastFactIds);
  const urls=/リンク|url|link/.test(text);
  selected=urls?data.facts.filter(f=>last.has(f.id)&&f.url):[];
  if(!urls){
   const other=/他|ほか|else/.test(text);
   const related=new Set(data.facts.filter(f=>last.has(f.id)).flatMap(f=>f.relatedFactIds||[]).filter(id=>context.lastFactIds.length===1||context.lastTopics.includes(data.facts.find(f=>f.id===id)?.topic)));
   let candidates=data.facts.filter(f=>other?context.lastTopics.includes(f.topic)&&!last.has(f.id):related.has(f.id));
   if(!candidates.length&&context.lastFactIds.length>1&&!other)candidates=data.facts.filter(f=>last.has(f.id));
   candidates.sort((a,b)=>(context.seen.get(a.id)||0)-(context.seen.get(b.id)||0));selected.push(...candidates.slice(0,3));
  }
 }
 // A bare topic keyword is not evidence for an arbitrary preference or product.
 if(!selected.length){
  for(const fallback of data.generalQuestions||[])if(new RegExp(fallback.pattern,'i').test(search))selected.push(...data.facts.filter(f=>fallback.factIds.includes(f.id)));
 }
 if(semantic.intent==='design-principles')selected=selected.filter(f=>f.ja.relation!=='interest');
 selected=selected.filter(f=>!exclude.has(f.id));
 if(!overview&&!['identity-overview','site-author'].includes(semantic.intent)&&!/名前|呼び|呼ん|呼べ|ニックネーム|name|nickname|何者|どんな人/.test(text)&&selected.length>1)selected=selected.filter(f=>f.id!=='name');
 if(/ヘッドホン|ヘッドフォン|headphone|愛用|愛用品|使って|持って/.test(text)&&!/興味|関心|好き|interest|like/.test(text))selected=selected.filter(f=>f.topic!=='interests');
 if(semantic.concepts.has('social')&&selected.some(f=>f.topic==='social')&&semantic.intent!=='identity-name')selected=selected.filter(f=>f.id!=='name');
 if(semantic.mode==='brief')selected=selected.slice(0,3);
 return {learningEligible:!follow&&!referenceLink&&!learned&&!retrieval&&semantic.priority>=60&&selected.length>0,learned:!!learned,factIds:[...new Set(selected.map(f=>f.id))],topics,unknown:!selected.length,intent:semantic.intent,mode:semantic.mode,confidence:semantic.confidence};
}
