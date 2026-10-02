import { playTransition } from './transition.js';
export const BOOT_CHARACTER_INTERVAL=28;
export const BOOT_LINE_PAUSE=240;
// Only report exposed browser values. User-Agent strings are deliberately not guessed.
export function deviceInfo(nav=navigator,screenInfo=screen,viewport=window){
 const hints=nav.userAgentData;
 return {
  OS:hints?.platform||'Unknown',
  Browser:hints?.brands?.filter(b=>!/not.?a.?brand/i.test(b.brand)).map(b=>`${b.brand} ${b.version}`).join(', ')||'Unknown',
  Device:typeof hints?.mobile==='boolean'?(hints.mobile?'Mobile (browser-reported)':'Non-mobile (browser-reported)'):'Unknown',
  Screen:Number.isFinite(screenInfo?.width)&&Number.isFinite(screenInfo?.height)?`${screenInfo.width} × ${screenInfo.height}`:'Unknown',
  Viewport:Number.isFinite(viewport?.innerWidth)&&Number.isFinite(viewport?.innerHeight)?`${viewport.innerWidth} × ${viewport.innerHeight}`:'Unknown',
  Language:nav.language||'Unknown',
  Languages:nav.languages?.length?nav.languages.join(', '):'Unknown'
 };
}
export async function startBoot(ready){
 // A back/forward-cache restoration must also begin with a fresh boot screen.
 window.addEventListener('pageshow',event=>{if(event.persisted)window.location.reload();});
 const boot=document.querySelector('#boot'),next=document.querySelector('#boot-next'),log=document.querySelector('#boot-log'),transition=document.querySelector('#transition');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const lines=['$ start personal-session','const device = readBrowserCapabilities();',...Object.entries(deviceInfo()).map(([key,value])=>`  ${key}: ${value}`),'[local] device information stays in this browser','[local] loading profile.json','[ready] personal session'];
 for(const line of lines){
  if(reduced){log.append(document.createTextNode(line+'\n'));continue;}
  const row=document.createTextNode('');log.append(row);
  for(let offset=0;offset<line.length;offset+=2){row.appendData(line.slice(offset,offset+2));await new Promise(resolve=>setTimeout(resolve,BOOT_CHARACTER_INTERVAL));}
  row.appendData('\n');await new Promise(resolve=>setTimeout(resolve,BOOT_LINE_PAUSE));
 }
 next.disabled=false;next.focus();
 let continuing=false;
 async function proceed(){if(next.disabled||continuing)return;continuing=true;document.removeEventListener('keydown',key);boot.remove();await playTransition(transition,reduced);await ready();}
 function key(event){if(event.key==='Enter'&&!event.isComposing){event.preventDefault();proceed();}}
 next.addEventListener('click',proceed);document.addEventListener('keydown',key);
}
