export const clamp = (value) => Math.max(0, Math.min(1, value));
export const phase = (value, start, end) => clamp((value - start) / (end - start));
export const lerp = (from, to, progress) => from + (to - from) * progress;
export const smooth = (p) => p * p * (3 - 2 * p);
export const ease = (t, start, end) => smooth(phase(t, start, end));

/* Closed-form damped spring, sampled by scroll. Endpoints stay exact. */
export function settle(p) {
  if (p <= 0 || p >= 1) return p;
  const sample = (x) => 1 - Math.exp(-6.9 * x) * (Math.cos(8 * x) + .84 * Math.sin(8 * x));
  return sample(p) / sample(1);
}

export const box = (x, y, w, h, rotation = 0) => ({x, y, w, h, rotation});
export const mixBox = (a, b, p) => box(
  lerp(a.x, b.x, p), lerp(a.y, b.y, p), lerp(a.w, b.w, p),
  lerp(a.h, b.h, p), lerp(a.rotation, b.rotation, p),
);
export const point = (x,y) => ({x,y});
export const mixPoint = (a,b,p) => point(lerp(a.x,b.x,p),lerp(a.y,b.y,p));
export const corner = (b) => point(b.x,b.y);
export const right = (b) => point(b.x+b.w,b.y);
export const bottomRight = (b) => point(b.x+b.w,b.y+b.h);

function css(node, key, value) {
  if (node.style[key] !== value) node.style[key] = value;
}
const px = (value) => value.toFixed(2) + 'px';
export function visible(node, opacity, interactive) {
  css(node, 'opacity', clamp(opacity).toFixed(4));
  css(node, 'visibility', opacity > .001 ? 'visible' : 'hidden');
  if (interactive !== undefined) node.inert = !interactive;
}
export function place(node, region) {
  css(node, 'transform', `translate3d(${px(region.x)},${px(region.y)},0) rotate(${region.rotation.toFixed(3)}deg)`);
  css(node, 'width', px(region.w));
  css(node, 'height', px(region.h));
}
export function drawFrame(node, region, top = 1, depth = 1, opacity = 1) {
  place(node, region);
  visible(node, opacity);
  const [upper, left, right, lower] = node.children;
  css(upper, 'width', px(region.w * top));
  for (const edge of [left, right]) {
    css(edge, 'height', px(region.h * depth));
    visible(edge, depth > 0 ? 1 : 0);
  }
  css(right, 'left', px(region.w - 1));
  css(lower, 'width', px(region.w));
  css(lower, 'top', px(Math.max(0, region.h * depth - 1)));
  visible(lower, depth > 0 ? 1 : 0);
}

const arrow = 'M0 0 L34 15.5 L21 21 L16 34 Z';
const circle = 'M0 -5 A5 5 0 1 1 0 5 A5 5 0 1 1 0 -5 Z';


export function cursor(node, position, opacity = 1, form = 0, resize = false, lineHeight = 0) {
  visible(node, opacity);
  if (!position || opacity < .002) return;
  css(node,'transform', `translate3d(${px(position.x)},${px(position.y)},0)`);
  const [outline, stem, caps] = node.children;
  const morph = ease(form,0,.42);
  const beam = ease(form,.43,.76);
  const caret = ease(form,.76,1);
  const pointing = !resize && morph < .57;
  outline.setAttribute('d', resize ? 'M-8 0 L0 0 L0 -8 M0 0 L-12 -12 M-12 -4 L-12 -12 L-4 -12' : pointing ? arrow : circle);
  outline.classList.toggle('cursor-arrow',pointing);
  const scale = resize ? 1 : morph < .57 ? lerp(1,.19,morph/.57) : lerp(.78,1,(morph-.57)/.43);
  outline.setAttribute('transform', `scale(${scale.toFixed(3)})`);
  css(outline,'opacity',(1-ease(form,.42,.64)).toFixed(3));
  const finalHalf=lineHeight>0 ? lineHeight*.40*node.viewBox.baseVal.width/Math.max(1,node.clientWidth) : 12;
  const half=lerp(lerp(3,12,beam),finalHalf,caret);
  stem.setAttribute('d',`M0 ${-half} V${half}`);
  caps.setAttribute('d',`M${-5*beam} -12 H${5*beam} M${-5*beam} 12 H${5*beam}`);
  css(stem,'opacity',beam.toFixed(3));
  css(caps,'opacity',(beam*(1-caret)).toFixed(3));
}

const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789+=/<>#%';
function hash(n) {
  const x = Math.imul(n ^ (n >>> 16), 0x45d9f3b);
  return ((x ^ (x >>> 16)) >>> 0) / 4294967296;
}
class TypeFlicker {
  constructor(heading, text) {
    this.glyphs=Array.from(text.replace(/\s+/gu,''));
    this.layer=document.createElement('span');
    this.layer.className='type-flicker';
    this.layer.setAttribute('aria-hidden','true');
    this.fragments=Array.from({length:6},()=>{
      const fragment=document.createElement('span');
      this.layer.append(fragment);
      return fragment;
    });
    heading.after(this.layer);
  }

  render(progress) {
    const frame=Math.floor(progress*10);
    this.layer.hidden=progress<=0 || progress>=.87;
    if(this.layer.hidden || frame===this.frame) return;
    this.frame=frame;
    this.fragments.forEach((fragment,index)=>{
      const seed=frame*293+index*131;
      const offset=Math.floor(hash(seed+5)*this.glyphs.length);
      const length=1+Math.floor(hash(seed+17)*4);
      fragment.hidden=hash(seed+23)>.70;
      fragment.textContent=Array.from({length},(_,i)=>this.glyphs[(offset+i)%this.glyphs.length]).join('');
      fragment.style.left=(6+hash(seed+39)*79)+'%';
      fragment.style.top=(index<3 ? 2+hash(seed+53)*15 : 76+hash(seed+53)*14)+'%';
      fragment.dataset.ink=String(Math.floor(hash(seed+61)*5));
    });
  }
}

export class Scramble {
  constructor(node) {
    const text = node.textContent;
    node.replaceChildren();
    const original = document.createElement('span');
    original.className = 'visually-hidden';
    original.textContent = text;
    node.append(original);
    this.display = document.createElement('span');
    this.display.setAttribute('aria-hidden','true');
    node.append(this.display);
    this.node = node;
    this.flicker=node.hasAttribute('data-type-flicker') ? new TypeFlicker(node,text) : null;
    this.chars = Array.from(text).map((char,index) => {
      if (/\s/u.test(char)) {
        this.display.append(char);
        return {char};
      }
      const slot = document.createElement('span');
      slot.className = 'scramble-slot';
      const ghost = document.createElement('span');
      ghost.className = 'scramble-size';
      ghost.textContent = char;
      const glyph = document.createElement('span');
      glyph.className = 'scramble-glyph';
      slot.append(ghost,glyph);
      this.display.append(slot);
      return {char,slot,glyph,index};
    });
    this.render(1);
  }
  render(amount) {
    const step = Math.round(clamp(amount) * 126);
    if (step === this.step) return;
    this.step = step;
    const p = step / 126;
    const active = p < 1;
    this.flicker?.render(p);
    const insertion=Math.floor(p*this.chars.length);
    const caret=this.chars.find((char,index)=>index>=insertion && char.slot)?.index;
    this.node.classList.toggle('is-scrambling',active);
    this.chars.forEach(({char,slot,glyph,index})=>{
      if (!slot) return;
      const position = index / Math.max(1,this.chars.length-1);
      const target = .12 + .81 * position + .065 * hash(index+19);
      const pending = p < target;
      const letter = pending ? alphabet[Math.floor(hash(step*317 + index*829 + 41)*alphabet.length)] : char;
      if (glyph.textContent !== letter) glyph.textContent = letter;
      slot.classList.toggle('scramble-pending',pending);
      slot.classList.toggle('scramble-caret',active && index === caret);
    });
  }
}
