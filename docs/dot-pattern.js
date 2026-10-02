// Sample the existing icon into monochrome square pixels; reveal it from the centre along spirals.
export function createDotPattern(pixels,columns,rows,random=Math.random){
 const dots=[],cx=(columns-1)/2,cy=(rows-1)/2;
 let maxRadius=1;
 for(let y=0;y<rows;y++)for(let x=0;x<columns;x++){
  const index=(y*columns+x)*4,alpha=pixels[index+3]/255;
  if(alpha<.18)continue;
  const dx=x-cx,dy=y-cy,radius=Math.hypot(dx,dy),angle=Math.atan2(dy,dx);
  const luminance=(pixels[index]*.2126+pixels[index+1]*.7152+pixels[index+2]*.0722)/255;
  dots.push({dx,dy,radius,angle,alpha,bucket:Math.min(7,Math.floor(luminance*8)),duration:.14+random()*.08,turns:1+random(),frequency:1+Math.floor(random()*3)});
  maxRadius=Math.max(maxRadius,radius);
 }
 for(const dot of dots){
  const phase=(dot.angle+Math.PI)/(Math.PI*2);
  dot.birth=.72*dot.radius/maxRadius+.05*phase;
 }
 return dots.sort((a,b)=>a.birth-b.birth);
}
export function dotPosition(dot,progress,cell,cx,cy){
 if(progress<dot.birth)return null;
 const raw=Math.min(1,Math.max(0,(progress-dot.birth)/dot.duration));
 // Random frequency and travel time vary acceleration; endpoints stay exact and motion stays forward.
 const paced=raw+.045/dot.frequency*Math.sin(raw*Math.PI*2*dot.frequency);
 const travel=1-Math.pow(1-paced,3),angle=dot.angle+(1-travel)*Math.PI*2*dot.turns;
 if(raw===1)return {x:cx+dot.dx*cell,y:cy+dot.dy*cell,opacity:dot.alpha};
 return {x:cx+Math.cos(angle)*dot.radius*cell*travel,y:cy+Math.sin(angle)*dot.radius*cell*travel,opacity:dot.alpha*Math.min(1,raw*5)};
}
