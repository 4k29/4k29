import { playTransition } from './transition.js';
import { collectDeviceInfo } from './device-info.js';
export { deviceInfo } from './device-info.js';
export async function startBoot(ready){
 window.addEventListener('pageshow',event=>{if(event.persisted)window.location.reload();});
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const [info]=await Promise.all([collectDeviceInfo(),playTransition(document.querySelector('#transition'),reduced)]);
 const log=document.querySelector('#boot-log'),summary=document.querySelector('#device-summary');
 summary.textContent=`device / ${info.OS} ${info['OS version']} · ${info.Browser}`;
 await ready();
 const lines=['$ personal-session / device',...Object.entries(info).map(([key,value])=>`${key}: ${value}`),'[local] device information stays in this browser'];
 for(const line of lines){log.append(document.createTextNode(line+'\n'));if(!reduced)await new Promise(resolve=>setTimeout(resolve,55));}
 if(!reduced){const thinking=document.createElement('span');thinking.className='device-thinking spinner';thinking.setAttribute('aria-label','Thinking');thinking.innerHTML='<i></i><i></i><i></i>';summary.append(thinking);await new Promise(resolve=>setTimeout(resolve,350));thinking.remove();}
 log.append(document.createTextNode('[ready] personal session\n'));
}
