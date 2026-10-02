import {createDotPattern,dotPosition} from './dot-pattern.js';
export const TRANSITION_DURATION=12000;
const SAMPLE_SIZE=96;
async function readIcon(){
 const icon=new Image();icon.src=new URL('./assets/avatar-neutral.png',import.meta.url).href;
 try{await icon.decode();}catch{return [];}
 const sample=document.createElement('canvas');sample.width=sample.height=SAMPLE_SIZE;
 const context=sample.getContext('2d');if(!context)return [];
 context.drawImage(icon,0,0,SAMPLE_SIZE,SAMPLE_SIZE);
 return createDotPattern(context.getImageData(0,0,SAMPLE_SIZE,SAMPLE_SIZE).data,SAMPLE_SIZE,SAMPLE_SIZE);
}
export async function playTransition(element,reduced){
 element.classList.remove('stage-hidden');
 const canvas=element.querySelector('canvas'),context=canvas.getContext('2d');
 const percentage=element.querySelector('.transition-percentage'),next=element.querySelector('button');
 let width,height,ratio,cell,frame,complete=false,finished=false;
 let dots=[];const started=performance.now();
 function resize(){width=innerWidth;height=innerHeight;ratio=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);context?.setTransform(ratio,0,0,ratio,0,0);cell=Math.min(width*.9,height*.7,620)/SAMPLE_SIZE;}
 resize();
 function draw(now){
  if(finished)return;
  const progress=reduced?1:Math.min(1,(now-started)/TRANSITION_DURATION),percent=Math.floor(progress*100);
  percentage.textContent=`loading… ${percent}%`;percentage.setAttribute('aria-valuenow',String(percent));
  if(percent===100&&!complete){complete=true;next.hidden=false;next.focus();}
  if(context){
   const dark=document.documentElement.dataset.theme==='dark'||document.documentElement.dataset.theme!=='light'&&!matchMedia('(prefers-color-scheme: light)').matches;
   context.fillStyle=dark?'#181818':'#fafafa';context.fillRect(0,0,width,height);
   const side=Math.max(1,Math.round(cell*.83*ratio))/ratio;
   for(let bucket=0;bucket<8;bucket++){
    context.fillStyle=`rgba(${dark?'235,235,235':'30,30,30'},${.22+bucket*.1})`;context.beginPath();
    for(const dot of dots){
     if(dot.bucket!==bucket)continue;
     const position=dotPosition(dot,progress,cell,width/2,height/2);
     if(!position||position.opacity<.18)continue;
     // Keep a true square silhouette at physical-pixel boundaries.
     context.rect(Math.round((position.x-side/2)*ratio)/ratio,Math.round((position.y-side/2)*ratio)/ratio,side,side);
    }
    context.fill();
   }
  }
  if(!reduced&&progress<1)frame=requestAnimationFrame(draw);
 }
 function onResize(){resize();if(reduced||complete)draw(performance.now());}
 window.addEventListener('resize',onResize);
 await new Promise(resolve=>{
  function finish(){if(!complete||finished)return;finished=true;cancelAnimationFrame(frame);window.removeEventListener('resize',onResize);document.removeEventListener('keydown',key);next.removeEventListener('click',finish);element.remove();resolve();}
  function key(event){if(event.key==='Enter'&&!event.isComposing&&!event.repeat){event.preventDefault();finish();}}
  document.addEventListener('keydown',key);next.addEventListener('click',finish);
  // Keep the progress/control flow available even if the local icon cannot be decoded.
  readIcon().then(value=>{if(finished)return;dots=value;if(reduced||complete)draw(performance.now());});draw(performance.now());
 });
}
