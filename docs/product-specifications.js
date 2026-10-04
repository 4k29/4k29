import {neuralModel as model} from './neural-model.js?v=20261004-transformer-5b';
import {neuralLogits} from './neural-inference.js?v=20261004-transformer-5b';
export const specificationMemory=model.specificationMemory;
export function unsupportedProductName(text){return /\bcmf\s*buds\s*(?:pro|2|plus)\b|\b(?:nothing\s*)?headphone\s*\(?\s*(?:a|[2-9]\d*|1\d+)\b|\bpowerbeats\s*fit\b/i.test(text);}
const recallCache=new Map();
export function recallSpecification(field,language='ja',kind='product'){
 const key=field.control+':'+language+':'+kind;if(recallCache.has(key))return recallCache.get(key);
 const tokens=[],context={language,kind,style:'friendly',specification:field.control};let ended=false;
 for(let step=0;step<model.config.context-5;step++){
  const logits=neuralLogits(context,tokens);let best=0;for(let i=1;i<logits.length;i++)if(logits[i]>logits[best])best=i;
  if(best===1){ended=true;break;}tokens.push(best);
 }
 const exact=ended&&JSON.stringify(tokens)===JSON.stringify(field.tokens[language]);
 const result={text:exact?tokens.map(id=>model.vocabulary[id]).join(''):typeof field[language]==='string'?field[language]:field[language].value,exact,tokens,method:exact?'learned-literal-recall':'verified-model-memory'};
 recallCache.set(key,result);return result;
}
const factId=(product,field)=>'specification:'+product.id+':'+field.key;
function specificationClause(product,field,value){
 const label=field.ja.label;
 switch(field.key){
  case 'driver':return value+'ドライバーを搭載';
  case 'bluetooth':return 'Bluetooth '+value+'に対応';
  case 'codecs':return '音声コーデックは'+value;
  case 'anc':return value.replace(/に対応$/,'')+'に対応';
  case 'resistance':return product.id==='headphones'?'防塵・防水性能は'+value:product.id==='earphones-cmf'?'イヤホン本体の防塵・防水性能は'+value.replace('イヤホン本体は',''):value.replace('イヤホン本体は','イヤホン本体の耐汗・耐水性能は').replace('ケースは','充電ケースは');
  case 'fast-charging':return value+'可能';
  case 'multipoint':return value==='対応'?'2台同時接続に対応':'2台同時接続は'+value;
  case 'weight':return '重さは'+value;
  case 'connection':return value+'で接続可能';
  case 'charging':return '充電端子は'+value;
  default:return label+'は'+value;
 }
}
// Compose verified values recalled by the Transformer into one paragraph per
// product. The design introduction is editorial text sourced in research/;
// it is not an additional numerical value or a claimed personal review.
export function specificationParagraph(facts,language='ja'){
 const product=specificationMemory.products.find(p=>p.id===facts[0].specification.product);
 const fields=facts.map(f=>product.fields.find(field=>field.key===f.specification.key));
 if(fields.length===1)return specificationSentence(product,fields[0],recallSpecification(fields[0],language).text,language);
 if(language==='en')return product.name+': '+fields.map(f=>f.en.label+': '+recallSpecification(f,'en').text).join('; ')+'.';
 const broad=fields.some(f=>f.key==='driver')&&fields.some(f=>f.key==='bluetooth');
 const intro=product.id==='headphones'&&broad?product.name+'はNothingのヘッドホンで、透明なイヤーカップとアルミを使ったデザインが特徴です。':'';
 const groups=[fields.filter(f=>!f.key.startsWith('battery-')),fields.filter(f=>f.key.startsWith('battery-'))].filter(g=>g.length);
 const sentences=[];
 for(const group of groups)for(let i=0;i<group.length;i+=4){
  const clauses=group.slice(i,i+4).map(f=>specificationClause(product,f,recallSpecification(f,'ja').text));
  const last=clauses.pop();
  const ending=/対応$/.test(last)?last+'しています':/搭載$/.test(last)?last+'しています':/可能$/.test(last)?last.replace(/可能$/,'できます'):/使える$/.test(last)?last.replace(/使える$/,'使えます'):last+'です';
  const connected=clauses.map(c=>/対応$/.test(c)?c+'し':/搭載$/.test(c)?c+'し':/可能$/.test(c)?c.replace(/可能$/,'でき'):c);
  sentences.push(connected.concat(ending).join('、')+'。');
 }
 return intro+(intro?'':product.name+'：')+sentences.join('');
}
function specificationSentence(product,field,value,language){
 if(language==='en')return product.name+' — '+field.en.label+': '+value+'.';
 const name=product.name;
 if(field.key==='resistance'&&product.id==='earphones-cmf')return name+'のイヤホン本体は'+value.replace('イヤホン本体は','')+'の防塵・防水性能に対応しています。';
 if(field.key==='resistance'&&product.id==='earphones-beats')return name+'の'+value.replace(/^イヤホン本体は(.+)、ケースは(.+)$/,'イヤホン本体は$1の耐汗・耐水性能に対応しています。ケースは$2です。');
 if(field.key==='anc'&&product.id==='earphones-beats')return name+'は'+value+'しています。';
 if(field.key==='fast-charging')return name+'は'+value+'できます。';
 if(field.key==='multipoint')return value==='対応'?name+'は2台同時接続に対応しています。':name+'の2台同時接続は'+value.replace(/使える$/,'使えます')+'。';
 return name+'の'+field.ja.label+'は'+value+'です。';
}
export function withProductSpecifications(data){
 const facts=data.facts.map(f=>{
  const description=specificationMemory?.descriptions.find(d=>d.id===f.id);if(!description)return f;
  const copy={...f};for(const language of ['ja','en'])copy[language]={...f[language],overview:{get brief(){return recallSpecification(description,language,'favorite').text;},get detail(){return recallSpecification(description,language,'favorite').text;}}};return copy;
 });
 for(const product of specificationMemory?.products||[])for(const field of product.fields){
  const fact={id:factId(product,field),topic:'product-specifications',specification:{product:product.id,key:field.key},category:product.category,ja:{relation:'knowledge',value:product.name},en:{relation:'knowledge',value:product.name},url:field.source.url,source:field.source};
  // Decode only fields that are requested. Exact values are checked against
  // the sourced memory bundled with the weights before displaying numbers.
  for(const language of ['ja','en'])for(const name of ['answer','detail'])Object.defineProperty(fact[language],name,{get(){return specificationSentence(product,field,recallSpecification(field,language).text,language);}});
  facts.push(fact);
 }
 return {...data,facts};
}
export function resolveProductSpecifications(text,data,context,matches){
 const trigger=/スペック|仕様|性能|バッテリー|電池|再生時間|何時間|防水|耐水|防塵|耐汗|ip[x\d]|bluetooth|ブルートゥース|コーデック|codec|ldac|aac|sbc|ドライバ|重さ|重量|何グラム|サイズ|寸法|容量|ストレージ|充電|ノイ(?:ズ)?キャン|anc|インピーダンス|何mm|接続|端子|解像度|fps|\b(?:specs?|specifications?|battery|waterproof|weight|charging|driver|storage|dimensions|playback)\b/i;
 if(!trigger.test(text))return null;
 const unknown=()=>({factIds:[],topics:[],unknown:true,intent:'unsupported-product-specification'});
 if(/買|購入|価格|値段|いくら|好きな理由|なぜ|どうして|感想|何年|何月|いつ|\b(?:bought|purchase|price|cost|why|review)\b/.test(text))return null;
 if(unsupportedProductName(text)||/powerbeats|airpods|sony|bose|ソニー|ボーズ|WH-/i.test(text))return unknown();
 const products=specificationMemory?.products||[],named=products.filter(p=>p.aliases.some(a=>matches(text,a)));
 let selected=named;
 if(!selected.length&&/イヤホン|ヘッドホン|ヘッドフォン|earbuds?|earphones?|headphones?/.test(text))selected=products.filter(p=>p.owner&&['earphones','headphones'].includes(p.category));
 if(!selected.length&&/^(?:それ|その|さっき|もっと|詳しく|(?:its|their|those|that|it)\b)/.test(text))selected=products.filter(p=>context.lastFactIds.includes(p.id)||context.lastFactIds.some(id=>id.startsWith('specification:'+p.id+':')));
 if(!selected.length)return null;
 if(/使って|持って|愛用|\b(?:use|own)\b/.test(text)&&selected.some(p=>!p.owner))return unknown();
 if(/ケース|charging case|\bcase\b/.test(text)&&/防水|耐水|防塵|耐汗|waterproof/.test(text)&&selected.some(p=>p.id!=='earphones-beats'))return unknown();
 const broad=/スペック|仕様|性能|\bspec/.test(text);
 const fields=[];
 for(const product of selected.sort((a,b)=>['earphones','headphones','brand'].indexOf(a.category)-['earphones','headphones','brand'].indexOf(b.category))){
  let keys=null;
  if(/バッテリー.*容量|電池.*容量|mah/i.test(text))keys=['battery-capacity'];
  else if(/バッテリー|電池|再生時間|何時間|battery|playback/.test(text)&&! /充電|charging/.test(text)){
   keys=product.fields.filter(f=>f.key.startsWith('battery-')&&f.key!=='battery-capacity').map(f=>f.key);
   const codec=/ldac/.test(text)?'LDAC':/aac/.test(text)?'AAC':null;
   const anc=/anc\s*(?:を|は|が)?\s*(?:オフ|off)|(?:anc|ノイ(?:ズ)?キャン).*切|ノイズキャンセリングオフ/.test(text)?'off':/anc\s*(?:を|は|が)?\s*(?:オン|on)|(?:anc|ノイ(?:ズ)?キャン).*有効|ノイズキャンセリングオン/.test(text)?'on':null;
   keys=keys.filter(key=>{const f=product.fields.find(f=>f.key===key);return (!codec||f.conditions?.codec===codec)&&(!anc||f.conditions?.anc===anc);});
  }else if(/防水|耐水|防塵|耐汗|ip[x\d]|waterproof/.test(text))keys=['resistance'];
  else if(/2台|二台|同時|multipoint|dual/.test(text))keys=['multipoint'];
  else if(/ワイヤレス充電|無線充電|wireless charging/.test(text))keys=['wireless-charging'];
  else if(/急速充電|fast charg/.test(text))keys=['fast-charging'];
  else if(/充電|charging/.test(text))keys=['charging','fast-charging','wireless-charging'];
  else if(/bluetooth|ブルートゥース/.test(text))keys=['bluetooth'];
  else if(/コーデック|codec|ldac|aac|sbc/.test(text))keys=['codecs'];
  else if(/ドライバ|driver|何mm/.test(text))keys=['driver'];
  else if(/重さ|重量|何グラム|weight/.test(text))keys=['weight'];
  else if(/サイズ|寸法|dimensions/.test(text))keys=['dimensions'];
  else if(/インピーダンス/.test(text))keys=['impedance'];
  else if(/解像度|fps|動画.*画質/.test(text))keys=['video-front','video-back'];
  else if(/ストレージ|容量|storage/.test(text))keys=['storage'];
  else if(/接続|端子/.test(text))keys=['connection','charging'];
  else if(/ノイ(?:ズ)?キャン|anc/.test(text))keys=['anc'];
  const values=product.fields.filter(f=>keys?keys.includes(f.key):broad&&(context.explanationRequested||/詳しく|詳細|detail/.test(text)||f.core));
  for(const field of values)fields.push(factId(product,field));
 }
 return fields.length?{factIds:fields,topics:['product-specifications'],unknown:false,intent:'product-specifications',mode:'knowledge',learningEligible:false}:unknown();
}
