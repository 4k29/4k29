import { createDotField, positionDot } from './dot-field.js';
export const TRANSITION_DURATION=12000;
// Dense geometric dot choreography with decorative progress.
export async function playTransition(element,reduced){
 if(reduced){element.remove();return;}
 element.classList.remove('stage-hidden');
 const canvas=element.querySelector('canvas'),context=canvas.getContext('2d');
 const percentage=element.querySelector('.transition-percentage');
 let width=0,height=0,frame=0,finished=false,lastPercent=-1,dots=[];
 const dark=()=>document.documentElement.dataset.theme==='dark'||document.documentElement.dataset.theme!=='light'&&!matchMedia('(prefers-color-scheme: light)').matches;
 function resize(){width=innerWidth;height=innerHeight;const ratio=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);context?.setTransform(ratio,0,0,ratio,0,0);dots=createDotField(width,height);}
 resize();window.addEventListener('resize',resize);
 const started=performance.now(),position={x:0,y:0};
 function draw(now){
  if(finished)return;
  const elapsed=now-started,progress=Math.min(elapsed/(TRANSITION_DURATION-300),1),t=elapsed/1000;
  // Simulated progress reaches 100% just before the introduction appears.
  const percent=progress===1?100:Math.floor(100*(.12*progress+.88*(1-Math.pow(1-progress,1.4))));
  if(percent!==lastPercent){percentage.textContent=percent+'%';percentage.setAttribute('aria-valuenow',String(percent));lastPercent=percent;}
  if(context){
   const isDark=dark();context.fillStyle=isDark?'#181818':'#fafafa';context.fillRect(0,0,width,height);
   const fade=Math.min(elapsed/400,1);
   // Batch dots by opacity: only eight fill operations per frame, even at high density.
   for(let bucket=0;bucket<8;bucket++){
    const opacity=(.25+bucket*.075)*fade,radius=1+bucket*.1;
    context.fillStyle=isDark?`rgba(205,221,194,${opacity})`:`rgba(65,88,58,${opacity})`;
    context.beginPath();
    for(let index=bucket;index<dots.length;index+=8){
     const {x,y}=positionDot(dots[index],t,width,height,position);
     context.moveTo(x+radius,y);context.arc(x,y,radius,0,Math.PI*2);
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
