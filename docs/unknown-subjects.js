// Label missing facts without inventing their values. All-unknown questions keep the existing fallback.
const fields=[[/年齢|何歳|何才|how old|\bage\b/i,'年齢','your age'],[/誕生日|生年月日|birthday|born/i,'誕生日','your birthday'],[/学校|大学|school|university|college/i,'学校','your school'],[/住所|住ん|住まい|address|where.*live/i,'住んでいる場所','where you live'],[/本名|real name/i,'本名','your real name'],[/音楽|曲|music|song/i,'好きな音楽','your music preferences'],[/年収|収入|salary/i,'収入','your income'],[/身長|height/i,'身長','your height'],[/電話|phone/i,'電話番号','your phone number'],[/メール|email/i,'メールアドレス','your email address'],[/理由|なぜ|どうして|why/i,'その理由','the reason'],[/価格|値段|いくら|料金|cost|price/i,'料金・価格','the price'],[/何色|の色|color|colour/i,'色','the colour']];
export function unknownSubjects(text){
 if(/(?:どこ|どちら|どの店|どのお店).*(?:買|購入)|\bwhere\b.*\b(?:buy|bought|purchase|purchased)\b/.test(text))return [{ja:'購入した場所',en:'where you bought it'}];
 if(/メーカー|製造元|\bmanufacturer\b/.test(text))return [{ja:'その製品のメーカー',en:'the product manufacturer'}];
 const matches=fields.filter(([pattern])=>pattern.test(text)).map(([,ja,en])=>({ja,en}));
 if(matches.length)return matches;
 if(/ランニング|ジョギング|running|\brun\b|走って/.test(text)&&/どこ|場所|コース|ルート|where/.test(text))return [{ja:'走っている場所',en:'where you run'}];
 return [{ja:'「'+text.slice(0,80)+'」',en:'“'+text.slice(0,80)+'”'}];
}
export function missingFactsSentence(subjects,language){
 const unique=[...new Map(subjects.map(s=>[s[language],s])).values()];
 return unique.map(s=>language==='ja'?s.ja+'については、まだ答えられません。':"I can't answer about "+s.en+' yet.').join('\n');
}
