import { playTransition } from './transition.js';
export const BOOT_CHARACTER_INTERVAL=28;
export const BOOT_LINE_PAUSE=240;
import { collectDeviceInfo } from './device-info.js';
export { deviceInfo } from './device-info.js';
export async function startBoot(ready){
 // A back/forward-cache restoration must also begin with a fresh boot screen.
 window.addEventListener('pageshow',event=>{if(event.persisted)window.location.reload();});
 const boot=document.querySelector('#boot'),next=document.querySelector('#boot-next'),log=document.querySelector('#boot-log'),transition=document.querySelector('#transition');
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const info=await collectDeviceInfo();
 const lines=['$ start personal-session','const device = readBrowserCapabilities();',...Object.entries(info).map(([key,value])=>`  ${key}: ${value}`),'[local] device information stays in this browser','[local] loading profile.json','[ready] personal session'];
 for(const line of lines){
  if(line.startsWith('[ready]')&&!reduced){
   const thinking=document.createElement('span');thinking.className='boot-thinking spinner';thinking.setAttribute('aria-label','Thinking');thinking.innerHTML='<i></i><i></i><i></i>';log.append(thinking);
   await new Promise(resolve=>setTimeout(resolve,1400));thinking.remove();
  }
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
