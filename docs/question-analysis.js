import {resolveEntities} from './answer-entities.js?v=20261005-topic-language-1';
import {retrieveIntent} from './intent-retrieval.js?v=20261005-topic-language-1';
import {semanticText,resolveSemanticIntent} from './intent-model.js?v=20261005-topic-language-1';
import {resolveKnowledge} from './knowledge-retrieval.js?v=20261005-topic-language-1';
import {resolveProductSpecifications,unsupportedProductName} from './product-specifications.js?v=20261005-topic-language-1';
// Local retrieval only: query scopes and evidence come from the editable profile.
export function normalizeQuestion(text){return String(text).normalize('NFKC').toLowerCase().replace(/headphone\s*(?:\(\s*1\s*\)|1(?!\d))/g,'headphone (1)').replace(/[\s　]+/g,' ').trim();}
export function matchesKeyword(text,word){
 word=normalizeQuestion(word);
 if(word==='サブ'.toLowerCase())return /サブ(?:垢|アカ|のアカ|だけ|は|が|を|って|について|と|$)/i.test(text);
 if(word==='メイン'.toLowerCase())return /メイン(?:垢|アカ|のアカ|だけ|は|が|を|って|について|と|$)/i.test(text);
 return /^[a-z0-9_ ]+$/.test(word)?new RegExp(`(?:^|[^a-z0-9_])${word.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}(?:$|[^a-z0-9_])`,'i').test(text):text.includes(word);
}
const followOnly=/^(?:それ|その話|そのこと|それについて|その話について)?(?:を|は)?(?:もっと|詳しく|もう少し|他には|ほかには|他は|ほかは|続き|続けて|教えて|聞かせて|説明して|知りたい|お願い|お願いし?ます|について|何|は|\s|[?？!！。])*$/;
export function isFollowUp(text){return Boolean(text)&&((followOnly.test(text)&&/それ|その|もっと|詳しく|他|ほか|続|もう少し/.test(text))||/^(?:more|tell me more|anything else|what else|continue|details|about that)[?.!\s]*$/.test(text));}
function standalone(text,data){return data.facts.some(f=>[...(f.aliases||[]),...(f.tags||[])].some(k=>matchesKeyword(text,k)))||data.routes.some(r=>(r.keywords||[]).some(k=>matchesKeyword(text,k)))||data.unknownPatterns.some(p=>new RegExp(p,'i').test(text))||/趣味|興味|関心|メイン|サブ|hobb|interest/.test(text)||Boolean(resolveEntities(text,data,{lastFactIds:[]},matchesKeyword))||resolveSemanticIntent(text,{lastFactIds:[]}).factIds.length>0;}
function sharedScope(pieces){
 // Carry only an explicit domain/owner, never guess a missing product or preference.
 const running=pieces.find(p=>/ランニング|ジョギング|\b(?:running|jogging)\b/.test(p));
 const article=pieces.find(p=>/記事|ブログ|\b(?:articles?|blog|writing)\b/.test(p));
 const owner=pieces[0].match(/^(?:私|僕|俺|わたし|友達|友人|先生)の/)?.[0]||pieces[0].match(/^(?:(?:what|which)(?: is| are)?\s+|tell me (?:about )?)?(my\s+)/)?.[1];
 const productOwner=pieces[0].match(/^(.+?の)(?=イヤホン|ヘッドホン|ヘッドフォン|靴|シューズ)/)?.[1];
 const sharedNames=pieces.length>1&&pieces.slice(0,-1).every(p=>/^(?:好きな)?(?:イヤホン|ヘッドホン|ヘッドフォン|ドラマ|漫画|まんが|ブランド|サブスク)$/.test(p))?pieces.at(-1).match(/の((?:名前|名称|機種)(?:だけ(?:教えて)?))(?:$|[?？])/ )?.[1]:null;
 return pieces.map((p,index)=>{
  if(sharedNames&&index<pieces.length-1)p+='の'+sharedNames;
  if(running&&!/ランニング|ジョギング|\b(?:running|jogging)\b/.test(p)&&/^(?:何の|どの|what |which )?(?:アプリ|靴|シューズ|apps?\b|shoes?\b)/.test(p))p=(/[ぁ-んァ-ヶ一-龠]/.test(p)?'ランニングの':'running ')+p;
  if(article&&!/記事|ブログ|\b(?:articles?|blog|writing)\b/.test(p)&&/^(?:読む場所|読める場所|どこで読|内容|テーマ|where.*(?:read|find))/.test(p))p=(/[ぁ-んァ-ヶ一-龠]/.test(p)?'記事の':'articles ')+p;
  if(owner&&!p.startsWith(owner))p=owner+p;
  if(productOwner&&!p.startsWith(productOwner)&&/^(?:イヤホン|ヘッドホン|ヘッドフォン|靴|シューズ)/.test(p))p=productOwner+p;
  return p;
 });
}
export function splitQuestions(text,data){
 const sentences=text.split(/[?？!！。;；\n]+|、(?:あと|それから|それと)|\b(?:also|and then)\b/).map(s=>s.trim()).filter(Boolean);
 const result=[];
 for(const sentence of sentences){
  // Split coordinated requests only if both sides independently identify a subject.
  // Preserve lexical compounds such as 人とコンピューター.
  if(/以外|除いて|except|other than|おすすめ|お勧め|比較|違い|どっち|どちら|\b(?:recommend|compare|difference|better)\b/.test(sentence)){result.push(sentence);continue;}
  const pieces=sharedScope(sentence.split(/、|(?:それと|それから)|\s+and\s+|(?<!こ)と(?!き|ころ|して|いう|思|考)|や(?!って|る)/).map(p=>p.trim()).filter(Boolean));
  // A single registered entity may have a compound name (UIとUX, ChatGPTやCodex).
  const singleEntity=data.facts.some(f=>pieces.length>1&&pieces.every(p=>(f.aliases||[]).some(a=>{
   a=normalizeQuestion(a);
   return p.startsWith(a)&&/^(?:は|が|を|に)?(?:関心|興味|好き|ある|あるの|教えて|何|\s)*$/.test(p.slice(a.length));
  })));
  if(pieces.length>1&&!singleEntity&&pieces.every(p=>standalone(p,data)))result.push(...pieces);else result.push(sentence);
 }
 return result;
}
export function analyzeQuestion(text,data,context){
 if(unsupportedProductName(text)||/^[\d(+-].*[+\-*/].*[a-z_]\w*\s*[.(]/i.test(text))return {factIds:[],topics:[],unknown:true};
 if(/^(?:検索|けんさく|search)\s*[:：\s]|(?:を|について)(?:検索|けんさく|ググって)|(?:検索|けんさく)して|\bsearch (?:for|the web)\b/i.test(text))return {factIds:[],topics:[],unknown:true};
 text=semanticText(text);
 const knowledge=resolveKnowledge(text,data,context,matchesKeyword);if(knowledge)return knowledge;
 if(!/この(?:サイト|ページ|チャット)|自己紹介サイト|this (?:site|page|chat)/.test(text)&&(/web|ウェブ|ホームページ|website|サイト/.test(text)&&/開発|制作|作|build|make|develop/.test(text)||/^(?:web|ウェブ|website)$/.test(text)))return {factIds:[],topics:[],unknown:true};
 const historyReference=text.match(/^(最初|(?:[1-9][0-9]*)つ前|(?:[1-9][0-9]*)回前)の(?:話|質問|回答|答え)(?:について)?(?:もう一度|もう一回|詳しく|教えて|は|を|何|\s)*$/);
 if(historyReference){
  const index=historyReference[1]==='最初'?0:context.history.length-Number.parseInt(historyReference[1],10);
  const entry=context.history[index];const ids=entry?.factIds||[];
  return {factIds:ids,topics:entry?.topics||[],unknown:!ids.length};
 }
 const referenceLink=/^(?:それ|その|さっき|前の).*(?:リンク|url|link)/.test(text);
 const follow=isFollowUp(text),overview=/^(?:こんにちは|こんばんは|おはよう|やあ|よろしく|hello|hi|hey|自己紹介(?:して)?|紹介して|あなたについて(?:教えて)?|どんな人(?:ですか)?|about you|introduce yourself)[!！?？。\s]*$/.test(text);
 const unsupportedSubject=/(?:私|僕|俺|わたし|友達|友人|先生)(?:の|が|は).*(?:名前|趣味|職業|興味|仕事|イヤホン|ヘッドホン|ヘッドフォン|サブスク|契約|推し|好きな(?:もの|物|漫画|まんが|ドラマ|ブランド|メーカー)|耳に|耳を)|\b(?:my|(?:my )?(?:friend|teacher)'s) (?:name|job|hobbies|interests|earphones|earbuds|headphones|subscriptions|favou?rite (?:person|things|brands?|manga|dramas?|tv shows?)|account)\b/.test(text);
 const unsupportedRank=/(?:一番|いちばん|最も|一位|ランキング).*(?:好き|興味|関心|大切|重視)|(?:好き|興味|大切).*(?:一番|最も)|(?:どの会社で|どの会社に|どこの会社|勤務先|勤め先)/.test(text);
 const unregisteredAudio=/イヤホン|ヘッドホン|ヘッドフォン|earphones?|earbuds?|earpods?|headphones?/i.test(text)&&!data.facts.some(f=>['earphones','headphones'].includes(f.category));
 const unregisteredSubscriptions=/サブスク|subscription|契約.*(?:サービス|有料)/i.test(text)&&!data.facts.some(f=>f.topic==='subscriptions');
 const unregisteredRunningDetail=/(?:ランニング|ジョギング|走る|走って|running|\brun\b).*(?:どこ|どちら|場所|コース|ルート|何キロ|距離|ペース|何時|時間|大会)|(?:どこ|どちら|場所|コース|ルート).*(?:走|ランニング|ジョギング|running|\brun\b)/.test(text);
 const unsupportedEnglishPreference=/\b(?:like|love|enjoy|favou?rite|prefer)\b/.test(text)&&/\b(?:food|music|songs?|movies?|anime|games?|books?|sports?|drinks?|cars?)\b/.test(text)&&!/\b(?:article|articles|blog)\b/.test(text);
 const unknownCompany=/^(?:what (?:is|are)|who founded) (?:openai|apple|nothing)(?: (?:company|inc))?$/.test(text);
 const ownYouTube=/youtube|ユーチューブ|ゆーちゅーぶ/.test(text)&&/アカウント|チャンネル|\bid\b|account|channel|url|リンク/.test(text)&&!/推し|(?:好き|すき)な(?:人|ひと)|してはる|shiteharu|記事|ブログ|favou?rite (?:person|creator|youtuber)/.test(text)&&!(context.lastFactIds.includes('favorite-person')&&/^(?:それ|その|さっき|(?:their|his|her|that person's|what is (?:their|his|her))\b)/.test(text));
 const missingAttribute=/(?:どこ|どちら|どの店|どのお店).*(?:買|購入)|(?:買|購入).*(?:場所|店)|\bwhere\b.*\b(?:buy|bought|purchase|purchased)\b|\bhow often\b|週に何|月に何/.test(text);
 const productMaker=/メーカー|製造元|\b(?:manufacturer|brand)\b/.test(text)&&(/イヤホン|ヘッドホン|靴|シューズ|earbuds?|earphones?|headphones?|shoes?/.test(text)||/^(?:それ|その|さっき|their\b|its\b)/.test(text));
 if(!unsupportedSubject&&!missingAttribute&&!unsupportedRank){const specs=resolveProductSpecifications(text,data,context,matchesKeyword);if(specs)return specs;}
 // The newly registered manga category now has a grounded answer. Other
 // unsupported genres and personal attributes keep their existing guards.
 text=text.replace(/どうして(?:る|いる|います)/g,'どうやってしてる');
 const patternText=data.facts.some(f=>f.favoriteCategory==='manga')?text.replace(/好きな(?:漫画|まんが)/g,'好きな作品'):text;
 const unknown=missingAttribute||productMaker||unsupportedEnglishPreference||unknownCompany||ownYouTube||unregisteredRunningDetail||unregisteredAudio||unregisteredSubscriptions||unsupportedSubject||unsupportedRank||data.unknownPatterns.some(pattern=>new RegExp(pattern,'i').test(patternText));
 if(unknown)return {factIds:[],topics:[],unknown:true};
 const entity=resolveEntities(text,data,context,matchesKeyword);
 if(entity)return {...entity,learningEligible:!follow&&!referenceLink&&!/^(?:それ|その|さっき|前に|前の)/.test(text)&&!entity.unknown&&!entity.contextDependent};
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
 const targeted=data.facts.filter(f=>f.topic!=='general-knowledge'&&[...(f.aliases||[]),...(f.tags||[])].some(k=>matchesKeyword(search,k)));
 let selected=data.facts.filter(f=>routed.has(f.id));
 const routedTopics=new Set(selected.map(f=>f.topic));
 selected.push(...targeted.filter(f=>!routedTopics.has(f.topic)));
 const semantic=resolveSemanticIntent(search,context,targeted);
 const retrieval=semantic.priority<60&&!targeted.length?retrieveIntent(search):null;
 const learned=!follow&&!referenceLink&&semantic.priority<60&&!targeted.length&&!retrieval?context.learner?.retrieve(search):null;
 if(learned){semantic.factIds=learned.factIds;semantic.intent=learned.intent;semantic.priority=65;semantic.confidence=learned.confidence;}
 if(retrieval){semantic.factIds=retrieval.factIds;semantic.intent=retrieval.intent;semantic.priority=65;semantic.confidence=retrieval.confidence;}

 if(semantic.factIds.length&&(semantic.priority>=60||!selected.length||semantic.intent==='identity-overview'))selected=semantic.factIds.map(id=>data.facts.find(f=>f.id===id)).filter(Boolean);
 if(/以外/.test(text)&&(/活動|趣味|何(?:を)?して/.test(text)||context.lastModes?.includes('hobbies'))){
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
 if((/趣味|\bhobb(?:y|ies)\b|for fun|free time/.test(text)||context.lastModes?.includes('hobbies')&&(follow||/以外/.test(text)))&&selected.some(f=>f.ja.relation==='activity')){
  selected=selected.filter(f=>f.id!=='tecirc');semantic.mode='hobbies';
 }
 return {learningEligible:!follow&&!referenceLink&&!/^(?:それ|その|さっき|前に|前の)/.test(text)&&!learned&&!retrieval&&semantic.priority>=60&&selected.length>0,learned:!!learned,factIds:[...new Set(selected.map(f=>f.id))],topics,unknown:!selected.length,intent:semantic.intent,mode:semantic.mode,confidence:semantic.confidence};
}
