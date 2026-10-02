import test from 'node:test';import assert from 'node:assert/strict';
import {createDotPattern,createWaveClock,advanceWaveClock,dotPosition,thinkingState,THINKING_DURATION} from '../docs/dot-pattern.js';
test('only three thinking dots appear at the centre on desktop and mobile',()=>{
 for(const [w,h] of [[1440,900],[390,844]]){const dots=createDotPattern(w,h);assert.equal(dots.length,3);assert.equal(dots[1].x,w/2);assert.ok(dots.every(d=>d.y===h/2&&Math.abs(d.x-w/2)<=14&&d.size===8));}
});
test('canvas thinking matches the CSS bounce extrema, opacity and period',()=>{
 const start=thinkingState(0),peak=thinkingState(THINKING_DURATION/2),end=thinkingState(THINKING_DURATION);
 assert.ok(Math.abs(start.offset-4)<.0001&&Math.abs(start.opacity-.35)<.0001);
 assert.ok(Math.abs(peak.offset+4)<.0001&&Math.abs(peak.opacity-1)<.0001);assert.deepEqual(start,end);
 const dots=createDotPattern(1440,900),buckets=new Set();
 for(const d of dots){const p=dotPosition(d,2);assert.equal(p.x,d.x);assert.ok(Math.abs(p.y-d.y)<=4);buckets.add(p.bucket);}
 assert.ok([...buckets].every(bucket=>bucket>=0&&bucket<8));
 const a=dots[0],b=dots[1];assert.ok(Math.abs(b.delay-a.delay-.18)<.0001);assert.ok(Math.abs(dotPosition(a,1).y-a.y-(dotPosition(b,1.18).y-b.y))<.0001);
});
test('random wave tempo accelerates smoothly and handles long background frames',()=>{
 const clock=createWaveClock();advanceWaveClock(clock,20,1,()=>.9);assert.ok(clock.speed>1&&clock.speed<clock.target);assert.ok(clock.phase>0&&clock.phase<.1);const phase=clock.phase;advanceWaveClock(clock,.02,5,()=>.1);assert.ok(clock.phase>phase);assert.ok(clock.target<1);
});
