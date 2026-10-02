import test from 'node:test';import assert from 'node:assert/strict';
import {createDotPattern,createWaveClock,advanceWaveClock,dotPosition} from '../docs/dot-pattern.js';
test('square lattice fills desktop and mobile with bounded responsive density',()=>{
 for(const [w,h] of [[1440,900],[390,844]]){const dots=createDotPattern(w,h);assert.ok(dots.length>1500&&dots.length<4000);assert.ok(dots.every(d=>d.x>0&&d.x<w&&d.y>0&&d.y<h));}
});
test('wave displacement stays close to each grid cell and all eight monochrome shades are used',()=>{
 const dots=createDotPattern(1440,900),buckets=new Set();for(const d of dots){const p=dotPosition(d,2,1440,900);assert.ok(Math.abs(p.x-d.x)<=5&&Math.abs(p.y-d.y)<=14);assert.notDeepEqual(p,dotPosition(d,4,1440,900));buckets.add(p.bucket);}assert.equal(buckets.size,8);
});
test('random wave tempo accelerates smoothly and handles long background frames',()=>{
 const clock=createWaveClock();advanceWaveClock(clock,20,1,()=>.9);assert.ok(clock.speed>1&&clock.speed<clock.target);assert.ok(clock.phase>0&&clock.phase<.1);const phase=clock.phase;advanceWaveClock(clock,.02,5,()=>.1);assert.ok(clock.phase>phase);assert.ok(clock.target<1);
});
