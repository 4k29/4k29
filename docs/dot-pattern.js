// A full-screen square lattice follows coherent waves; no image or motif is sampled.
export function createDotPattern(width,height,random=Math.random){
 const gap=width<600?14:20,columns=Math.max(1,Math.floor(width/gap)),rows=Math.max(1,Math.floor(height/gap)),dots=[];
 for(let row=0;row<rows;row++)for(let column=0;column<columns;column++)dots.push({
  x:(column+.5)*width/columns,y:(row+.5)*height/rows,
  phase:(random()-.5)*.3,pace:.9+random()*.2,size:width<600?3:4
 });
 return dots;
}
export function createWaveClock(){return {phase:0,speed:1,target:1,nextChange:0};}
export function advanceWaveClock(clock,delta,time,random=Math.random){
 const dt=Math.min(.05,Math.max(0,delta));
 if(time>=clock.nextChange){clock.target=.6+random()*1.1;clock.nextChange=time+1+random()*2;}
 clock.speed+=(clock.target-clock.speed)*Math.min(1,dt*1.8);clock.phase+=clock.speed*dt;
}
export function dotPosition(dot,phase,width,height){
 const nx=dot.x/Math.max(1,width),ny=dot.y/Math.max(1,height),t=phase*dot.pace;
 const a=nx*Math.PI*4+ny*Math.PI*1.2-t*1.9+dot.phase;
 const b=ny*Math.PI*3-nx*Math.PI-t*1.1;
 const amplitude=width<600?9:14;
 return {x:dot.x+Math.sin(b)*amplitude*.35,y:dot.y+Math.sin(a)*amplitude,
  bucket:Math.max(0,Math.min(7,Math.floor((.5+.32*Math.sin(a)+.18*Math.cos(b))*8)))};
}
