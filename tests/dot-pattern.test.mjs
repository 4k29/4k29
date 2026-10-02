import test from 'node:test';
import assert from 'node:assert/strict';
import {createDotPattern,dotPosition} from '../docs/dot-pattern.js';
const pixels=new Uint8ClampedArray(16*16*4);for(let i=0;i<pixels.length;i+=4){pixels[i]=pixels[i+1]=pixels[i+2]=230;pixels[i+3]=255;}
test('icon sampling keeps source coordinates, excludes transparency and reveals centre first',()=>{
 const source=pixels.slice();source[3]=0;const dots=createDotPattern(source,16,16,()=>.5);assert.equal(dots.length,255);
 assert.ok(dots[0].radius<2);assert.ok(dots.at(-1).radius>9);
 assert.ok(dots.every(d=>d.bucket>=0&&d.bucket<=7&&d.birth+d.duration<1));assert.equal(dotPosition(dots.at(-1),0,4,100,200),null);
});
test('every square settles exactly onto the original icon grid at completion',()=>{
 const dots=createDotPattern(pixels,16,16);
 for(const d of dots){const p=dotPosition(d,1,4,100,200);assert.deepEqual(p,{x:100+d.dx*4,y:200+d.dy*4,opacity:1});}
});
test('spiral motion starts at the centre and random timing changes the path, not the final icon',()=>{
 const a=createDotPattern(pixels,16,16,()=>.2),b=createDotPattern(pixels,16,16,()=>.8);const d=a.at(-1);
 const origin=dotPosition(d,d.birth,4,100,200);assert.equal(origin.x,100);assert.equal(origin.y,200);
 const halfway=dotPosition(d,d.birth+d.duration*.5,4,100,200);assert.ok(Math.hypot(halfway.x-100,halfway.y-200)>0);assert.ok(Math.hypot(halfway.x-100,halfway.y-200)<d.radius*4);
 assert.notEqual(a[0].duration,b[0].duration);assert.notEqual(a[0].turns,b[0].turns);assert.deepEqual(dotPosition(a[0],1,4,100,200),dotPosition(b[0],1,4,100,200));
});
