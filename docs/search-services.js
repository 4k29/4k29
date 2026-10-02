import {placeQuery} from './weather-places.js';
export async function fetchJSON(url,{fetcher=globalThis.fetch,timeout=10000}={}){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),timeout);
 try{const response=await fetcher(url,{signal:controller.signal,credentials:'omit',referrerPolicy:'no-referrer'});if(!response.ok)throw Error('HTTP '+response.status);return await response.json();}finally{clearTimeout(timer);}
}
export function validPlace(place){return place&&Number.isFinite(place.latitude)&&Math.abs(place.latitude)<=90&&Number.isFinite(place.longitude)&&Math.abs(place.longitude)<=180&&typeof place.name==='string';}
export async function findPlaces(name,options){
 const query=placeQuery(name),url=new URL('https://geocoding-api.open-meteo.com/v1/search');
 url.search=new URLSearchParams({name:query.name,count:'5',language:'ja',format:'json'});
 const data=await fetchJSON(url,options);let places=(data.results||[]).filter(validPlace);
 if(query.japanese&&places.some(p=>p.country_code==='JP'))places=places.filter(p=>p.country_code==='JP');
 if(query.japanese){const normalized=name=>name.replace(/[都道府県市区町村]+$/,'');const exact=places.filter(p=>normalized(p.name)===normalized(query.exactName));if(exact.length)places=exact;}
 return places.map(p=>({name:p.name,latitude:p.latitude,longitude:p.longitude,admin:p.admin1||'',country:p.country||'',geocoding:true}));
}
const codes=new Map([[0,'快晴'],[1,'晴れ'],[2,'晴れ時々曇り'],[3,'曇り'],[45,'霧'],[48,'着氷性の霧'],[51,'弱い霧雨'],[53,'霧雨'],[55,'強い霧雨'],[56,'弱い凍る霧雨'],[57,'強い凍る霧雨'],[61,'弱い雨'],[63,'雨'],[65,'強い雨'],[66,'弱い凍る雨'],[67,'強い凍る雨'],[71,'弱い雪'],[73,'雪'],[75,'強い雪'],[77,'雪粒'],[80,'弱いにわか雨'],[81,'にわか雨'],[82,'激しいにわか雨'],[85,'弱いにわか雪'],[86,'強いにわか雪'],[95,'雷雨'],[96,'雹を伴う雷雨'],[99,'強い雹を伴う雷雨']]);
export function weatherCode(code){return codes.get(code)||'Unknown';}
const metric=(n,suffix)=>typeof n==='number'&&Number.isFinite(n)?n+suffix:'Unknown';
export function formatWeather(data,place,day,now=new Date()){
 const daily=data.daily,i=day,date=daily?.time?.[i];
 if(!/^\d{4}-\d{2}-\d{2}$/.test(date||''))throw Error('forecast unavailable');
 const label=['今日','明日','明後日'][day],area=[place.name,place.admin&&place.admin!==place.name?place.admin:'',place.country].filter(Boolean).join(' / ');
 let text=`${area}\n${label}（${date}）の予報：${weatherCode(daily.weather_code?.[i])}\n最高 ${metric(daily.temperature_2m_max?.[i],'°C')} / 最低 ${metric(daily.temperature_2m_min?.[i],'°C')}\n降水確率（1日の最大）：${metric(daily.precipitation_probability_max?.[i],'%')}`;
 if(day===0&&data.current&&typeof data.current.time==='string')text+=`\n現在の推定：${weatherCode(data.current.weather_code)} / ${metric(data.current.temperature_2m,'°C')}（${data.current.time.replace('T',' ')}）`;
 text+=`\n地域のタイムゾーン：${data.timezone||'Unknown'}\n取得：${now.toLocaleString('ja-JP')}\n出典：Open-Meteo（予報・モデル推定。実測や確定情報ではありません）`;
 const links=[{label:'Open-Meteo',url:'https://open-meteo.com/'}];
 if(place.geocoding){text+='\n地域情報：GeoNames';links.push({label:'GeoNames',url:'https://www.geonames.org/'});}
 return {text,links,kind:'weather'};
}
export async function getWeather(place,day,options){
 if(!validPlace(place)||![0,1,2].includes(day))throw Error('invalid forecast request');
 const url=new URL('https://api.open-meteo.com/v1/forecast');url.search=new URLSearchParams({latitude:String(place.latitude),longitude:String(place.longitude),current:'temperature_2m,weather_code',daily:'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max',forecast_days:'3',timezone:'auto',temperature_unit:'celsius'});
 return formatWeather(await fetchJSON(url,options),place,day);
}
export function locate(geolocation=globalThis.navigator?.geolocation){
 return new Promise((resolve,reject)=>{
  if(!geolocation){reject(Error('location unavailable'));return;}
  geolocation.getCurrentPosition(position=>{
   const place={name:'現在地付近',latitude:Math.round(position.coords.latitude*100)/100,longitude:Math.round(position.coords.longitude*100)/100};
   if(!validPlace(place)){reject(Error('invalid location'));return;}resolve(place);
  },reject,{enableHighAccuracy:false,timeout:10000,maximumAge:300000});
 });
}
