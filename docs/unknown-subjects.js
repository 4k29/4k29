// Label missing facts without inventing their values. All-unknown questions keep the existing fallback.
const fields=[[/年齢|何歳|何才|\bage\b/i,'年齢','your age'],[/誕生日|生年月日|birthday|born/i,'誕生日','your birthday'],[/学校|大学|school|university/i,'学校','your school'],[/住所|住ん|住まい|address|where.*live/i,'住んでいる場所','where you live'],[/本名|real name/i,'本名','your real name'],[/音楽|曲|music|song/i,'好きな音楽','your music preferences'],[/年収|収入|salary/i,'収入','your income'],[/身長|height/i,'身長','your height'],[/電話|phone/i,'電話番号','your phone number'],[/メール|email/i,'メールアドレス','your email address'],[/理由|なぜ|どうして|why/i,'その理由','the reason'],[/価格|値段|いくら|料金|cost|price/i,'料金・価格','the price'],[/何色|の色|color|colour/i,'色','the colour']];
export function unknownSubjects(text){
 const matches=fields.filter(([pattern])=>pattern.test(text)).map(([,ja,en])=>({ja,en}));
 if(matches.length)return matches;
 if(/ランニング|ジョギング|running|走って/.test(text)&&/どこ|場所|コース|ルート|where/.test(text))return [{ja:'走っている場所',en:'where you run'}];
 return [{ja:'「'+text.slice(0,80)+'」',en:'“'+text.slice(0,80)+'”'}];
}
export function missingFactsSentence(subjects,language){
 const unique=[...new Map(subjects.map(s=>[s[language],s])).values()];
 return unique.map(s=>language==='ja'?s.ja+'は、まだ情報が登録されていません。':'There is no registered information about '+s.en+'.').join('\n');
}
