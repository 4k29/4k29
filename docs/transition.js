import {createDotPattern,moveDots} from './dot-pattern.js';
export const TRANSITION_DURATION=12000;
export async function playTransition(element,reduced){
 element.classList.remove('stage-hidden');
 const canvas=element.querySelector('canvas'),context=canvas.getContext('2d');
 const percentage=element.querySelector('.transition-percentage'),next=element.querySelector('button');
 let width,height,ratio,dots,frame,complete=false,last=performance.now();
 const started=last;
 function resize(){width=innerWidth;height=innerHeight;ratio=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);context?.setTransform(ratio,0,0,ratio,0,0);dots=createDotPattern(width,height);}
 resize();window.addEventListener('resize',resize);
 function draw(now){
  const elapsed=now-started,percent=reduced?100:Math.min(100,Math.floor(elapsed/TRANSITION_DURATION*100));
  percentage.textContent=`loading… ${percent}%`;percentage.setAttribute('aria-valuenow',String(percent));
  if(percent===100&&!complete){complete=true;next.hidden=false;next.focus();}
  if(context){
   const dark=document.documentElement.dataset.theme==='dark'||document.documentElement.dataset.theme!=='light'&&!matchMedia('(prefers-color-scheme: light)').matches;
   context.fillStyle=dark?'#181818':'#fafafa';context.fillRect(0,0,width,height);
   if(!reduced)moveDots(dots,width,height,elapsed/1000,(now-last)/1000);
   for(let bucket=0;bucket<8;bucket++){
    context.fillStyle=`rgba(${dark?'220,220,220':'45,45,45'},${.12+bucket*.1})`;context.beginPath();
    for(const dot of dots)if(dot.bucket===bucket){const side=Math.round(dot.size*ratio)/ratio;context.rect(Math.round(dot.x*ratio)/ratio,Math.round(dot.y*ratio)/ratio,side,side);}
    context.fill();
   }
  }
  last=now;if(!reduced)frame=requestAnimationFrame(draw);
 }
 await new Promise(resolve=>{
  function finish(){if(!complete)return;cancelAnimationFrame(frame);window.removeEventListener('resize',resize);document.removeEventListener('keydown',key);next.removeEventListener('click',finish);element.remove();resolve();}
  function key(event){if(event.key==='Enter'&&!event.isComposing&&!event.repeat){event.preventDefault();finish();}}
  document.addEventListener('keydown',key);next.addEventListener('click',finish);draw(performance.now());
 });
}
