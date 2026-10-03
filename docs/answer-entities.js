// Resolve the requested entity type before falling back to the profile owner's name or a broad topic.
export function resolveEntities(text,data,context,matches){
 const facts=data.facts,has=(id)=>facts.find(f=>f.id===id);
 const result=(selected,intent,mode=null)=>({factIds:selected.map(f=>f.id),topics:[...new Set(selected.map(f=>f.topic))],unknown:!selected.length,intent,mode});
 const favorite=has('favorite-person');
 if(/推し/.test(text)&&favorite)return result([favorite],'favorite-person',/だけ|only/.test(text)?'value-only':null);
 const subscriptions=facts.filter(f=>f.topic==='subscriptions');
 const explicitSubscriptions=subscriptions.filter(f=>(f.aliases||[]).some(a=>matches(text,a)));
 const subscriptionQuestion=/サブスク|subscription|(?:契約|課金|加入).*(?:サービス|プラン)|(?:サービス|プラン).*(?:契約|課金|加入)/i.test(text)||explicitSubscriptions.length;
 if(subscriptionQuestion){
  if(/ネットフリックス|ネトフリ|spotify|スポティファイ|netflix|amazon|アマゾン|アマプラ|disney|ディズニー|youtube|ユーチューブ|携帯|回線|モバイル/i.test(text))return result([],'unregistered-subscription');
  const named=subscriptions.filter(f=>matches(text,f.en.value.split(/[ +]/)[0]));
  return result(explicitSubscriptions.length?explicitSubscriptions:named.length?named:subscriptions,'subscriptions',/名前だけ|一覧だけ/.test(text)?'value-only':null);
 }
 const kind=/靴|シューズ|履(?:く|いて)|shoes?|sneakers?/i.test(text)?'running-shoes':/イヤホン|earphones?|earbuds?|earpods?/i.test(text)?'earphones':/ヘッドホン|ヘッドフォン|headphones?/i.test(text)?'headphones':null;
 if(kind){
  const products=facts.filter(f=>f.ja.relation==='product');
  const explicit=products.filter(f=>(f.aliases||[]).some(alias=>matches(text,alias)&&!/ヘッドホン|ヘッドフォン|イヤホン|愛用品|愛用製品|headphones?/i.test(alias)));
  const candidates=products.filter(f=>f.category===kind&&(!explicit.length||explicit.includes(f)));
  return result(candidates,kind,/名前だけ|名称だけ|機種だけ|only.*name/.test(text)?'value-only':null);
 }
 if(/^(?:それ|その|さっき|前に|前の)/.test(text)){
  const previous=facts.filter(f=>context.lastFactIds.includes(f.id));
  if(/名前|名称|機種(?:名)?|\bname\b/.test(text)){
   const entities=previous.filter(f=>['product','xMain','xSecondary','website','favorite','subscription'].includes(f.ja.relation));
   return result(entities,'entity-name','value-only');
  }
  if(/url|リンク|\blink\b/.test(text))return result(previous.filter(f=>f.url),'entity-link',/だけ|only/.test(text)?'url-only':null);
 }
 return null;
}
