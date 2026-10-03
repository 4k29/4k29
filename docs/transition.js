import {createDotPattern,createWaveClock,advanceWaveClock,dotPosition} from './dot-pattern.js';
export const TRANSITION_DURATION=1800;
export async function playTransition(element,reduced){
 element.classList.remove('stage-hidden');
 const canvas=element.querySelector('canvas'),context=canvas.getContext('2d');
 const percentage=element.querySelector('.transition-percentage'),next=element.querySelector('button');
 let width,height,ratio,dots,frame,complete=false,finished=false;
 const started=performance.now(),clock=createWaveClock();let last=started;
 function resize(){width=innerWidth;height=innerHeight;ratio=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);context?.setTransform(ratio,0,0,ratio,0,0);dots=createDotPattern(width,height);}
 resize();
 function draw(now){
  if(finished)return;
  const progress=reduced?1:Math.min(1,(now-started)/TRANSITION_DURATION),percent=Math.floor(progress*100);
  percentage.textContent=`loading… ${percent}%`;percentage.setAttribute('aria-valuenow',String(percent));
  if(percent===100&&!complete){complete=true;next.hidden=false;next.focus();}
  if(!reduced)advanceWaveClock(clock,(now-last)/1000,(now-started)/1000);last=now;
  if(context){
   const dark=document.documentElement.dataset.theme==='dark'||document.documentElement.dataset.theme!=='light'&&!matchMedia('(prefers-color-scheme: light)').matches;
   context.fillStyle=dark?'#181818':'#fafafa';context.fillRect(0,0,width,height);
   const positions=dots.map(dot=>({...dotPosition(dot,clock.phase),size:dot.size}));
   for(let bucket=0;bucket<8;bucket++){
    context.fillStyle=`rgba(${dark?'235,235,235':'30,30,30'},${.35+bucket*.65/7})`;context.beginPath();
    for(const point of positions){
     if(point.bucket!==bucket)continue;
     const side=Math.max(1,Math.round(point.size*ratio))/ratio;
     context.rect(Math.round((point.x-side/2)*ratio)/ratio,Math.round((point.y-side/2)*ratio)/ratio,side,side);
    }
    context.fill();
   }
  }
  if(!reduced)frame=requestAnimationFrame(draw);
 }
 function onResize(){resize();if(reduced)draw(performance.now());}
 window.addEventListener('resize',onResize);
 await new Promise(resolve=>{
  function finish(){if(!complete||finished)return;finished=true;cancelAnimationFrame(frame);window.removeEventListener('resize',onResize);document.removeEventListener('keydown',key);next.removeEventListener('click',finish);element.remove();resolve();}
  function key(event){if(event.key==='Enter'&&!event.isComposing&&!event.repeat){event.preventDefault();finish();}}
  document.addEventListener('keydown',key);next.addEventListener('click',finish);draw(performance.now());
 });
}
