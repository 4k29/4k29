// Explanations are protected, source-backed complete sentences. Their facts
// are supplied by retrieval or calculation rather than invented token values.
export function knowledgeGrammar(language,vocabulary){
 const value=vocabulary.indexOf('{value}');
 if(value<0)throw Error('Missing protected value token');
 return ['polite','friendly'].map(style=>({id:language+':knowledge:'+style,language,kind:'knowledge',style,tokens:[value],quality:1,detail:false}));
}
