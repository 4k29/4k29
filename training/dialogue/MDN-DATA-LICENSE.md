# MDN由来の抽出文章

`mdn-language-documents.jsonl` のMDN由来の文章・見出しは、MDN contributorsによる著作物を加工したものです。各ページのタイトル、URL、出典、加工内容は `mdn-language-sources.json` に記録しています。

MDNの[著作権・利用条件](https://developer.mozilla.org/en-US/docs/MDN/Writing_guidelines/Attrib_copyright_license)は、文書をCC BY-SA 2.5またはそれ以降の版で利用できるとしています。この抽出文章は[Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/)で提供します。再配布・改変時は出典、利用条件へのリンク、変更点を示し、同じ利用条件を適用してください。

本文の見出しと段落をHTMLから抽出し、空白を正規化しました。コードブロック・表・ナビゲーション・フィードバック・画像・添付ファイルを除いています。原文全体の完全な複製ではありません。ロゴや商標、ウェブサイトのデザインの利用権は含みません。

このデータは `binding-corpus.json` と `binding-candidate.js` の学習には使用していません。続く `continuous-corpus.json` では、MDN由来の原文トークン列と要約したQAラベルに出典とCC BY-SA 4.0を記録して学習へ使用します。翻訳案内・ブラウザー対応の定型案内を追加で除き、元の本文と加工後のSHAを保存します。自作プログラムや既存の政府由来データへ、このファイルの利用条件を一括して適用するという意味ではありません。MozillaやMDNが本モデルを作成・推奨したという意味でもありません。
