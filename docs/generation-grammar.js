// Authored grammar paths used for statistical training. {value} is an atomic,
// registered fact span. These paths add phrasing, never biographical information.
const ja={
 name:['名前は{value}です。','{value}といいます。','{value}です。','呼び名は{value}です。','{value}と呼んでください。','名前として{value}を使っています。','{value}という名前で活動しています。','私の名前は{value}です。','使っている名前は{value}です。','呼んでもらうときは、{value}でお願いします。'],
 role:['現在の身分は{value}です。','{value}です。','現在は{value}です。','今は{value}として過ごしています。','現在の立場は{value}です。','職業については、{value}です。','今の身分は{value}です。','プロフィール上の職業は{value}です。'],
 tool:['{value}を使って制作しています。','制作には{value}を使っています。','{value}を制作に活用しています。','開発で使っているのは、{value}です。','{value}を使って開発を進めています。','制作のツールは、{value}です。','開発には{value}を活用しています。','{value}で制作を進めています。','使っている制作ツールは、{value}です。','制作では{value}を使います。'],
 workflow:['進め方は「{value}」です。','{value}の順で制作を進めます。','制作は「{value}」という流れです。','制作の手順は、{value}です。','{value}という手順で制作します。','{value}の流れで試しながら改善しています。','制作では、{value}の順に進めています。','開発は「{value}」の順で進めます。','{value}という流れで制作しています。','進める順序は、{value}です。'],
 responsibility:['{value}は自分で担っています。','{value}を担当しています。','自分が担当するのは、{value}です。','{value}は自分の担当です。','{value}を自分で行っています。','自分の役割は、{value}です。','{value}は自分が担う部分です。','本人が担当する部分は、{value}です。','制作では、{value}を自分で担当しています。','{value}は自分で確認し、担当しています。'],
 preference:['{value}を大切にしています。','{value}を重視しています。','大切にしているのは、{value}です。','{value}を意識しています。','制作では、{value}を大切にしています。','{value}を念頭に置いて制作しています。','重視するポイントは、{value}です。','制作で意識しているのは、{value}です。','{value}を大事にしています。','こだわりとして、{value}を挙げています。'],
 interest:['{value}に関心があります。','{value}に興味があります。','関心があるのは、{value}です。','{value}に興味を持っています。','{value}が気になっています。','興味のある対象は、{value}です。','{value}に関心を持っています。','気になっているのは、{value}です。','関心の対象として、{value}を挙げています。','{value}への関心があります。'],
 activity:['{value}に取り組んでいます。','{value}をしています。','活動として、{value}に取り組んでいます。','取り組んでいる活動は、{value}です。','普段の活動には、{value}があります。','{value}が活動の内容です。','普段は{value}をしています。','{value}という活動に取り組んでいます。','活動については、{value}を挙げています。','{value}が普段の活動です。'],
 hobbies:['趣味は、{value}です。','{value}が趣味です。','趣味として、{value}をしています。','趣味には、{value}があります。','楽しんでいる趣味は、{value}です。','趣味については、{value}を挙げています。','趣味として楽しんでいるのは、{value}です。','{value}を趣味として楽しんでいます。','趣味の活動は、{value}です。','{value}が趣味の内容です。'],
 product:['{value}を使っています。','使っている製品は、{value}です。','{value}を普段使っています。','愛用品は、{value}です。','{value}を使う製品として選んでいます。','普段使っているのは、{value}です。','{value}が使っている製品です。','{value}を愛用しています。'],
 audio:['{label}は、{value}を使っています。','使っている{label}は、{value}です。','{label}として、{value}を使っています。','{value}が使っている{label}です。','普段使う{label}は、{value}です。','{label}には{value}を選んでいます。','愛用している{label}は、{value}です。','{value}を{label}として使っています。','{label}については、{value}を使っています。','{value}が普段の{label}です。'],
 runningApp:['ランニング用のアプリは、{value}です。','ランニング用のアプリとして、{value}を使っています。','使っているランニングアプリは、{value}です。','{value}がランニング用のアプリです。','ランニングでは、{value}というアプリを使っています。','ランニングのアプリには、{value}を選んでいます。','ランニングに使うアプリは、{value}です。','{value}をランニング用のアプリとして使っています。'],
 runningShoes:['ランニング用の靴は、{value}です。','ランニングでは、{value}をシューズとして使っています。','ランニングシューズは、{value}を使っています。','{value}がランニング用の靴です。','走るときの靴は、{value}です。','ランニング用のシューズには、{value}を選んでいます。','ランニングで履いているのは、{value}です。','{value}をランニングシューズとして使っています。'],
 writing:['{value}について記事を書いています。','{value}をテーマに執筆しています。','記事で扱っているテーマは、{value}です。','{value}について書いています。','{value}が記事で扱っているテーマです。','執筆のテーマは、{value}です。','{value}についての記事を執筆しています。','記事では、{value}を取り上げています。','{value}を題材に記事を書いています。','{value}が執筆している内容です。'],
 website:['{value}から記事を選んで読めます。','{value}に記事をまとめています。','記事は{value}で探せます。','記事を読むなら、{value}をご覧ください。','記事の一覧は、{value}です。','{value}から記事を探せます。','記事を読む場所は、{value}です。','{value}で公開している記事を選べます。'],
 articleLink:['「{value}」を読めます。','該当する記事は「{value}」です。','「{value}」の記事はこちらです。','こちらの記事を案内できます：「{value}」','読める記事は「{value}」です。','「{value}」のリンクを案内します。','記事のタイトルは「{value}」です。','「{value}」の記事を紹介します。'],
 favorite:['推しは{value}です。','{value}が推しです。','好きな人は{value}です。','推しの名前は{value}です。','好きな人として挙げているのは、{value}です。','{value}が好きな人です。','推している人は、{value}です。','{value}を推しています。','好きな人物は、{value}です。','推しについては、{value}を挙げています。'],
 subscription:['契約しているサブスクは、{value}です。','サブスクとして、{value}を契約しています。','利用しているサブスクは、{value}です。','{value}をサブスクとして利用しています。','サブスクの契約は、{value}です。','契約中のサービスは、{value}です。','サブスクには、{value}を利用しています。','契約しているサービスは、{value}です。','{value}が契約中のサブスクです。','利用中のサブスクとして、{value}を挙げています。'],
 xMain:['X（Twitter）のメインアカウントは{value}です。','メインのX（Twitter）は、{value}です。','X（Twitter）では、{value}をメインに使っています。','メインアカウントのIDは、{value}です。','X（Twitter）の本アカウントは、{value}です。','メインのアカウントは{value}です。'],
 xSecondary:['サブアカウントは{value}です。','X（Twitter）のサブアカウントは、{value}です。','サブのアカウントは{value}です。','サブアカウントのIDは、{value}です。','X（Twitter）では、{value}をサブに使っています。','サブのX（Twitter）は、{value}です。'],
 siteStack:['{value}でこの自己紹介サイトを実装しています。','このサイトの技術構成は、{value}です。','この自己紹介サイトは、{value}で作っています。','実装に使っている言語は、{value}です。','このサイトは、{value}で実装しています。','{value}がこのサイトの技術構成です。'],
 siteEngine:['{value}で回答を組み立てています。','{value}を使ってこのチャットを実装しています。','{value}を用いて返答を構成しています。','{value}でこのチャットの返答を作っています。','回答の組み立てには、{value}を使っています。','このチャットは、{value}で回答しています。'],
 privacy:['{value}は外部に送信しません。','{value}を外部に送らず、ブラウザ内で扱っています。','{value}はブラウザ内で扱い、外部には送りません。','{value}を外部へ送信することはありません。','外部に送信しない情報は、{value}です。','{value}は外部に送らずに扱っています。']
};
const friendlyJa={
 name:['{value}だよ。','名前は{value}だよ。','{value}って呼んでね。','{value}っていう名前だよ。','呼び名は{value}だよ。','{value}で呼んでね。'],
 role:['今は{value}だよ。','{value}だよ。','現在の立場は{value}だよ。','今の身分は{value}だよ。'],
 tool:['制作には{value}を使っているよ。','{value}を使って作っているよ。','開発で使うのは、{value}だよ。','制作のツールは{value}だよ。','{value}で制作を進めているよ。','{value}を開発に使っているよ。'],
 workflow:['{value}の順で進めているよ。','制作の流れは「{value}」だよ。','{value}という手順で作っているよ。','進め方は「{value}」だよ。'],
 responsibility:['{value}は自分で担当しているよ。','自分の担当は{value}だよ。','{value}は自分で担っているよ。','自分がやっているのは、{value}だよ。'],
 preference:['{value}を大切にしているよ。','こだわっているのは、{value}だよ。','{value}を意識して作っているよ。','重視しているのは、{value}だよ。'],
 interest:['{value}に興味があるよ。','{value}が気になっているよ。','関心があるのは、{value}だよ。','{value}に関心があるよ。','興味のある対象は{value}だよ。','気になっているのは{value}だよ。'],
 activity:['{value}をしているよ。','普段は{value}に取り組んでいるよ。','活動は{value}だよ。','{value}が普段の活動だよ。'],
 hobbies:['趣味は{value}だよ。','{value}が趣味だよ。','趣味として{value}を楽しんでいるよ。','趣味には{value}があるよ。','{value}を趣味でやっているよ。','趣味の活動は{value}だよ。'],
 product:['{value}を使っているよ。','普段使っているのは{value}だよ。','愛用品は{value}だよ。','{value}を愛用しているよ。'],
 audio:['{label}は{value}を使っているよ。','使っている{label}は{value}だよ。','{value}が普段の{label}だよ。','{value}を{label}として使っているよ。'],
 runningApp:['ランニングのアプリは{value}だよ。','ランニングでは{value}を使っているよ。','使っているランニングアプリは{value}だよ。','{value}がランニング用のアプリだよ。'],
 runningShoes:['ランニングの靴は{value}だよ。','走るときは{value}を履いているよ。','ランニングシューズには{value}を使っているよ。','{value}がランニング用の靴だよ。'],
 writing:['記事では{value}について書いているよ。','書いているテーマは{value}だよ。','{value}をテーマに記事を書いているよ。','記事で扱う内容は{value}だよ。'],
 website:['記事は{value}で読めるよ。','{value}から記事を探してみてね。','記事の一覧は{value}だよ。','{value}で記事を選べるよ。'],
 articleLink:['「{value}」を読めるよ。','「{value}」の記事はこちらだよ。','案内する記事は「{value}」だよ。','記事のタイトルは「{value}」だよ。'],
 favorite:['推しは{value}だよ。','{value}が推しだよ。','好きな人は{value}だよ。','{value}を推しているよ。','推している人は{value}だよ。','{value}が好きな人だよ。'],
 subscription:['サブスクは{value}を使っているよ。','契約しているのは{value}だよ。','使っているサブスクは{value}だよ。','{value}をサブスクとして利用しているよ。'],
 xMain:['メインのXは{value}だよ。','Xのメインアカウントは{value}だよ。','メインでは{value}を使っているよ。','本アカウントは{value}だよ。'],
 xSecondary:['サブのXは{value}だよ。','サブアカウントは{value}だよ。','サブでは{value}を使っているよ。','Xのサブアカウントは{value}だよ。'],
 siteStack:['このサイトは{value}で作っているよ。','技術構成は{value}だよ。','このサイトの実装は{value}だよ。','{value}でこのサイトを実装しているよ。'],
 siteEngine:['{value}で答えを組み立てているよ。','回答には{value}を使っているよ。','このチャットは{value}で動いているよ。','返答は{value}で構成しているよ。'],
 privacy:['{value}は外部に送らないよ。','{value}はブラウザの中で扱っていて、外部には送らないよ。','{value}を外部へ送信することはないよ。','{value}はブラウザ内で扱い、外部には送らないよ。']
};
const extraFriendlyJa={
 name:['名前には{value}を使っているよ。','呼んでもらうときは{value}でお願い。','活動するときの名前は{value}だよ。','ハンドルネームは{value}だよ。','プロフィールの名前は{value}だよ。','呼ぶなら{value}でいいよ。'],
 role:['今の職業は{value}だよ。','プロフィールでは{value}として紹介しているよ。','現在は{value}として過ごしているよ。','立場としては{value}だよ。','職業については{value}だよ。','今の状況をいうと、{value}だよ。'],
 tool:['制作で使っているツールは{value}だよ。','{value}を制作に活用しているよ。','制作は{value}を使って進めているよ。','使っている開発ツールは{value}だよ。','ものを作るときは{value}を使っているよ。','制作に活用するのは{value}だよ。'],
 workflow:['進める順番は「{value}」だよ。','{value}という流れで制作しているよ。','開発では「{value}」の順に進めるよ。','制作は「{value}」に沿って進めているよ。','手順としては、{value}だよ。','{value}の流れで試しながら改善しているよ。','制作の手順は{value}だよ。','作るときは「{value}」の順だよ。'],
 responsibility:['制作で自分が担うのは{value}だよ。','{value}を自分の役割として担当しているよ。','本人の担当は{value}だよ。','{value}は自分が受け持っている部分だよ。','制作の中では、{value}を自分で行っているよ。','自分の役割として挙げるのは{value}だよ。'],
 preference:['大切にしているポイントは{value}だよ。','制作では{value}を重視しているよ。','{value}を意識しているよ。','大事にしているのは{value}だよ。','制作のこだわりは{value}だよ。','{value}を念頭に置いて作っているよ。'],
 interest:['興味を持っているのは{value}だよ。','{value}への関心があるよ。','関心の対象は{value}だよ。','プロフィールの関心事は{value}だよ。','{value}に興味を持っているよ。','好きなものや関心事として、{value}を挙げているよ。'],
 activity:['取り組んでいる活動は{value}だよ。','{value}に取り組んでいるよ。','普段の活動には{value}があるよ。','プロフィールで紹介している活動は{value}だよ。','日頃やっているのは{value}だよ。','活動として{value}を挙げているよ。'],
 hobbies:['趣味として挙げているのは{value}だよ。','{value}を趣味として楽しんでいるよ。','楽しんでいる趣味は{value}だよ。','趣味の内容は{value}だよ。','趣味でやっているのは{value}だよ。','プロフィールに挙げている趣味は{value}だよ。'],
 product:['使っている製品は{value}だよ。','{value}が使っている製品だよ。','普段の愛用品は{value}だよ。','製品として使っているのは{value}だよ。','{value}が普段使う製品だよ。','愛用しているものは{value}だよ。'],
 audio:['普段の{label}は{value}だよ。','{label}には{value}を選んでいるよ。','愛用している{label}は{value}だよ。','{label}については、{value}を使っているよ。','{value}を普段の{label}にしているよ。','{label}の製品名は{value}だよ。','{label}として挙げているのは{value}だよ。','{value}が使っている{label}だよ。'],
 runningApp:['走るときに使うアプリは{value}だよ。','ランニング用には{value}というアプリを使っているよ。','ランニングのアプリには{value}を選んでいるよ。','{value}をランニング用のアプリにしているよ。','ランニングで使っているアプリの名前は{value}だよ。','使うランニングアプリは{value}だよ。','ランニングのアプリとして挙げるのは{value}だよ。','アプリについては、ランニングに{value}を使っているよ。'],
 runningShoes:['走るときの靴は{value}だよ。','ランニングで履いているのは{value}だよ。','使っているランニングシューズは{value}だよ。','ランニング用のシューズは{value}だよ。','{value}をランニング用の靴にしているよ。','ランニングの靴として挙げるのは{value}だよ。','靴については、ランニングに{value}を使っているよ。','ランニングシューズの名前は{value}だよ。'],
 writing:['執筆のテーマは{value}だよ。','記事では{value}を取り上げているよ。','記事で書いているのは{value}だよ。','{value}を題材に書いているよ。','{value}が記事のテーマだよ。','ブログでは{value}について書いているよ。'],
 website:['記事を探すなら{value}を見てね。','記事をまとめているのは{value}だよ。','{value}に記事をまとめているよ。','記事の一覧を見られるのは{value}だよ。','記事を読む場所は{value}だよ。','{value}から読む記事を選んでね。'],
 articleLink:['該当する記事は「{value}」だよ。','「{value}」のリンクを案内するよ。','「{value}」の記事を紹介するね。','読める記事は「{value}」だよ。','リンク先の記事は「{value}」だよ。','この記事を読めるよ：「{value}」'],
 favorite:['推しの名前は{value}だよ。','好きな人物は{value}だよ。','推しとして挙げているのは{value}だよ。','好きな人として挙げるのは{value}だよ。','お気に入りの人物は{value}だよ。','推しについては、{value}を挙げているよ。'],
 subscription:['利用しているサブスクは{value}だよ。','サブスクの契約は{value}だよ。','契約中のサービスは{value}だよ。','サブスクとして{value}を契約しているよ。','{value}が契約中のサブスクだよ。','使っている契約サービスは{value}だよ。','サブスクとして挙げるのは{value}だよ。','サブスクの一覧は{value}だよ。'],
 xMain:['Xで使っている本アカウントは{value}だよ。','メインアカウントのIDは{value}だよ。','X（Twitter）では{value}がメインだよ。','メインのアカウントは{value}だよ。','{value}をXのメインアカウントにしているよ。','メインのXアカウントとして挙げるのは{value}だよ。'],
 xSecondary:['サブアカウントのIDは{value}だよ。','X（Twitter）では{value}がサブだよ。','サブのアカウントは{value}だよ。','{value}をXのサブアカウントにしているよ。','サブのXアカウントとして挙げるのは{value}だよ。','Xで使っている別アカウントは{value}だよ。'],
 siteStack:['このサイトに使っている言語は{value}だよ。','{value}がこのサイトの技術構成だよ。','実装に使っているのは{value}だよ。','この自己紹介サイトは{value}で作っているよ。','{value}を使ってこのサイトを作っているよ。','このサイトを構成する技術は{value}だよ。'],
 siteEngine:['このチャットの仕組みは{value}だよ。','回答を作るときには{value}を使っているよ。','この返答は{value}で組み立てているよ。','回答の組み立てに使うのは{value}だよ。','{value}を使って返答を作っているよ。','このチャットの内部では{value}を使っているよ。'],
 privacy:['{value}はブラウザ内で処理して、外部には送らないよ。','{value}を外部に送ることはないよ。','ブラウザ内で扱う{value}は、外部には送信しないよ。','{value}は外部に送らず、このブラウザで扱っているよ。','外部に送信しないのは{value}だよ。','{value}を外に送らず、ブラウザ内で扱っているよ。']
};
for(const [kind,templates] of Object.entries(extraFriendlyJa))friendlyJa[kind].push(...templates);
const en={
 name:['My name is {value}.','You can call me {value}.','I go by {value}.','The name I use is {value}.','I am known as {value}.','The name on my profile is {value}.','I use the name {value}.','Call me {value}.'],
 role:['I am {value}.','I am currently {value}.','My current role is {value}.','At present, I am {value}.','My occupation is {value}.','My current status is {value}.'],
 tool:['I develop with {value}.','I make things with {value}.','I use {value} for development.','My development tools are {value}.','For making things, I use {value}.','The tools I work with are {value}.','I use {value} when creating things.','I build things using {value}.'],
 workflow:['My process is {value}.','I work through {value}.','I follow this sequence: {value}.','My development workflow is {value}.','The steps I follow are {value}.','I create things in this order: {value}.','My approach follows {value}.','The sequence is {value}.'],
 responsibility:['I handle {value}.','I take care of {value}.','My contribution is {value}.','The part I handle is {value}.','I am responsible for {value}.','My own role covers {value}.','I personally handle {value}.','I take responsibility for {value}.'],
 preference:['I care about {value}.','I value {value}.','I pay attention to {value}.','My design priorities are {value}.','I keep {value} in mind when creating things.','What matters to me is {value}.','I focus on {value}.','My priorities include {value}.'],
 interest:['I am interested in {value}.','My interests include {value}.','I have an interest in {value}.','I am drawn to {value}.','The things I am interested in include {value}.','My interests are {value}.','I have an interest in these topics: {value}.','I am curious about {value}.'],
 activity:['My activities include {value}.','I spend time on {value}.','I take part in {value}.','I work on {value}.','The activities on my profile include {value}.','I am involved in {value}.','I do {value}.','My regular activities include {value}.'],
 hobbies:['My hobbies include {value}.','I enjoy {value} as hobbies.','For hobbies, I do {value}.','The hobbies on my profile are {value}.','I spend my leisure time on {value}.','My hobby activities include {value}.','I pursue {value} as hobbies.','For fun, I enjoy {value}.'],
 product:['I use {value}.','The products I use are {value}.','My go-to products include {value}.','I use these products: {value}.','My usual products include {value}.','The products on my profile include {value}.'],
 audio:['I use {value} as my {label}.','My {label} are {value}.','The {label} I use are {value}.','For {label}, I use {value}.','I use these {label}: {value}.','The {label} on my profile are {value}.','My choice of {label} is {value}.','I use {value} for my {label}.'],
 runningApp:['My running app is {value}.','I use {value} as my running app.','For running, I use the app {value}.','The running app I use is {value}.','I use this running app: {value}.','My app for running is {value}.','The app I use for running is {value}.','For a running app, I use {value}.'],
 runningShoes:['I use {value} for running.','My running shoes are {value}.','For running shoes, I use {value}.','The shoes I run in are {value}.','I wear {value} when running.','My shoes for running are {value}.','The running shoes I use are {value}.','I run in {value}.'],
 writing:['I write about {value}.','My articles cover {value}.','The subjects I write about are {value}.','My writing focuses on {value}.','I cover {value} in my articles.','The topics of my articles include {value}.','My article subjects are {value}.','I write articles on {value}.'],
 website:['You can read my articles at {value}.','My article list is at {value}.','You can find my articles at {value}.','Visit {value} to choose an article.','My articles are listed at {value}.','For my articles, see {value}.','The place to browse my articles is {value}.','You can browse articles at {value}.'],
 articleLink:['You can read “{value}”.','The article is titled “{value}”.','Here is the article “{value}”.','You can visit the article “{value}”.','The matching article is “{value}”.','The article title is “{value}”.','Here is a link to “{value}”.','Read the article “{value}”.'],
 favorite:['My favorite person is {value}.','The person I like is {value}.','A person I like is {value}.','The person I follow as a favorite is {value}.','My pick is {value}.','My favorite is {value}.','The person I name as my favorite is {value}.','I name {value} as my favorite person.'],
 subscription:['My subscriptions are {value}.','I subscribe to {value}.','The services I subscribe to are {value}.','The subscriptions I use are {value}.','My subscribed services include {value}.','I use these subscriptions: {value}.','The services on my subscription list are {value}.','I have subscriptions to {value}.'],
 xMain:['My main X (Twitter) account is {value}.','My primary X account is {value}.','On X (Twitter), my main account is {value}.','The handle of my main X account is {value}.','For my main X account, I use {value}.','My main account on X is {value}.'],
 xSecondary:['My secondary X (Twitter) account is {value}.','My secondary account is {value}.','My alt X account is {value}.','On X, my secondary account is {value}.','The handle of my secondary account is {value}.','My alternate account on X is {value}.'],
 siteStack:['This profile site is built with {value}.','This site uses {value}.','The site is implemented with {value}.','The technologies behind this site are {value}.','I use {value} to implement this site.','This site is made with {value}.'],
 siteEngine:['This chat composes answers with {value}.','The dialogue engine uses {value}.','This chat builds replies using {value}.','Replies are composed from {value}.','This chat generates its responses with {value}.','The answer generation uses {value}.'],
 privacy:['This site does not send outside the browser: {value}.','This site keeps the following inside the browser: {value}.','These stay inside the browser: {value}.','This site does not send {value} externally.','The following are not sent externally: {value}.','This site handles {value} inside the browser.']
};
// Descriptive variants explain the registered relation, not an invented reason.
const detailJa={
 name:['プロフィールで使っている名前は、{value}です。','呼び名については、{value}という名前を使っています。'],
 role:['職業や現在の立場については、プロフィールでは{value}として紹介しています。','現在の身分として登録しているのは、{value}です。'],
 tool:['制作を進めるときのツールとして、{value}を使っています。','制作や開発に活用しているツールは、{value}です。'],
 workflow:['制作の進め方は「{value}」です。この順で試しながら改善しています。','開発でたどる手順は、{value}です。この流れで制作を進めています。'],
 responsibility:['制作で自分が担当している範囲は、{value}です。','本人の役割として、{value}を自分で担っています。'],
 preference:['制作で大切にしているポイントとして、{value}を挙げています。','デザインや使い心地については、{value}を重視しています。'],
 interest:['プロフィールに登録している関心の対象は、{value}です。','興味を持っている対象として、{value}を挙げています。'],
 activity:['普段取り組んでいる活動として、{value}を挙げています。','プロフィールで紹介している活動は、{value}です。'],
 hobbies:['趣味としてプロフィールに挙げているのは、{value}です。','楽しんでいる趣味の活動には、{value}があります。'],
 product:['プロフィールに登録している愛用品は、{value}です。','普段使っている製品として、{value}を挙げています。'],
 audio:['普段使っている{label}として、{value}を挙げています。','{label}について、プロフィールに登録している製品は{value}です。'],
 runningApp:['ランニングで利用しているアプリとして、{value}を挙げています。','ランニング用のアプリについては、{value}を使っています。'],
 runningShoes:['ランニングのときに使っているシューズは、{value}です。','ランニング用の靴として、プロフィールには{value}を登録しています。'],
 writing:['記事を執筆するときに扱っているテーマは、{value}です。','記事の内容としては、{value}について書いています。'],
 website:['公開している記事の一覧は、{value}です。ここから読む記事を選べます。','記事をまとめて読める場所は、{value}です。リンクから一覧を確認できます。'],
 articleLink:['該当する記事の正式なタイトルは「{value}」です。リンクから読めます。','確認できる記事として「{value}」を案内します。リンクから記事を開けます。'],
 favorite:['プロフィールで好きな人、推しとして挙げているのは、{value}です。','推しについては、{value}という人を挙げています。'],
 subscription:['契約中のサブスクリプションとして、{value}を挙げています。','利用しているサブスクの一覧には、{value}があります。'],
 xMain:['X（Twitter）でメインとして使っているアカウントは、{value}です。','メインアカウントとして登録しているX（Twitter）のIDは、{value}です。'],
 xSecondary:['X（Twitter）でサブとして使っているアカウントは、{value}です。','サブアカウントとして登録しているX（Twitter）のIDは、{value}です。'],
 siteStack:['この自己紹介サイトの実装に使用している技術は、{value}です。','このサイトを構成している言語として、{value}を使っています。'],
 siteEngine:['このチャットの回答を組み立てる仕組みとして、{value}を使っています。','回答生成の内部では、{value}を用いて返答を構成しています。'],
 privacy:['会話の中で扱う{value}は、このブラウザ内で処理し、外部には送信しません。','このサイトで扱う{value}については、外部へ送信しない仕組みです。']
};
const rows=[];
function add(language,kind,templates,style='polite',detail=false){
 for(const [index,template] of templates.entries())rows.push({id:language+':'+kind+':'+style+':'+(detail?'detail':'normal')+':'+index,language,kind,style,detail,template,quality:index<4?1:.92,weight:index<4?6:3});
}
for(const [kind,templates] of Object.entries(ja)){add('ja',kind,templates);add('ja',kind,friendlyJa[kind],'friendly');add('ja',kind,detailJa[kind],'polite',true);add('ja',kind,detailJa[kind].map(t=>t.replace(/しています/g,'しているよ').replace(/使っています/g,'使っているよ').replace(/挙げています/g,'挙げているよ').replace(/進めています/g,'進めているよ').replace(/読めます/g,'読めるよ').replace(/選べます/g,'選べるよ').replace(/確認できます/g,'確認できるよ').replace(/開けます/g,'開けるよ').replace(/案内します/g,'案内するよ').replace(/送信しません/g,'送信しないよ').replace(/です/g,'だよ')),'friendly',true);}
for(const [kind,templates] of Object.entries(en)){
 add('en',kind,templates);
 // English keeps a natural conversational register, without adding enthusiasm or facts.
 add('en',kind,templates.slice(0,4).map(t=>t.replace(/I am /g,"I'm ").replace(/I have /g,"I've ")),'friendly');
 add('en',kind,templates.slice(0,2).map(t=>'In my profile, '+(t.startsWith('I ')?t:t[0].toLowerCase()+t.slice(1))),'polite',true);
}
export const generationGrammar=rows;
