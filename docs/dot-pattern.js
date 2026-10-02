// Three centred squares use the same 1.35s / 180ms / ±4px thinking-dot bounce.
export function createDotPattern(width,height){
 return Array.from({length:3},(_,index)=>({x:width/2+(index-1)*14,y:height/2,delay:index*.18,size:8}));
}
export function createWaveClock(){return {phase:0,speed:1,target:1,nextChange:0};}
export function advanceWaveClock(clock,delta,time,random=Math.random){
 const dt=Math.min(.05,Math.max(0,delta));
 if(time>=clock.nextChange){clock.target=.6+random()*1.1;clock.nextChange=time+1+random()*2;}
 clock.speed+=(clock.target-clock.speed)*Math.min(1,dt*1.8);clock.phase+=clock.speed*dt;
}
export const THINKING_DURATION=1.35;
// CSS ease-in-out cubic-bezier(.42,0,.58,1), sampled once for inexpensive canvas frames.
const easing=Array.from({length:257},(_,index)=>{
 const x=index/256;let low=0,high=1;
 for(let i=0;i<18;i++){const t=(low+high)/2,v=3*(1-t)*(1-t)*t*.42+3*(1-t)*t*t*.58+t*t*t;if(v<x)low=t;else high=t;}
 const t=(low+high)/2;return 3*(1-t)*t*t+t*t*t;
});
export function thinkingState(time){
 const phase=((time%THINKING_DURATION)+THINKING_DURATION)%THINKING_DURATION/THINKING_DURATION;
 const half=phase<.5?phase*2:(1-phase)*2,index=half*256;
 const lower=Math.floor(index),upper=Math.min(256,lower+1),amount=easing[lower]+(easing[upper]-easing[lower])*(index-lower);
 return {offset:4-8*amount,opacity:.35+.65*amount};
}
export function dotPosition(dot,phase){
 const state=thinkingState(phase-dot.delay);
 return {x:dot.x,y:dot.y+state.offset,bucket:Math.max(0,Math.min(7,Math.round((state.opacity-.35)/.65*7)))};
}
