// Independent square particles follow a breathing flow field, with smoothly changing random speeds.
export function createDotPattern(width,height,random=Math.random){
 return Array.from({length:Math.min(1800,Math.max(500,Math.floor(width*height/700)))},()=>({
  x:random()*width,y:random()*height,phase:random()*Math.PI*2,
  speed:.35+random()*1.4,target:.35+random()*1.4,nextChange:random()*2,
  bucket:Math.floor(random()*8),size:2+Math.floor(random()*3)
 }));
}
export function moveDots(dots,width,height,time,delta,random=Math.random){
 const dt=Math.min(Math.max(delta,0),.05);
 for(const dot of dots){
  if(time>=dot.nextChange){dot.target=.25+random()*2.5;dot.nextChange=time+.4+random()*2;}
  dot.speed+=(dot.target-dot.speed)*Math.min(1,dt*2);
  const nx=dot.x/width,ny=dot.y/height;
  const angle=Math.sin(nx*6+time*.35)+Math.cos(ny*5-time*.27)+dot.phase*.18;
  dot.x=(dot.x+Math.cos(angle)*dot.speed*55*dt+width)%width;
  dot.y=(dot.y+Math.sin(angle)*dot.speed*55*dt+height)%height;
 }
}
