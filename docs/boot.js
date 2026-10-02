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
 const boot=document.querySelector('#boot'),next=document.querySelector('#boot-next'),status=document.querySelector('#boot-status'),log=document.querySelector('#boot-log'),transition=document.querySelector('#transition');
 let seen=false;try{seen=localStorage.getItem('4k29.boot-seen')==='1';}catch{}
 if(seen){boot.remove();await ready();return;}
 const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
 const lines=['$ start personal-session','const device = readBrowserCapabilities();',...Object.entries(deviceInfo()).map(([key,value])=>`  ${key}: ${value}`),'[local] device information stays in this browser','[local] loading profile.json','[ready] personal session'];
 for(const line of lines){log.append(document.createTextNode(line+'\n'));if(!reduced)await new Promise(resolve=>setTimeout(resolve,110));}
 next.disabled=false;status.textContent='準備完了。Enter またはボタンで次へ進みます。';next.focus();
 let continuing=false;
 async function proceed(){if(next.disabled||continuing)return;continuing=true;document.removeEventListener('keydown',key);try{localStorage.setItem('4k29.boot-seen','1');}catch{}boot.remove();transition.classList.remove('stage-hidden');if(!reduced)await new Promise(resolve=>setTimeout(resolve,900));transition.remove();await ready();}
 function key(event){if(event.key==='Enter'&&!event.isComposing){event.preventDefault();proceed();}}
 next.addEventListener('click',proceed);document.addEventListener('keydown',key);
}
