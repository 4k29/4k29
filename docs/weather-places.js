// Spelling aliases only. Coordinates always come from the geocoding service or browser permission.
const cities=[
 ['東京|とうきょう|東京都','Tokyo'],['大阪|おおさか|大阪市','Osaka'],['京都|きょうと|京都市','Kyoto'],
 ['札幌|さっぽろ|札幌市','Sapporo'],['横浜|よこはま|横浜市','Yokohama'],['名古屋|なごや|名古屋市','Nagoya'],
 ['福岡|ふくおか|福岡市','Fukuoka'],['神戸|こうべ|神戸市','Kobe'],['仙台|せんだい|仙台市','Sendai'],
 ['広島|ひろしま|広島市','Hiroshima'],['千葉|ちば|千葉市','Chiba'],['さいたま|さいたま市','Saitama'],
 ['那覇|なは|那覇市','Naha'],['金沢|かなざわ|金沢市','Kanazawa'],['新潟|にいがた|新潟市','Niigata'],
 ['長野|ながの|長野市','Nagano'],['静岡|しずおか|静岡市','Shizuoka'],['岡山|おかやま|岡山市','Okayama'],
 ['熊本|くまもと|熊本市','Kumamoto'],['鹿児島|かごしま|鹿児島市','Kagoshima'],['長崎|ながさき|長崎市','Nagasaki'],
 ['松山|まつやま|松山市','Matsuyama'],['高松|たかまつ|高松市','Takamatsu'],['大分|おおいた|大分市','Oita'],
 ['宮崎|みやざき|宮崎市','Miyazaki'],['函館|はこだて|函館市','Hakodate'],['旭川|あさひかわ|旭川市','Asahikawa']
];
export function placeQuery(name){
 const key=name.normalize('NFKC').trim();
 const city=cities.find(([aliases])=>aliases.split('|').includes(key));
 return {name:city?city[1]:key,japanese:/[ぁ-んァ-ヶ一-龠]/.test(key),exactName:city?city[0].split('|')[0]:key};
}
