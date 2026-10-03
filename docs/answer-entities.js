// Resolve the requested entity type before falling back to the profile owner's name or a broad topic.
export function resolveEntities(text,data,context,matches){
 const facts=data.facts,has=(id)=>facts.find(f=>f.id===id);
 const result=(selected,intent,mode=null)=>({factIds:selected.map(f=>f.id),topics:[...new Set(selected.map(f=>f.topic))],unknown:!selected.length,intent,mode});
 const readArticle=/読(?:み|む|め)|記事|ブログ|notes?|執筆|\b(?:read|articles?|blog)\b/i.test(text);
 if(readArticle){
  const broad=new Set(['ai','生成ai','apple','iphone','テクノロジー','デザイン']);
  const articles=facts.filter(f=>f.ja.relation==='articleLink').map(f=>({fact:f,terms:(f.lookupTerms||[]).filter(term=>matches(text,term))})).filter(entry=>entry.terms.length);
  const specific=articles.filter(entry=>entry.terms.some(term=>!broad.has(term.normalize('NFKC').toLowerCase())));
  if(articles.length)return result((specific.length?specific:articles).map(entry=>entry.fact),'article-read');
  if(/記事|ブログ|\b(?:articles?|blog)\b/.test(text)&&/読|見たい|read|リンク|url/.test(text))return result(facts.filter(f=>f.id==='tecirc-link'),'article-link');
 }

 const favorite=has('favorite-person');
 const favoriteReference=context.lastFactIds.length===1&&context.lastFactIds[0]==='favorite-person'&&/^(?:their|his|her|that person's|what is (?:their|his|her))\b/.test(text);
 if((/推し|(?:好き|すき)な(?:人物|人|ひと)|してはる|shiteharu|\bfavou?rite (?:person|creator|youtuber)\b|\bwho (?:do you like|is your favou?rite)\b/.test(text)||favoriteReference)&&favorite)return {...result([favorite],'favorite-person',/youtube|ユーチューブ|ゆーちゅーぶ/i.test(text)?'favorite-youtube':/twitter|ツイッター|(?:^|[^a-z])x(?:$|[^a-z])/i.test(text)?'favorite-x':/だけ|only/.test(text)?'value-only':null),contextDependent:favoriteReference};
 if(/twitter|\bx\b|account/.test(text)){
  const main=/\b(?:main|primary)\b/.test(text),secondary=/\b(?:secondary|alt|alternate|second|backup)\b/.test(text);
  if(main||secondary)return result(facts.filter(f=>(main&&f.id==='x')||(secondary&&f.id==='x-secondary')),'social-account');
 }
 const subscriptions=facts.filter(f=>f.topic==='subscriptions');
 const explicitSubscriptions=subscriptions.filter(f=>(f.aliases||[]).some(a=>matches(text,a)));
 const subscriptionQuestion=/サブスク|subscri(?:ption|ptions|be|bed|bing)|(?:契約|課金|加入).*(?:サービス|プラン)|(?:サービス|プラン).*(?:契約|課金|加入)/i.test(text)||explicitSubscriptions.length;
 if(subscriptionQuestion){
  if(/ネットフリックス|ネトフリ|spotify|スポティファイ|netflix|amazon|アマゾン|アマプラ|disney|ディズニー|youtube|ユーチューブ|携帯|回線|モバイル/i.test(text))return result([],'unregistered-subscription');
  const named=subscriptions.filter(f=>matches(text,f.en.value.split(/[ +]/)[0]));
  return result(explicitSubscriptions.length?explicitSubscriptions:named.length?named:subscriptions,'subscriptions',/名前だけ|一覧だけ/.test(text)?'value-only':null);
 }
 const runningApp=/(?:ランニング|ジョギング|\b(?:run|runs|running|jogging)\b).*(?:アプリ|\bapps?\b)|\bapps?\b.*\b(?:run|runs|running|jogging)\b|\bnrc\b|nike run club|ナイキランクラブ|ないきらんくらぶ/.test(text);
 if(runningApp){if(/strava|ストラバ|ストラヴァ|adidas|アディダス|garmin|ガーミン|runkeeper/.test(text))return result([],'unregistered-running-app');return result(facts.filter(f=>f.category==='running-app'),'running-app');}
 const contextualRunning=context.lastFactIds.length===1&&context.lastFactIds[0]==='running'&&/^(?:それ(?:には|は)?|その時(?:は)?)?何(?:を)?使/.test(text);
 const runningGear=contextualRunning||/(?:ランニング|ジョギング|走る|走って|running|\brun\b)/.test(text)&&/何(?:を)?使|道具|装備|ギア|何(?:で|を)走|(?:what|which).*(?:use|gear|equipment)|gear|equipment/.test(text);
 if(runningGear&&!/靴|シューズ|履|\b(?:shoes?|sneakers?)\b/.test(text)){const gear=facts.filter(f=>['running-shoes','running-app'].includes(f.category));if(/アプリ|時計|ウォッチ|イヤホン|ヘッドホン|ウェア|服|スマホ|app|watch|earphones?|earbuds?|headphones?|clothes|clothing|phone|tracker/.test(text))return result([],'unregistered-running-gear');return {...result(gear,'running-gear'),contextDependent:contextualRunning};}
 const kind=/靴|シューズ|履(?:く|いて)|shoes?|sneakers?/i.test(text)?'running-shoes':/イヤホン|earphones?|earbuds?|earpods?/i.test(text)?'earphones':/ヘッドホン|ヘッドフォン|headphones?/i.test(text)?'headphones':null;
 if(kind){
  const products=facts.filter(f=>f.ja.relation==='product');
  const explicit=products.filter(f=>(f.aliases||[]).some(alias=>matches(text,alias)&&!/ヘッドホン|ヘッドフォン|イヤホン|愛用品|愛用製品|headphones?/i.test(alias)));
  const candidates=products.filter(f=>f.category===kind&&(!explicit.length||explicit.includes(f)));
  return result(candidates,kind,/名前だけ|名称だけ|機種だけ|only.*name/.test(text)?'value-only':null);
 }
 if(/^(?:それ|その|さっき|前に|前の|(?:those|these|that|it|they|their)\b|what (?:is|are) (?:they|that|it|their|those|these)\b)/.test(text)){
  const previous=facts.filter(f=>context.lastFactIds.includes(f.id));
  if(/名前|名称|機種(?:名)?|\bnames?\b|\bcalled\b/.test(text)){
   const entities=previous.filter(f=>['product','xMain','xSecondary','website','favorite','subscription'].includes(f.ja.relation));
   return {...result(entities,'entity-name','value-only'),contextDependent:true};
  }
  if(/url|リンク|\blink\b/.test(text))return result(previous.filter(f=>f.url),'entity-link',/だけ|only/.test(text)?'url-only':null);
 }
 return null;
}
