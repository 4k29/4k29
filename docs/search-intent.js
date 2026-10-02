const weatherWords=/天気|てんき|天候|気温|きおん|降水|weather|temperature|傘(?:は|が|って)?(?:必要|いる)|雨(?:は|が|降)|あめ(?:は|が|ふる)/i;
const personal=/あなた|君|しかさん|4k29|僕|私|俺|趣味|好き|推し|契約|サブスク|イヤホン|ヘッドホン|サブ垢|アカウント|名前|誕生日|学校|本名|年齢|しゅみ|おし(?=は|が|を|の|って|について|だれ|誰|いる|$)|なまえ|いやほん|subscri|your|my\s+(?:name|hobbies|age|birthday)/i;
export function searchIntent(question,{forceSearch=false,pendingWeather=false,hasPlace=false}={}){
 const text=question.normalize('NFKC').trim();
 const explicit=/^(?:Google検索|グーグル検索|検索|けんさく|search|調べて|ググって)\s*[:：\s]|(?:を|について)(?:検索|けんさく|調べて|しらべて|ググって)|(?:検索|けんさく)して[？?。!]*$/i.test(text);
 const weather=!personal.test(text)&&(weatherWords.test(text)||((pendingWeather||hasPlace)&&/^(?:今日|きょう|明日|あした|明後日|あさって|今|いま|tomorrow|today)(?:は|の天気|のてんき)?[？?。!]*$/i.test(text)));
 if(weather||pendingWeather&&!explicit&&!personal.test(text)&&!forceSearch&&!/何|誰|どう|いつ|どこ|なに|だれ|who|what|why/i.test(text)){
  const datePattern=/(^|[\sのはで])(?:明後日|あさって|明日|あした|今日|きょう|現在(?!地)|今|いま|day after tomorrow|tomorrow|today)(?=の|は|で|天気|てんき|雨|あめ|weather|[\s？?。!]|$)/gi;
  const dates=[...text.matchAll(datePattern)].map(m=>m[0]);
  const day=dates.some(d=>/明後日|あさって|day after tomorrow/i.test(d))?2:dates.some(d=>/明日|あした|tomorrow/i.test(d))?1:0;
  const unsupported=/来週|来月|昨日|きのう|週間|一週間|週末|[0-9]+[日月]|next week|yesterday/i.test(text);
  const place=text.replace(datePattern,'$1')
   .replace(/(?:の)?(?:天気|てんき|天候|気温|きおん|降水確率|降水|weather|temperature)/gi,'')
   .replace(/(?:傘(?:は|が|って)?(?:必要|いる)|雨(?:は|が)?(?:降る|降ります|降りそう)|雨(?:は|が)|あめ(?:は|が|ふる))/g,'')
   .replace(/(?:を|について)?(?:教えて|おしえて|知りたい|調べて|しらべて|検索して|けんさくして)|(?:は|って)?(?:どう|どんな感じ|何度|なんど)|ですか|ますか/g,'')
   .replace(/(?:かな|かしら)[？?。!！]*$/,'')
   .replace(/\b(?:what(?:'s| is)?|is|the|like|in|for)\b/gi,'').replace(/[？?。!！]/g,'').trim().replace(/^(?:の|は|で|に|が|を)+|(?:の|は|で|に|が|を)+$/g,'').trim();
  const useLocation=/現在地|げんざいち|ここ|\bmy location\b|\bhere\b/i.test(text);
  return {kind:'weather',query:text,place:useLocation?'':place,day,explicitDay:dates.length>0,unsupported,useLocation};
 }
 if(forceSearch||explicit||!personal.test(text)&&/(?:今日|最新|現在|速報).*(?:ニュース|情報|価格|株価|為替)|(?:ニュース|株価|為替)(?:は|を|？|\?|$)/.test(text)){
  const query=text.replace(/^(?:Google検索|グーグル検索|検索|けんさく|search|調べて|ググって)\s*[:：\s]+/i,'').replace(/^(?:Googleで|グーグルで)/i,'').replace(/(?:を|について)(?:検索|けんさく|調べて|しらべて|ググって).*$/,'').replace(/(?:検索|けんさく)して[？?。!]*$/,'').trim();
  return {kind:'web',query:query||text,fresh:/今日|最新|現在|速報|ニュース|価格|株価|為替|発売|営業時間|最安|news|latest|price|today/i.test(text)};
 }
 return null;
}
export function webLinks(query){
 return [{label:'Googleで検索',url:'https://www.google.com/search?q='+encodeURIComponent(query)}];
}
