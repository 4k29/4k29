import { collectDeviceInfo } from './device-info.js?v=20261005-topic-language-1';
export { deviceInfo } from './device-info.js?v=20261005-topic-language-1';
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
export async function startBoot(ready){
 window.addEventListener('pageshow',event=>{if(event.persisted)window.location.reload();});
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const profile=document.querySelector('#profile'),log=document.querySelector('#boot-log'),summary=document.querySelector('#device-summary');
 profile.classList.remove('stage-hidden');
 for(const element of profile.querySelectorAll('.prompt,.reply,.events,.working'))element.classList.add('stage-hidden');
 async function type(element,text){
  if(reduced){element.append(document.createTextNode(text));return;}
  const row=document.createTextNode('');element.append(row);
  for(let i=0;i<text.length;i+=2){row.appendData(text.slice(i,i+2));await pause(28);}
 }
 const info=await collectDeviceInfo();summary.textContent='';
 await type(summary,`device / ${info.OS} ${info['OS version']} · ${info.Browser}`);
 const lines=['$ personal-session / device','const device = readBrowserCapabilities();',...Object.entries(info).map(([key,value])=>`${key}: ${value}`),'[local] device information stays in this browser'];
 for(const line of lines){await type(log,line+'\n');if(!reduced)await pause(80);}
 if(!reduced){const thinking=document.createElement('span');thinking.className='device-thinking spinner';thinking.setAttribute('aria-label','Thinking');thinking.innerHTML='<i></i><i></i><i></i>';summary.append(thinking);await pause(600);thinking.remove();}
 await type(log,'[ready] personal session\n');
 document.querySelector('#replay').disabled=false;
 await ready();
}
