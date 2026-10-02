import test from 'node:test';
import assert from 'node:assert/strict';
import {createDotField,positionDot} from '../docs/dot-field.js';
test('dot density increases within viewport-specific rendering budgets',()=>{
 const desktop=createDotField(1440,900),mobile=createDotField(390,844);
 assert.ok(desktop.length>5000&&desktop.length<=6000);
 assert.ok(mobile.length>1800&&mobile.length<=2200);
});
test('all geometric modes keep dots finite and inside the viewport',()=>{
 for(const [width,height] of [[1440,900],[390,844],[844,390],[3840,2160]]){
  const dots=createDotField(width,height);
  for(const time of [0,.5,2.399,2.4,2.55,3,5,7.3,9.7,11.9])for(const dot of dots){
   const {x,y}=positionDot(dot,time,width,height);assert.ok(Number.isFinite(x)&&x>=0&&x<width);assert.ok(Number.isFinite(y)&&y>=0&&y<height);
  }
 }
});
test('dense choreography moves most dots substantially rather than gently waving',()=>{
 const dots=createDotField(1440,900);
 for(const time of [.6,3,5.5,8]){
  let moved=0;for(const dot of dots){const a=positionDot(dot,time,1440,900),b=positionDot(dot,time+.2,1440,900);if(Math.hypot(a.x-b.x,a.y-b.y)>8)moved++;}
  assert.ok(moved>dots.length*.7,`insufficient movement at ${time}s`);
 }
});
