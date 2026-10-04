// Link only registered answer metadata; never interpret user input as HTML.
export function renderAnswer(element,{text,links=[]}){
 const allowed=links.filter(link=>{try{const url=new URL(link.url);return url.protocol==='https:'&&['x.com','4k29.github.io','youtube.com','www.youtube.com','m.youtube.com','youtu.be','www.tbs.co.jp','www.shonenjump.com','kyu-core.com','kyu-o.com','developer.mozilla.org','developers.google.com','arxiv.org','www.nngroup.com','www.w3.org','spaceplace.nasa.gov','science.nasa.gov','www.eia.gov','openstax.org','www.nist.gov','git-scm.com'].includes(url.hostname)&&typeof link.label==='string'&&link.label.length>0;}catch{return false;}});
 element.replaceChildren();let cursor=0;
 while(cursor<text.length){
  let next=null;
  for(const link of allowed){const index=text.indexOf(link.label,cursor);if(index>=0&&(!next||index<next.index))next={...link,index};}
  if(!next){element.append(document.createTextNode(text.slice(cursor)));break;}
  element.append(document.createTextNode(text.slice(cursor,next.index)));
  const anchor=document.createElement('a');anchor.textContent=next.label;anchor.href=next.url;anchor.target='_blank';anchor.rel='noopener noreferrer';element.append(anchor);cursor=next.index+next.label.length;
 }
}
