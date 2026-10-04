// Supervised question examples for a small local TF-IDF intent retriever. These are questions, not canned answers.
import {expandedIntentExamples} from './intent-expansion.js?v=20261004-transformer-7';
const coreIntentExamples=[
 {id:'hobbies',facts:['photo','running'],examples:['趣味についてもう少し教えて','tell me about your hobbies']},
 {id:'interests',facts:['apple','nothing','openai','tech','ui','design','hci','slm','context'],examples:['どんなことにハマってる','今ハマっているものは','最近のマイブームは','どのようなことに関心を持っていますか','何に興味がある','関心のあるものを知りたい','熱中していることを教えて','what are you interested in','what catches your attention']},
 {id:'interest-fields',facts:['tech','ui','design','hci','slm','context'],examples:['気になっている分野について聞きたい','関心のある領域を教えて','興味のある分野は','what fields are you interested in']},
 {id:'activities',facts:['tecirc','photo','running'],examples:['普段の過ごし方を教えて','暇な時にやっていることは','日頃はどんな活動をしていますか','余暇には何をして過ごしていますか','休日に楽しんでいる活動は','普段取り組んでいることが知りたい','what do you do in your spare time']},
 {id:'creative-process',facts:['workflow','iteration','taste'],examples:['どういう風に開発してるの','どんなふうに作品を作っている','制作はどのように進めているの','アイデアから完成までの進め方を知りたい','ものづくりの進め方を説明して','制作の手順を順に教えて','開発を進める流れを知りたい','how do you approach creating things','walk me through your development process']},
 {id:'creative-tools',facts:['workflow'],examples:['普段どんな技術を使ってる','制作で使用するツールは何ですか','普段使っている開発ツールを教えて','開発に使うソフトを知りたい','ものづくりで何のツールを使う','どの生成AIを制作で利用していますか','what tools do you use for development']},
 {id:'creative-division',facts:['workflow','taste'],examples:['ものづくりではどこを自分で決めてる','開発ってAIに指示するだけ','全部AIに任せているのか本人の担当も知りたい','AIで制作するときあなたは何を考えるの','AIとの協力で自分は何をするの','作るとき本人が判断する部分は','AI任せではなく自分で担当することは','what is your own contribution when building with AI']},
 {id:'design-principles',facts:['defaults','spacing'],examples:['デザインで重視してるポイントを具体的に','UIの使い心地で気をつけていること','設計するときに意識しているポイントは','デザインへのこだわりを聞かせて','開発において何を大切にしてる','制作で重視する見た目と使い勝手を知りたい','what matters to you in interface design']},
 {id:'article-subjects',facts:['tecirc','tecirc-subjects','tecirc-link'],examples:['記事は何をテーマに書くの','どんな内容の記事を書いてる','執筆しているテーマについて教えて','記事の内容を知りたい','ブログで書いている話題を知りたい','what do your articles focus on']},
 {id:'article-link',facts:['tecirc-link'],examples:['記事を読むにはどうしたらいい','あなたの記事が読みたい','執筆した文章を読みたい','ブログへ行くにはどうしたらいい','記事が読める場所を教えて','where can I find your writing']},
 {id:'products',facts:['earphones-beats','earphones-cmf','headphones'],examples:['愛用しているものを知りたい','普段使いのヘッドホンを教えて','よく使っているガジェットは','いつも身につけているヘッドフォンは','お気に入りの愛用品は','what headphones do you use']},
 {id:'social',facts:['x','x-secondary'],examples:['SNSでつながりたい','ツイッターでフォローしたい','あなたのアカウントを知りたい','Xのユーザー名を教えて','どのSNSで連絡できますか','where can I follow you']},
 {id:'chat-mechanism',facts:['site-engine'],examples:['このチャットはどうやって答えているの','返事を生成する方法を知りたい','この返答の裏側では何をしていますか','会話ができる仕組みを知りたい','how does this chat generate its replies']},
 {id:'chat-privacy',facts:['site-privacy'],examples:['チャットの入力はどこに送られるの','このサイトの会話データの扱いが知りたい','端末情報はサーバーに送信していますか','入力した内容は外部へ送信されますか','会話が外部に流れることはありますか','does this site send my messages anywhere']}
];
export const intentExamples=[...coreIntentExamples,...expandedIntentExamples];
