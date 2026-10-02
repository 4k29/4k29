import test from 'node:test';
import assert from 'node:assert/strict';
import {createDotPattern,moveDots} from '../docs/dot-pattern.js';
test('particles are monochrome square sizes with bounded responsive density',()=>{
 for(const [w,h] of [[1440,900],[390,844]]){const dots=createDotPattern(w,h);assert.ok(dots.length>=500&&dots.length<=1800);for(const d of dots){assert.ok(d.x>=0&&d.x<w&&d.y>=0&&d.y<h);assert.ok(d.bucket>=0&&d.bucket<8);assert.ok(d.size>=2&&d.size<=4);}}
});
test('random targets change speed smoothly and motion stays bounded after long frames',()=>{
 const dots=createDotPattern(390,844,()=>.5),before={...dots[0]};moveDots(dots,390,844,3,10,()=>.9);
 assert.notEqual(dots[0].target,before.target);assert.ok(dots[0].speed>before.speed&&dots[0].speed<dots[0].target);assert.notEqual(dots[0].x,before.x);
 for(let i=0;i<1000;i++)moveDots(dots,390,844,i,.05);assert.ok(dots.every(d=>d.x>=0&&d.x<390&&d.y>=0&&d.y<844));
});
