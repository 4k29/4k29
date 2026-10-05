// Resolve the requested entity type before falling back to the profile owner's name or a broad topic.
export function resolveEntities(text,data,context,matches){
 const facts=data.facts,has=(id)=>facts.find(f=>f.id===id),previous=facts.filter(f=>context.lastFactIds.includes(f.id));
 const result=(selected,intent,mode=null)=>({factIds:selected.map(f=>f.id),topics:[...new Set(selected.map(f=>f.topic))],unknown:!selected.length,intent,mode});
 const readArticle=/読(?:み|む|め)|記事|ブログ|notes?|執筆|\b(?:read|articles?|blog)\b/i.test(text);
 if(readArticle){
  if(previous.length&&previous.every(f=>['tecirc','tecirc-subjects','tecirc-link'].includes(f.id)||f.ja.relation==='articleLink')&&/^(?:どこ(?:で|から)読(?:める|む)(?:の|か|ですか)?|where can i read(?: it| them| that)?|where (?:can i )?find (?:it|them|that))$/.test(text)){
   const articles=previous.filter(f=>f.ja.relation==='articleLink');
   return {...result(articles.length?articles:facts.filter(f=>f.id==='tecirc-link'),articles.length?'article-read':'article-link'),contextDependent:true};
  }
  const broad=new Set(['ai','生成ai','apple','iphone','テクノロジー','デザイン']);
  const articles=facts.filter(f=>f.ja.relation==='articleLink').map(f=>({fact:f,terms:(f.lookupTerms||[]).filter(term=>matches(text,term))})).filter(entry=>entry.terms.length);
  const specific=articles.filter(entry=>entry.terms.some(term=>!broad.has(term.normalize('NFKC').toLowerCase())));
  if(articles.length)return result((specific.length?specific:articles).map(entry=>entry.fact),'article-read');
  if(/記事|ブログ|\b(?:articles?|blog)\b/.test(text)&&/読|見たい|read|リンク|url/.test(text))return result(facts.filter(f=>f.id==='tecirc-link'),'article-link');
 }

 const favorite=has('favorite-person');
 const liked=facts.filter(f=>f.ja.relation==='favoriteThing');
 const favoriteProducts=/使って|使う|持って|購入|買った|愛用|\b(?:use|using|own|bought|purchase)\b/;
 const missingFavoriteDetail=/続編|結末|最終回|何話|何巻|何回|何年|何月|どこで見|好きな理由|なぜ|どうして|感想|キャスト|ジャンル|最新|配信|発売|\b(?:episodes?|ending|spoilers?|latest|release|why|review|genre|cast)\b/;
 const namedLikes=liked.filter(f=>(f.aliases||[]).some(alias=>matches(text,alias)));
 if(namedLikes.length){
  const field=/主演|\b(?:star|starring|lead actor)\b/.test(text)?'actor':/主人公|\bprotagonist\b/.test(text)?'protagonist':null;
  if(field&&!namedLikes.every(f=>f.publicDetails?.[field]))return result([],'unregistered-favorite-detail');
  if(field&&namedLikes.every(f=>f.publicDetails?.[field]))return result(namedLikes,'favorite-public-detail','favorite-'+field);
  if(favoriteProducts.test(text)||missingFavoriteDetail.test(text)||/作者|\bauthor\b/.test(text)&&namedLikes.some(f=>!f.publicInfo?.author))return result([],'unregistered-favorite-detail');
  if(/リンク|url|\blink\b/.test(text))return result(namedLikes.filter(f=>f.url),'favorite-source',/だけ|only/.test(text)?'url-only':null);
  return result(namedLikes,'liked-things',/名前だけ|名称だけ|only.*name/.test(text)?'value-only':'favorite-detail');
 }
 const previousLikes=previous.filter(f=>f.ja.relation==='favoriteThing');
 if(previousLikes.length&&/^(?:それ|その(?:作品|ブランド|漫画|ドラマ))(?:を|について|は)?$/.test(text))return {...result(previousLikes,'liked-things','favorite-detail'),contextDependent:true};
 if(previousLikes.length&&/^(?:それ|その(?:作品|ブランド|漫画|ドラマ)|もう少し|もっと)?(?:を|について)?(?:詳しく|どんなもの|説明して|教えて)|^(?:tell me more|more detail|describe (?:it|them))$/.test(text))return {...result(previousLikes,'liked-things','favorite-detail'),contextDependent:true};
 if(/(?:好き|お気に入り).*(?:作品)|(?:作品).*(?:好き|お気に入り)/.test(text))return result(liked.filter(f=>['drama','manga'].includes(f.favoriteCategory)),'liked-things','value-only');
 const category=/漫画|まんが|マンガ|\bmanga\b/.test(text)?'manga':/ドラマ|\b(?:dramas?|tv shows?)\b/.test(text)?'drama':/ブランド|メーカー|\b(?:brands?|manufacturers?)\b/.test(text)&&/好き|興味|関心|お気に入り|\b(?:like|interest|favou?rite)\b/.test(text)?'brand':null;
 const namedBrands=category==='brand'?facts.filter(f=>['apple','nothing','openai'].includes(f.id)&&(f.aliases||[]).some(alias=>matches(text,alias))):[];
 if(namedBrands.length)return result(namedBrands,'interest-entity','value-only');
 if(category&&(/好き|お気に入り|何|どれ|名前|名称|興味|関心|見る|観る|見て|ハマ|はま|\b(?:like|favou?rite|what|which|names?)\b/.test(text)||/^(?:漫画|まんが|ドラマ|manga|dramas?)(?:は|を|について|教えて|\s)*$/.test(text)))return result([...facts.filter(f=>category==='brand'&&['apple','nothing','openai'].includes(f.id)),...liked.filter(f=>f.favoriteCategory===category)],'liked-things','value-only');
 if(/(?:好き|すき)な(?:もの|物)|何(?:が|を)好き|お気に入りのもの|\bfavou?rite things\b|\bwhat (?:do you|are your) (?:like|love|favou?rites)\b/.test(text)&&!/分野|メーカー|ブランド|\b(?:field|brand|company)\b/.test(text))return result([...facts.filter(f=>f.ja.relation==='interest'&&!f.interestOnly),...liked,...(favorite?[favorite]:[])],'liked-things','value-only');
 const personReference=/^(?:その人|そのひと|その推し|その好きな人)|^(?:their|his|her|that person's|what is (?:their|his|her))\b/.test(text);
 const favoriteReference=context.lastFactIds.length===1&&context.lastFactIds[0]==='favorite-person'&&personReference;
 if(personReference&&!favoriteReference)return {...result([],'unknown-person-reference'),contextDependent:true};
 if((/推し|(?:好き|すき)な(?:人物|人|ひと)|してはる|shiteharu|\bfavou?rite (?:person|creator|youtuber)\b|\bwho (?:do you like|is your favou?rite)\b/.test(text)||favoriteReference)&&favorite)return {...result([favorite],'favorite-person',/youtube|ユーチューブ|ゆーちゅーぶ/i.test(text)?'favorite-youtube':/twitter|ツイッター|(?:^|[^a-z])x(?:$|[^a-z])/i.test(text)?'favorite-x':/だけ|only/.test(text)?'value-only':null),contextDependent:favoriteReference};
 if(/twitter|\bx\b|account/.test(text)){
  const main=/\b(?:main|primary)\b/.test(text),secondary=/\b(?:secondary|alt|alternate|second|backup)\b/.test(text);
  if(main||secondary)return result(facts.filter(f=>(main&&f.id==='x')||(secondary&&f.id==='x-secondary')),'social-account');
 }
 const subscriptions=facts.filter(f=>f.topic==='subscriptions');
 if(/^(?:名前|名称|機種(?:名)?|(?:the )?names?)(?:だけ(?:教えて)?| only| only please)$/.test(text)&&previous.length&&previous.every(f=>['product','xMain','xSecondary','website','favorite','favoriteThing','subscription'].includes(f.ja.relation)))return {...result(previous,'entity-name','value-only'),contextDependent:true};
 const explicitSubscriptions=subscriptions.filter(f=>(f.aliases||[]).some(a=>matches(text,a)));
 const subscriptionQuestion=/有料プラン|有料サービス|入って(?:る|いる).*プラン|サブスク|subscri(?:ption|ptions|be|bed|bing)|(?:契約|課金|加入).*(?:サービス|プラン)|(?:サービス|プラン).*(?:契約|課金|加入)/i.test(text)||explicitSubscriptions.length;
 if(subscriptionQuestion){
  if(/ネットフリックス|ネトフリ|spotify|スポティファイ|netflix|amazon|アマゾン|アマプラ|disney|ディズニー|youtube|ユーチューブ|携帯|回線|モバイル/i.test(text))return result([],'unregistered-subscription');
  const named=subscriptions.filter(f=>matches(text,f.en.value.split(/[ +]/)[0]));
  return result(explicitSubscriptions.length?explicitSubscriptions:named.length?named:subscriptions,'subscriptions',/名前だけ|一覧だけ/.test(text)?'value-only':null);
 }
 const contextualApp=previous.length>0&&previous.every(f=>['running','running-shoes','running-app'].includes(f.id))&&/^(?:(?:それ|その時)(?:の|は|に使う)?)?(?:アプリ(?:は|を|何|教えて|使ってる|\s)*|(?:what|which) app(?: do you use)?)$/.test(text);
 const runningApp=contextualApp||/(?:ランニング|ジョギング|走る).*(?:記録|管理).*(?:どう|何|して)|(?:ランニング|ジョギング|走る).*(?:記録|管理).*(?:してる|する|している)|(?:ランニング|ジョギング|走る).*(?:どう|何).*(?:記録|管理)/.test(text)||/(?:ランニング|ジョギング|走る|走って|\b(?:run|runs|running|jogging)\b).*(?:アプリ|\bapps?\b)|\bapps?\b.*\b(?:run|runs|running|jogging)\b|\bnrc\b|nike run club|ナイキランクラブ|ないきらんくらぶ/.test(text);
 if(runningApp){if(/strava|ストラバ|ストラヴァ|adidas|アディダス|garmin|ガーミン|runkeeper/.test(text))return result([],'unregistered-running-app');return {...result(facts.filter(f=>f.category==='running-app'),'running-app'),contextDependent:contextualApp};}
 const contextualRunning=context.lastFactIds.length===1&&context.lastFactIds[0]==='running'&&/^(?:それ(?:には|は)?|その時(?:は)?)?何(?:を)?使/.test(text);
 const runningGear=contextualRunning||/(?:ランニング|ジョギング|走る|走って|running|\brun\b)/.test(text)&&/何(?:を)?使|道具|装備|ギア|何(?:で|を)走|(?:what|which).*(?:use|gear|equipment)|gear|equipment/.test(text);
 if(runningGear&&!/靴|シューズ|履|\b(?:shoes?|sneakers?)\b/.test(text)){const gear=facts.filter(f=>['running-shoes','running-app'].includes(f.category));if(/アプリ|時計|ウォッチ|イヤホン|ヘッドホン|ウェア|服|スマホ|app|watch|earphones?|earbuds?|headphones?|clothes|clothing|phone|tracker/.test(text))return result([],'unregistered-running-gear');return {...result(gear,'running-gear'),contextDependent:contextualRunning};}
 const kind=/靴|シューズ|履(?:く|いて)|shoes?|sneakers?/i.test(text)?'running-shoes':/音楽.*(?:聴く|聞く).*(?:機器|道具|使|何で)|音を(?:聴く|聞く)機器|イヤホン|耳(?:に|へ)(?:入れ|つけ|着け)|earphones?|earbuds?|earpods?/i.test(text)?'earphones':/ヘッドホン|ヘッドフォン|耳(?:を|全体を)(?:覆|おお)|headphones?|愛用品|愛用製品|愛用しているもの|お気に入りの(?:製品|ガジェット)|普段使っているもの|よく使って(?:る|いる)ガジェット/i.test(text)?'headphones':null;
 if(kind){
  const products=facts.filter(f=>f.ja.relation==='product');
  const explicit=products.filter(f=>matches(text,f.en.value.split(' ')[0])||(f.category!=='headphones'&&(f.aliases||[]).some(alias=>matches(text,alias)&&!/イヤホン|愛用品|愛用製品/i.test(alias)))||(f.category==='headphones'&&(matches(text,'ナッシング')||matches(text,'headphone (1)'))));
  const categories=kind==='running-shoes'?[kind]:['earphones','headphones'];
  const candidates=products.filter(f=>categories.includes(f.category)&&(!explicit.length||explicit.includes(f)));
  return result(candidates,kind,/名前だけ|名称だけ|機種だけ|only.*name/.test(text)?'value-only':null);
 }
 if(/^(?:それ|その|さっき|前に|前の|(?:those|these|that|it|they|their)\b|what (?:is|are) (?:they|that|it|their|those|these)\b)/.test(text)){
  const previous=facts.filter(f=>context.lastFactIds.includes(f.id));
  if(/名前|名称|機種(?:名)?|\bnames?\b|\bcalled\b/.test(text)){
   const entities=previous.filter(f=>['product','xMain','xSecondary','website','favorite','favoriteThing','subscription'].includes(f.ja.relation));
   return {...result(entities,'entity-name','value-only'),contextDependent:true};
  }
  if(/url|リンク|\blink\b/.test(text))return result(previous.filter(f=>f.url),'entity-link',/だけ|only/.test(text)?'url-only':null);
 }
 return null;
}
