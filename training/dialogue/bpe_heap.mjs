// Exact learned byte-BPE with adjacent-pair updates; no outside vocabulary.
// Rule rank, then the original left position, preserve the ordered merge loop.
export function createAdjacentBPE(config){
 const offset=Object.keys(config.specials).length,V=config.bytes.length;
 const ranks=new Map();
 for(const [rank,[left,right,token]] of config.merges.entries()){
  const pair=left*V+right;
  if(!ranks.has(pair))ranks.set(pair,{rank,token});
 }
 const encoder=new TextEncoder();
 return function encode(text){
  const values=[...encoder.encode(text)].map(byte=>byte+offset);
  if(!values.length)return [];
  const previous=values.map((_,i)=>i-1),next=values.map((_,i)=>i+1),alive=new Uint8Array(values.length).fill(1),heap=[];
  next[next.length-1]=-1;
  const before=(a,b)=>a.rank<b.rank||(a.rank===b.rank&&a.left<b.left);
  function push(item){
   let i=heap.length;heap.push(item);
   while(i){const parent=(i-1)>>1;if(!before(item,heap[parent]))break;heap[i]=heap[parent];i=parent;}heap[i]=item;
  }
  function pop(){
   const first=heap[0],last=heap.pop();
   if(heap.length){let i=0;while(2*i+1<heap.length){let child=2*i+1;if(child+1<heap.length&&before(heap[child+1],heap[child]))child++;if(!before(heap[child],last))break;heap[i]=heap[child];i=child;}heap[i]=last;}
   return first;
  }
  function enqueue(left){
   if(left<0||!alive[left])return;
   const right=next[left];if(right<0)return;
   const a=values[left],b=values[right],rule=ranks.get(a*V+b);
   if(rule)push({rank:rule.rank,left,right,a,b,token:rule.token});
  }
  for(let i=0;i<values.length-1;i++)enqueue(i);
  while(heap.length){
   const {left,right,a,b,token}=pop();
   if(!alive[left]||!alive[right]||next[left]!==right||values[left]!==a||values[right]!==b)continue;
   values[left]=token;alive[right]=0;next[left]=next[right];
   if(next[right]>=0)previous[next[right]]=left;
   enqueue(previous[left]);enqueue(left);
  }
  return values.filter((_,i)=>alive[i]);
 };
}
