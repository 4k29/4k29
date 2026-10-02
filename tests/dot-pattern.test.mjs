import test from 'node:test';
import assert from 'node:assert/strict';
import {createDotPattern} from '../docs/dot-pattern.js';
test('pattern appears in top-to-bottom order within the viewport',()=>{
 for(const [width,height] of [[1440,900],[390,844]]){
  const dots=createDotPattern(width,height,()=>.5);
  assert.ok(dots.length>1500);let lastBirth=-1,lastY=-1;
  for(const dot of dots){assert.ok(dot.birth>=lastBirth&&dot.birth<1);assert.ok(dot.y>=lastY);assert.ok(dot.x>0&&dot.x<width&&dot.y>0&&dot.y<height);assert.ok(dot.bucket>=0&&dot.bucket<8);lastBirth=dot.birth;lastY=dot.y;}
  assert.ok(dots.filter(d=>d.birth<=.5).every(d=>d.y<height*.53));
 }
});
test('new runs create different placements and shades without changing reveal order',()=>{
 const a=createDotPattern(390,844),b=createDotPattern(390,844);
 assert.notDeepEqual(a,b);assert.ok(new Set(a.map(d=>d.bucket)).size===8);
});
