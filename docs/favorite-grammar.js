// New favorite names remain protected values. These authored frames reuse the
// frozen model's existing vocabulary and favorite control, without claiming
// that the new profile facts or frames were part of its training corpus.
const templates={
 ja:{polite:['好きな{label}は{value}です。','{label}では、{value}が好きです。','{label}の中では{value}が好きです。','好きな{label}なら{value}です。','{label}は{value}が好きです。'],friendly:['好きな{label}は{value}だよ。','{label}では、{value}が好きだよ。','{label}の中では{value}が好きだよ。','好きな{label}なら{value}だよ。','{label}は{value}が好きだよ。']},
 en:{polite:['I like {value}.','My interests include {value}.','I am interested in {value}.','I like these {label}: {value}.','I like the following {label}: {value}.'],friendly:['I like {value}.','My interests include {value}.','I am interested in {value}.','I like these {label}: {value}.','I like the following {label}: {value}.']}
};
export function favoriteGrammar(language,vocabulary){
 const ids=new Map(vocabulary.map((word,id)=>[word,id])),segmenter=new Intl.Segmenter(language,{granularity:'word'});
 return Object.entries(templates[language]).flatMap(([style,frames])=>frames.map((template,index)=>{
  const words=template.split(/(\{value\}|\{label\})/).filter(Boolean).flatMap(piece=>/^\{(?:value|label)\}$/.test(piece)?[piece]:[...segmenter.segment(piece)].map(part=>part.segment));
  const tokens=words.map(word=>{if(!ids.has(word))throw Error('Favorite grammar vocabulary mismatch: '+word);return ids.get(word);});
  return {id:language+':favoriteThing:'+style+':'+index,language,kind:'favoriteThing',style,tokens,quality:1,detail:false};
 }));
}
