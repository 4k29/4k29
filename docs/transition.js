export const TRANSITION_DURATION=12000;
// A full-screen field of circular dots with travelling waves and decorative progress.
export async function playTransition(element,reduced){
 if(reduced){element.remove();return;}
 element.classList.remove('stage-hidden');
 const canvas=element.querySelector('canvas'),context=canvas.getContext('2d');
 const percentage=element.querySelector('.transition-percentage');
 let width=0,height=0,frame=0,finished=false,lastPercent=-1;
 const dark=()=>document.documentElement.dataset.theme==='dark'||document.documentElement.dataset.theme!=='light'&&!matchMedia('(prefers-color-scheme: light)').matches;
 function resize(){width=innerWidth;height=innerHeight;const ratio=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);context?.setTransform(ratio,0,0,ratio,0,0);}
 resize();window.addEventListener('resize',resize);
 const started=performance.now();
 function draw(now){
  if(finished)return;
  const elapsed=now-started,progress=Math.min(elapsed/(TRANSITION_DURATION-300),1),t=elapsed/1000;
  // Simulated progress reaches 100% just before the introduction appears.
  const percent=progress===1?100:Math.floor(100*(.12*progress+.88*(1-Math.pow(1-progress,1.4))));
  if(percent!==lastPercent){percentage.textContent=percent+'%';percentage.setAttribute('aria-valuenow',String(percent));lastPercent=percent;}
  if(context){
   const isDark=dark();context.fillStyle=isDark?'#181818':'#fafafa';context.fillRect(0,0,width,height);
   const gap=width<600?22:28,columns=Math.ceil(width/gap),rows=Math.ceil(height/gap),amplitude=gap*.8;
   const fade=Math.min(elapsed/700,1);
   for(let y=-2;y<=rows+2;y++)for(let x=-2;x<=columns+2;x++){
    const bx=x*gap,by=y*gap,nx=bx/width,ny=by/height;
    const wave=Math.sin(nx*8+ny*3-t*1.7),cross=Math.sin(nx*4-ny*7+t*1.1);
    const px=bx+Math.cos(ny*6+nx*2-t*.9)*gap*.23;
    const py=by+wave*amplitude+cross*amplitude*.5;
    const crest=(wave+cross*.45+1.45)/2.9;
    const opacity=(.2+crest*.57)*fade,radius=.85+crest*1.65;
    context.fillStyle=isDark?`rgba(205,221,194,${opacity})`:`rgba(65,88,58,${opacity})`;
    context.beginPath();context.arc(px,py,radius,0,Math.PI*2);context.fill();
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
