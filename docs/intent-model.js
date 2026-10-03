import {canonicalReading} from './japanese-reading.js?v=20261003-weights-5';
// An explainable local intent model, not a language model. Every rule points to registered fact IDs.
export const semanticModel={
 synonyms:[
  ['(?:きみ|君|あんた|そちら|お前)','あなた'],['(?:だれ|ダレ|どなた)','誰'],
  ['何処','どこ'],['(?:やってん|やっている|やってます)','やってる'],
  ['(?:してん|している|しています)','してる'],['(?:作ってん|作っている|作っています)','作ってる'],
  ['(?:興味を持って|関心を持って|夢中)','興味'],['気になって(?:いる|る)','気になる'],['(?:チャットジーピーティー|チャットgpt)','chatgpt'],['コーデックス','codex']
 ],
 concepts:{
  self:/あなた|しか|4k29|\b(?:you|your|u)\b/,
  who:/誰|何者|どんな人|\bwho\b/,
  overview:/自己紹介|どういう人|どんな(?:人|やつ|奴)|何者|プロフィール|あなた(?:のこと|について)|introduce|about (?:you|yourself)/,
  role:/職業|仕事|学生|社会人|会社員|働いて|働く|何してる人|何やってる人|生業|\b(?:job|occupation|student)\b|do for (?:work|a living)/,
  activity:/活動|趣味|休日|暇|余暇|普段|日頃|何(?:を)?(?:して|やって|作)|制作物|作ってるもの|\b(?:hobb(?:y|ies)|activities)\b|do (?:for fun|in your free time)/,
  interest:/好き|興味|関心|気になる|注目|\b(?:interest(?:s|ed)?|like|love|favorite|favourite)\b/,
  broad:/何(?:が|に|を)|どんな(?:もの|こと|分野)|好きな(?:もの|物|分野)|どの(?:分野|メーカー|ブランド)|どれ|\b(?:what|which)\b/,
  brand:/メーカー|ブランド|企業|会社|\bbrands?\b/,
  create:/形に|アイデアから完成|ものづくり|作|制作|開発|プログラミング|コード|コーディング|\b(?:make|build|creat\w*|develop\w*|cod\w*)\b/,
  how:/どう(?:やって|いう流れ|進め|作|開発)|どう協力|どんな(?:手順|流れ|方法|工程)|手順|進め方|プロセス|工程|流れ|\b(?:how|process|workflow|steps)\b/,
  ai:/ai|chatgpt|codex|人工知能|生成ai/,
  human:/自分|本人|人間|あなた|人の|\b(?:you|human|yourself)\b/,
  responsibility:/役割|担当|分担|任せ|丸投げ|協力|何(?:を)?(?:する|してる|している|考える)|\b(?:responsibility|division|role|delegate)\b/,
  web:/web|ウェブ|サイト|ホームページ|\bwebsite\b/,
  design:/デザイン|余白|ui|ux|使い心地|\bdesign\b/,
  values:/こだわ|大切|大事|重視|意識|気を(?:つけ|付け)|心がけ|心掛け|使いやす|\b(?:value|priorit\w*|care about|matters|principles)\b/,
  article:/記事|執筆|tecirc|テサーク|ブログ|\b(?:articles?|writing|blog)\b/,
  subject:/テーマ|内容|何(?:を|について)?(?:書|か)|(?:何|なん)(?:の|についての)記事|どんな(?:記事|ブログ)|\b(?:topics?|about|cover)\b/,
  where:/どこ|どちら|場所|\bwhere\b/,
  link:/リンク|url|読め|読む|読ん|読みたい|行く|アクセス|\b(?:link|read|visit)\b/,
  social:/sns|twitter|ツイッター|(?:^|[^a-z0-9_])x(?:$|[^a-z0-9_])|アカウント|垢|フォロー|連絡|\b(?:social|account|contact|follow)\b/,
  chat:/この(?:サイト|チャット|会話|回答)|対話|回答|返答|返事|喋|しゃべ|会話|\b(?:this (?:site|website|page|chat)|answer|reply|chatbot)\b/,
  implementation:/言語|構成|実装|技術|スタック|\b(?:stack|language|implemented)\b/,
  mechanism:/仕組み|動(?:いて|く)|生成|組み立|裏側|接続|つなが|繋が|\b(?:work|engine|generate|connected)\b/,
  privacy:/送信|外部|保存|プライバシー|個人情報|端末情報|\b(?:privacy|send|store|tracking)\b/,
  detail:/詳しく|詳しい|掘り下げ|具体的|深く|\b(?:detail|explain|elaborate)\b/,
  brief:/短く|一言|ひとこと|簡単に|ざっくり|要約|まとめ|\b(?:brief|briefly|summary|summarize|short)\b/
 },
 intents:[
  {id:'identity-name',patterns:[/^(?:ねえ?\s*|すみません\s*)?(?:あなた(?:って|は)?\s*)?誰(?:なの|なんだ|なんですか|なん|なんだよ|なんでしょうか|だ|だよ|だっけ|だったっけ|よ|やねん|です|ですか|でしょうか|か|なのか|なのかな|なのよ|様)?(?:教えて(?:ください)?|知りたい)?$/, /^(?:who (?:are|r) (?:you|u)|who is (?:しか|4k29|this)|who's this|tell me who you are|who you are)$/],facts:['name'],priority:100},
  {id:'identity-name',patterns:[/(?:何|なん)(?:と|て)(?:お)?呼|お呼び|呼ばれ|呼び方|お名前|名前|ニックネーム|ハンドルネーム|\b(?:name|nickname|call you)\b/],none:['social','brand'],facts:['name'],priority:70},
  {id:'identity-overview',all:['overview'],facts:['name','student','workflow','tecirc','photo','running'],priority:40},
  {id:'identity-role',all:['role'],facts:['student'],priority:60},
  {id:'daily-activities',all:['activity'],facts:['tecirc','photo','running'],priority:30},
  {id:'daily-activities',patterns:[/^(?:あなた(?:は|って)?\s*)?何(?:を)?(?:してる|やってる)(?:の|んですか|人)?$/, /^what do you do(?: for fun| in your free time)?$/],facts:['tecirc','photo','running'],priority:35},
  {id:'interest-brands',all:['interest','brand'],facts:['apple','nothing','openai'],priority:60},
  {id:'interest-general',all:['interest','broad'],none:['brand'],facts:['apple','nothing','openai','tech','ui','design','hci','slm','context'],priority:25},
  {id:'creative-tools',patterns:[/何(?:を)?使.*(?:作|開発|制作)|(?:開発|制作).*(?:何(?:を)?使|どのai)|which tools.*(?:make|build|develop)/],facts:['workflow'],priority:78},
  {id:'creative-output',patterns:[/何(?:を)?作|どんな(?:もの|作品|サイト).*作|what (?:do|have) you (?:make|build)|what are you (?:making|building)/],facts:['tecirc','photo'],priority:65},
  {id:'site-author',patterns:[/(?:このサイト|このページ|自己紹介サイト).*(?:誰.*作|誰.*制作|作者)|誰.*(?:このサイト|このページ).*(?:作|制作)/],facts:['name','workflow','taste'],priority:95},
  {id:'creative-process',all:['create','how'],facts:['workflow','iteration','taste'],priority:75},
  {id:'creative-process',patterns:[/制作スタイル|開発スタイル|制作方法|開発方法|バイブコーディング|vibe coding/],facts:['workflow','iteration','taste'],priority:65},
  {id:'creative-process',patterns:[/(?:制作|開発).*(?:考え方|スタンス)|(?:考え方|スタンス).*(?:制作|開発)|aiとの付き合い方/],facts:['workflow','iteration','taste'],priority:75},
  {id:'creative-division',all:['ai','responsibility'],facts:['workflow','taste'],priority:90,mode:'division'},
  {id:'human-contribution',all:['human','responsibility'],patterns:[/自分|本人|人間|\b(?:human|yourself)\b/],facts:['workflow','taste'],priority:80,mode:'division'},
  {id:'design-principles',all:['create','values'],facts:['defaults','spacing'],priority:74},
  {id:'design-principles',all:['design','values'],facts:['defaults','spacing'],priority:75},
  {id:'article-subjects',all:['article','subject'],facts:['tecirc','tecirc-subjects','tecirc-link'],priority:80},
  {id:'article-link',all:['article','link'],facts:['tecirc-link'],priority:85},
  {id:'article-link',all:['article','where'],facts:['tecirc-link'],priority:85},
  {id:'article-detail',all:['article','detail'],facts:['tecirc','tecirc-subjects','tecirc-link'],priority:75},
  {id:'chat-implementation',all:['chat','implementation'],facts:['site-stack'],priority:85},
  {id:'chat-mechanism',all:['chat','mechanism'],facts:['site-engine'],priority:90},
  {id:'chat-ai',all:['chat','ai'],none:['create','implementation','privacy'],facts:['site-engine'],priority:96},
  {id:'chat-privacy',all:['chat','privacy'],facts:['site-privacy'],priority:100}
 ]
};
export function semanticText(text){
 let result=canonicalReading(text);
 for(const [pattern,replacement] of semanticModel.synonyms)result=result.replace(new RegExp(pattern,'g'),replacement);
 return result.replace(/^[\s、,]*(?:ねえ|ねぇ|ちょっと|えっと|えーと)[\s、,]*/,'').replace(/[?？!！。]+$/,'').trim().toLowerCase();
}
export function resolveSemanticIntent(text,context,targeted=[]){
 const canonical=semanticText(text);
 const concepts=new Set(Object.entries(semanticModel.concepts).filter(([,pattern])=>pattern.test(canonical)).map(([id])=>id));
 // Resolve procedural follow-ups only when the antecedent is a registered creative activity.
 if(/^(?:それ|その|さっき)/.test(canonical)&&context.lastFactIds.some(id=>['workflow','iteration','taste'].includes(id))&&concepts.has('how'))concepts.add('create');
 const candidates=semanticModel.intents.filter(intent=>
  (!intent.all||intent.all.every(id=>concepts.has(id)))&&
  (!intent.none||intent.none.every(id=>!concepts.has(id)))&&
  (!intent.patterns||intent.patterns.some(pattern=>pattern.test(canonical)))
 ).sort((a,b)=>b.priority-a.priority);
 let best=candidates[0];
 const namedInterests=targeted.filter(f=>f.ja.relation==='interest');
 if(concepts.has('interest')&&!concepts.has('values')&&!concepts.has('create')&&namedInterests.length&&(!best||best.priority<60))best={id:'interest-entity',facts:namedInterests.map(f=>f.id),priority:60};

 const facts=[...(best?.facts||[])];
 if(best&&['creative-process','creative-division','human-contribution','design-principles'].includes(best.id)){
  for(const candidate of candidates)if(['creative-process','creative-division','human-contribution','design-principles'].includes(candidate.id))facts.push(...candidate.facts);
 }
 if(best&&['chat-mechanism','chat-implementation'].includes(best.id)&&/回答|対話|チャット|\b(?:answer|chat)\b/.test(canonical)){
  for(const candidate of candidates)if(['chat-mechanism','chat-implementation'].includes(candidate.id))facts.push(...candidate.facts);
 }
 return {canonical,concepts,factIds:[...new Set(facts)],intent:best?.id||null,priority:best?.priority||0,mode:best?.mode||(concepts.has('brief')?'brief':null)};
}
