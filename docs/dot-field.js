const wrap=(value,size)=>((value%size)+size)%size;
const lerp=(a,b,t)=>a+(b-a)*t;
export function createDotField(width,height){
 const budget=width<600?2200:6000;
 const spacing=Math.max(width<600?10:12,Math.sqrt(width*height/budget));
 const columns=Math.max(1,Math.floor(width/spacing)),rows=Math.max(1,Math.floor(height/spacing));
 const sx=width/columns,sy=height/rows;
 return Array.from({length:columns*rows},(_,index)=>{
  const column=index%columns,row=Math.floor(index/columns),tileX=Math.floor(column/6),tileY=Math.floor(row/6);
  return {index,column,row,x:(column+.5)*sx,y:(row+.5)*sy,cx:(tileX*6+3)*sx,cy:(tileY*6+3)*sy,lx:((column%6)-2.5)*sx,ly:((row%6)-2.5)*sy,seed:(tileX*13+tileY*7)%19,bucket:index%8};
 });
}
function project(dot,time,mode,out){
 if(mode===0){
  // A tile of dots turns through right-angled paths instead of rotating in circles.
  const clock=time*(1.6+dot.seed*.035)+dot.seed*.27,step=Math.floor(clock),phase=clock-step;
  const q=step%4,ax=q===0?dot.lx:q===1?-dot.ly:q===2?-dot.lx:dot.ly,ay=q===0?dot.ly:q===1?dot.lx:q===2?-dot.ly:-dot.lx;
  const bx=-ay,by=ax;
  out.x=dot.cx+(phase<.5?lerp(ax,bx,phase*2):bx);out.y=dot.cy+(phase<.5?ay:lerp(ay,by,(phase-.5)*2));return out;
 }
 if(mode===1){
  // Interleaved horizontal and vertical streams cross at different speeds.
  const direction=dot.row%2?1:-1;
  const horizontal=(dot.column+dot.row)%2===0;
  out.x=horizontal?dot.x+time*(170+(dot.row%5)*35)*direction:dot.x;out.y=horizontal?dot.y:dot.y+time*(150+(dot.column%5)*40)*(dot.column%2?1:-1);return out;
 }
 if(mode===2){
  // Each dot travels along a diamond's four straight edges.
  const radius=Math.max(12,Math.max(Math.abs(dot.lx),Math.abs(dot.ly))*1.65),clock=time*2+dot.index*.019+dot.seed;
  const edge=Math.floor(clock)%4,phase=clock-Math.floor(clock),ax=edge===0?radius:edge===2?-radius:0,ay=edge===1?radius:edge===3?-radius:0;
  out.x=dot.cx+lerp(ax,-ay,phase);out.y=dot.cy+lerp(ay,ax,phase);return out;
 }
 // Diagonal counter-flow creates a rapidly changing, interwoven lattice.
 const direction=(dot.column+dot.row)%2?1:-1,speed=190+(dot.index%7)*25;
 out.x=dot.x+time*speed*direction;out.y=dot.y+time*speed*(dot.row%2?1:-1);return out;
}
export function positionDot(dot,time,width,height,out={}){
 const clock=time/2.4,stage=Math.floor(clock)%4,phase=clock-Math.floor(clock);
 const current=project(dot,time,stage,out);let x=wrap(current.x,width),y=wrap(current.y,height);
 if(time>=2.4&&phase<.1){
  const previous=project(dot,time,(stage+3)%4,out),px=wrap(previous.x,width),py=wrap(previous.y,height),blend=phase/.1;
  const dx=wrap(x-px+width/2,width)-width/2,dy=wrap(y-py+height/2,height)-height/2;
  x=wrap(px+dx*blend,width);y=wrap(py+dy*blend,height);
 }
 out.x=x;out.y=y;return out;
}
