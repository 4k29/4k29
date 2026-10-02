export const TRANSITION_DURATION=12000;
// A viewport-sized geometric field. No images, libraries, or device data are needed.
export async function playTransition(element,reduced){
 if(reduced){element.remove();return;}
 element.classList.remove('stage-hidden');
 const canvas=element.querySelector('canvas'),context=canvas.getContext('2d'),skip=element.querySelector('button');
 const caption=element.querySelector('.transition-phase');
 const phases=['Gathering context','Finding the shape','Connecting the dots','Ready to begin'];
 let width=0,height=0,frame=0,finished=false;
 const dark=()=>document.documentElement.dataset.theme==='dark'||document.documentElement.dataset.theme!=='light'&&!matchMedia('(prefers-color-scheme: light)').matches;
 function resize(){width=innerWidth;height=innerHeight;const ratio=Math.min(devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);context?.setTransform(ratio,0,0,ratio,0,0);}
 resize();window.addEventListener('resize',resize);
 const started=performance.now();
 function draw(now){if(finished||!context)return;const elapsed=now-started,progress=Math.min(elapsed/TRANSITION_DURATION,1),t=elapsed/1000;
  context.fillStyle=dark()?'#181818':'#fafafa';context.fillRect(0,0,width,height);
  const gap=width<600?28:38,columns=Math.ceil(width/gap),rows=Math.ceil(height/gap),cx=width/2,cy=height/2;
  const alpha=Math.min(progress*5,1, (1-progress)*8+.15);
  for(let y=0;y<=rows;y++)for(let x=0;x<=columns;x++){
   const bx=x*gap,by=y*gap,dx=bx-cx,dy=by-cy,r=Math.hypot(dx,dy),angle=Math.atan2(dy,dx);
   const wave=Math.sin(r/65-t*2.4),swirl=Math.sin(angle*3+t*.7)*Math.sin(progress*Math.PI);
   const px=bx+Math.cos(angle+Math.PI/2)*swirl*16,py=by+Math.sin(angle+Math.PI/2)*swirl*16;
   const ring=Math.exp(-Math.pow((r-(t*70)%(Math.hypot(cx,cy)+180))/75,2));
   const opacity=(.12+.28*(wave+1)/2+.4*ring)*alpha;
   context.fillStyle=dark()?`rgba(205,221,194,${opacity})`:`rgba(65,88,58,${opacity})`;
   const size=1.5+ring*2.8;if((x+y)%7===0){context.fillRect(px-size/2,py-size/2,size,size);}else{context.beginPath();context.arc(px,py,size/2,0,Math.PI*2);context.fill();}
  }
  context.save();context.translate(cx,cy);context.strokeStyle=dark()?'rgba(207,225,195,.22)':'rgba(53,78,45,.22)';context.lineWidth=1;
  for(let n=0;n<3;n++){context.save();context.rotate(t*(n%2?-.12:.1)+n*Math.PI/4);const size=(Math.min(width,height)*.32)+n*45+Math.sin(t+n)*12;context.strokeRect(-size/2,-size/2,size,size);context.restore();}
  context.restore();caption.textContent=phases[Math.min(3,Math.floor(progress*4))];frame=requestAnimationFrame(draw);
 }
 frame=requestAnimationFrame(draw);
 await new Promise(resolve=>{
  let timer;
  function finish(){if(finished)return;finished=true;clearTimeout(timer);cancelAnimationFrame(frame);window.removeEventListener('resize',resize);document.removeEventListener('keydown',key);skip.removeEventListener('click',finish);element.remove();resolve();}
  function key(event){if(event.key==='Enter'&&!event.isComposing){event.preventDefault();finish();}}
  skip.addEventListener('click',finish);document.addEventListener('keydown',key);timer=setTimeout(finish,TRANSITION_DURATION);skip.focus();
 });
}
