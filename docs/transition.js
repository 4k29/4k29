import { createDotPattern } from './dot-pattern.js';
export const TRANSITION_DURATION=12000;
// Random pixels appear row by row from the top; no motif or wave movement.
export async function playTransition(element,reduced){
 if(reduced){element.remove();return;}
 element.classList.remove('stage-hidden');
 const canvas=element.querySelector('canvas'),context=canvas.getContext('2d');
 const percentage=element.querySelector('.transition-percentage');
 let width=0,height=0,frame=0,finished=false,lastPercent=-1,lastTheme=null,dots=[],ratio=1;
 const dark=()=>document.documentElement.dataset.theme==='dark'||document.documentElement.dataset.theme!=='light'&&!matchMedia('(prefers-color-scheme: light)').matches;
 function resize(){width=innerWidth;height=innerHeight;ratio=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);context?.setTransform(ratio,0,0,ratio,0,0);dots=createDotPattern(width,height);}
 resize();window.addEventListener('resize',resize);
 const started=performance.now();
 function draw(now){
  if(finished)return;
  const elapsed=now-started,progress=Math.min(elapsed/(TRANSITION_DURATION-300),1);
  // Simulated progress reaches 100% just before the introduction appears.
  const coverage=progress===1?1:.12*progress+.88*(1-Math.pow(1-progress,1.4));
  const percent=Math.floor(coverage*100);
  if(percent!==lastPercent){percentage.textContent=percent+'%';percentage.setAttribute('aria-valuenow',String(percent));lastPercent=percent;}
  if(context){
   const isDark=dark();if(lastTheme!==isDark){percentage.style.color=isDark?'#ededed':'#252525';lastTheme=isDark;}context.fillStyle=isDark?'#181818':'#fafafa';context.fillRect(0,0,width,height);
   // Draw stable random shades; reveal order is top-to-bottom, left-to-right.
   for(let bucket=0;bucket<8;bucket++){
    const opacity=.16+bucket*.1;
    context.fillStyle=isDark?`rgba(220,220,220,${opacity})`:`rgba(45,45,45,${opacity})`;
    context.beginPath();
    for(const dot of dots){
     if(dot.birth>coverage)break;
     if(dot.bucket===bucket){
      const side=Math.max(1,Math.round(dot.size*ratio))/ratio;
      const left=Math.round((dot.x-side/2)*ratio)/ratio,top=Math.round((dot.y-side/2)*ratio)/ratio;
      context.rect(left,top,side,side);
     }
    }
    context.fill();
   }
  }
  frame=requestAnimationFrame(draw);
 }
 percentage.textContent='0%';percentage.setAttribute('aria-valuenow','0');
 frame=requestAnimationFrame(draw);
 await new Promise(resolve=>{
  let timer;
  function finish(){if(finished)return;finished=true;clearTimeout(timer);cancelAnimationFrame(frame);window.removeEventListener('resize',resize);document.removeEventListener('keydown',key);element.remove();resolve();}
  // Keep keyboard skipping available without adding visible text or controls.
  function key(event){if(event.key==='Enter'&&!event.isComposing){event.preventDefault();finish();}}
  document.addEventListener('keydown',key);timer=setTimeout(finish,TRANSITION_DURATION);
 });
}
