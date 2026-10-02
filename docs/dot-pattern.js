// A fresh, motif-free pixel pattern on each run. Geometry remains a regular grid.
export function createDotPattern(width,height,random=Math.random){
 const gap=width<600?12:16,columns=Math.max(1,Math.floor(width/gap)),rows=Math.max(1,Math.floor(height/gap));
 const sx=width/columns,sy=height/rows,dots=[];
 for(let row=0;row<rows;row++)for(let column=0;column<columns;column++){
  if(random()<.2)continue;
  dots.push({x:(column+.5)*sx,y:(row+.5)*sy,bucket:Math.min(7,Math.floor(random()*8)),birth:(row+.8*column/columns)/rows,size:Math.max(2,Math.round(gap*.25))});
 }
 return dots;
}
