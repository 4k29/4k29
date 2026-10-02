import {searchIntent,webLinks} from './search-intent.js';
import {findPlaces,getWeather,locate,validPlace} from './search-services.js';
export class SearchController{
 constructor(services={}){this.services={findPlaces,getWeather,locate,...services};this.reset();}
 reset(){this.place=null;this.pendingWeather=false;this.day=0;}
 plan(question,{forceSearch=false,profileKnown=false}={}){
  const plan=searchIntent(question,{forceSearch,pendingWeather:this.pendingWeather&&!profileKnown,hasPlace:!!this.place});
  if(this.pendingWeather&&plan?.kind==='weather'&&!plan.explicitDay)plan.day=this.day;
  if(!plan)this.pendingWeather=false;
  return plan;
 }
 async execute(plan,action=null){
  if(action?.type==='geolocate'){
   this.day=[0,1,2].includes(action.day)?action.day:this.day;this.place=null;
   try{this.place=await this.services.locate();return await this.weather(this.day);}
   catch{this.pendingWeather=true;return {text:'現在地を取得できませんでした。位置情報は使わず、地域名で調べられます。「東京の天気」のように入力してください。',kind:'weather'};}
  }
  if(action?.type==='place'&&validPlace(action.place)){this.day=[0,1,2].includes(action.day)?action.day:this.day;this.place=action.place;return this.weather(this.day);}
  if(plan.kind==='weather'){
   this.day=plan.day;
   if(plan.unsupported)return {text:'このチャットで取得できるのは今日・明日・明後日の予報です。別の日付は検索先で確認してください。\nGoogleで検索',links:webLinks(plan.query||'天気予報'),kind:'weather'};
   if(plan.place){
    this.place=null;
    try{
     const places=await this.services.findPlaces(plan.place);
     if(!places.length){this.pendingWeather=true;return {text:`「${plan.place}」の地域が見つかりませんでした。市区町村名、または英字の地名で入力してください。`,kind:'weather'};}
     if(places.length>1){this.pendingWeather=true;return {text:'地域の候補が複数見つかりました。調べる場所を選んでください。',kind:'weather',actions:places.map(place=>({type:'place',place,day:this.day,label:[place.name,place.admin!==place.name?place.admin:'',place.country].filter(Boolean).join(' / ')}))};}
     this.place=places[0];
    }catch{return this.failure('地域情報',plan.place+' 天気');}
   }
   if(!this.place||plan.useLocation){this.pendingWeather=true;return {text:'どこの天気を調べますか？「東京の天気」のように地域名を入力できます。',kind:'weather',actions:[{type:'geolocate',day:this.day,label:'現在地を使う'}]};}
   return this.weather(this.day);
  }
  const query=plan.query;
  return {text:`Google検索：${query}\n${plan.fresh?'最新情報は検索先で確認できます。':'検索結果は別タブで開きます。'}\nGoogleで検索`,links:webLinks(query),kind:'web'};
 }

 async weather(day){this.pendingWeather=false;try{return await this.services.getWeather(this.place,day);}catch{return this.failure('天気',this.place.name+' 天気');}}
 failure(label,query){return {text:`${label}を取得できませんでした。時間をおいて試すか、検索先で確認してください。\nGoogleで検索`,links:webLinks(query),kind:'web'};}
}
