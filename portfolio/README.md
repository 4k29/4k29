# Shika Portfolio

自己紹介、Tecircの紹介、記事、写真、プロフィールリンクの順に進む静的サイトです。ホイール、トラックパッド、スワイプ、矢印キーで前後の場面へ移動できます。写真と記事はタイトルバー付きのウィンドウで一斉に開きます。ウィンドウを選ぶと一角を基点に拡大し、周囲は元の大きさのまま押し出されます。タイトルバーはドラッグでき、素早く放すと少し滑ります。余白をクリック・タップするか、Escapeキーを押すと一覧へ戻ります。

## ローカル起動

リポジトリのルートで実行します。

```sh
node portfolio/build.mjs docs
python3 -m http.server 4173 --directory docs
```

[http://localhost:4173/](http://localhost:4173/) を開きます。追加パッケージやAPIキーは不要です。

## コンテンツの編集

- `src/content.js` の `profile` で自己紹介、関心分野、プロフィールリンクを編集できます。冒頭の名前と肩書きは `src/index.html` にあります。
- `photos` に画像パス、ファイル名、代替テキスト、元画像の幅と高さを登録します。横写真と縦写真の両方に対応しています。
- `articles` にTecircの公開URL、アイキャッチ、タイトル、日付を登録します。16:9以外のアイキャッチには `ratio`（横÷縦）を指定します。
- `projects` にタイトル、公開URL、説明、必要に応じて画像を登録します。画像は `docs/assets/` に置いてください。
- スタイルは `docs/style.css`、描画と操作は `src/app.js` と `src/motion.js` にあります。配色は端末の設定に連動します。「視差効果を減らす」などを有効にすると各場面へ即座に移動します。

## ブラウザテスト

`tests/browser.html` を配信先のフォルダに `qa.html` として一時コピーし、ブラウザで **Run browser checks** または **Check galleries** を選びます。デスクトップ、タブレット、390px幅での描画と、写真・記事の拡大とグリッドへの復帰を検査します。

文字スクランブルの参考は [DesignBookmark Motion Studies](https://designbookmark.com/motion#db-scramble-text) です。

本文に現れる文字断片の点滅は Recent の [Type Flicker Animation](https://recent.design/i/tbkt6wk-type-flicker-animation) を参考にしています。
