// Detect only identifiers the browser exposes. No device fingerprinting or external requests.
const UNKNOWN='Unknown';
const first=(value)=>typeof value==='string'&&value.trim()?value.trim():'';
function parseAgent(agent){
 const ua=first(agent);let os='',version='',device='',browser='';let match;
 if((match=ua.match(/\b(?:iPhone|iPad|iPod)\b/))){
  os=match[0]==='iPad'?'iPadOS':'iOS';device=match[0];version=ua.match(/(?:CPU(?: iPhone)? OS|iPhone OS) ([\d_]+)/)?.[1]?.replaceAll('_','.')||'';
 }else if((match=ua.match(/\bAndroid(?: ([\d.]+))?/))){
  os='Android';version=match[1]||'';device=/\bMobile\b/.test(ua)?'Mobile (browser-reported)':'';
 }else if((match=ua.match(/\bCrOS [\w]+ ([\d.]+)/))){os='ChromeOS';version=match[1];device='Non-mobile (browser-reported)';}
 else if((match=ua.match(/\bWindows NT ([\d.]+)/))){
  os='Windows';version=({'6.1':'7','6.2':'8','6.3':'8.1'})[match[1]]||'';
  // NT 10.0 is shared by Windows 10 and 11; do not invent the actual version.
  device='Non-mobile (browser-reported)';
 }else if((match=ua.match(/\bMac OS X(?: ([\d_\.]+))?/))){os='macOS';version=match[1]?.replaceAll('_','.')||'';device='Non-mobile (browser-reported)';}
 else if(/\b(?:Linux|X11)\b/.test(ua)){os='Linux';device='Non-mobile (browser-reported)';}
 // Chromium-based browsers must be matched before the generic Chrome/Safari tokens.
 const browsers=[['Edge',/\b(?:Edg|EdgA|EdgiOS)\/([\d.]+)/],['Opera',/\b(?:OPR|OPiOS)\/([\d.]+)/],['Samsung Internet',/\bSamsungBrowser\/([\d.]+)/],['Firefox',/\b(?:Firefox|FxiOS)\/([\d.]+)/],['Chrome',/\b(?:HeadlessChrome|Chrome|CriOS)\/([\d.]+)/],['Safari',/\bVersion\/([\d.]+).*\bSafari\//]];
 for(const [name,pattern] of browsers){const found=ua.match(pattern);if(found){browser=`${name} ${found[1]}`;break;}}
 return {os,version,device,browser};
}
function hintBrowser(hints,entropy){
 const list=Array.isArray(entropy?.fullVersionList)&&entropy.fullVersionList.length?entropy.fullVersionList:hints?.brands;
 if(!Array.isArray(list))return '';
 const brands=list.filter(b=>first(b?.brand)&&b.brand.replace(/[^a-z]/gi,'').toLowerCase()!=='notabrand');
 const preferred=brands.find(b=>b.brand!=='Chromium')||brands[0];
 if(!preferred)return '';
 const name=({'Google Chrome':'Chrome','Microsoft Edge':'Edge'})[preferred.brand]||preferred.brand;
 return name+(first(preferred.version)?' '+preferred.version:'');
}
export function deviceInfo(nav=navigator,screenInfo=screen,viewport=window,entropy={}){
 const hints=nav.userAgentData,parsed=parseAgent(nav.userAgent);
 const platform=first(hints?.platform)||first(entropy?.platform);
 const platformNames={macOS:'macOS',Windows:'Windows',Android:'Android',iOS:'iOS','Chrome OS':'ChromeOS',ChromeOS:'ChromeOS',Linux:'Linux'};
 let os=platformNames[platform]||platform||parsed.os;
 // navigator.platform is a final fallback; it does not provide an OS version or device model.
 if(!os){const reported=first(nav.platform);if(/^Mac/.test(reported))os='macOS';else if(/^Win/.test(reported))os='Windows';else if(/^Linux/.test(reported))os='Linux';else if(/^iPhone|^iPad|^iPod/.test(reported))os=reported==='iPad'?'iPadOS':'iOS';}
 const formFactors=Array.isArray(entropy?.formFactors)?entropy.formFactors.filter(f=>typeof f==='string'&&f):[];
 let device=formFactors.length?formFactors.join(', '):parsed.device;
 // Some iPads deliberately report a desktop Mac identity. Do not pretend to know which hardware it is.
 if(os==='macOS'&&nav.maxTouchPoints>1&&!/\biPad\b/.test(first(nav.userAgent))){os='Unknown (browser reports macOS)';device='Unknown (desktop identity; touch-capable)';}
 if(!device&&typeof hints?.mobile==='boolean')device=hints.mobile?'Mobile (browser-reported)':'Non-mobile (browser-reported)';
 const browser=hintBrowser(hints,entropy)||parsed.browser;
 // User-Agent OS tokens can be frozen by privacy protections (including Safari).
 let osVersion=(platform&&os===platformNames[platform]?first(entropy.platformVersion):'')||UNKNOWN;
 // Chromium's Windows platformVersion is an API contract, not a Windows release number.
 if(platform==='Windows'){
  const reported=first(entropy.platformVersion),major=/^\d+(?:\.\d+)*$/.test(reported)?Number(reported.split('.')[0]):-1;
  if(major>=13){os='Windows 11';osVersion='11';}
  else if(major>=1&&major<=10){os='Windows 10';osVersion='10';}
  else {osVersion=({'0.1.0':'7','0.2.0':'8','0.3.0':'8.1'})[reported]||UNKNOWN;}
 }

 const size=(w,h)=>Number.isFinite(w)&&w>0&&Number.isFinite(h)&&h>0?`${w} × ${h}`:UNKNOWN;
 return {
  OS:os||UNKNOWN,
  'OS version':osVersion,
  'Platform version':first(entropy.platformVersion)||UNKNOWN,
  'Reported OS token':parsed.version||UNKNOWN,
  Browser:browser||UNKNOWN,
  Device:device||UNKNOWN,
  Model:first(entropy.model)||UNKNOWN,
  Screen:size(screenInfo?.width,screenInfo?.height),
  Viewport:size(viewport?.innerWidth,viewport?.innerHeight),
  Language:first(nav.language)||UNKNOWN,
  Languages:Array.isArray(nav.languages)&&nav.languages.length?nav.languages.join(', '):UNKNOWN
 };
}
export async function collectDeviceInfo(nav=navigator,screenInfo=screen,viewport=window){
 let entropy={},timeout;
 if(typeof nav.userAgentData?.getHighEntropyValues==='function'){
  try{entropy=await Promise.race([nav.userAgentData.getHighEntropyValues(['platformVersion','fullVersionList','model','formFactors']),new Promise(resolve=>{timeout=setTimeout(()=>resolve({}),700);})])||{};}catch{}finally{clearTimeout(timeout);}
 }
 return deviceInfo(nav,screenInfo,viewport,entropy);
}
