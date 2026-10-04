# モデルへ学習した製品仕様

確認日2026-10-04。値・条件・公式出典・本文の抜粋は `training/product-specifications.json`。実行時の情報取得は行わず、自作モデルの重みと同梱メモリーを使う。

| 製品 | 学習した主な値 | 公式出典 |
| --- | --- | --- |
| 元のCMF Buds | Bluetooth 5.3、AAC/SBC、最大42dB ANC、IP54、ANCオフ単体8h／ケース込み35.5h、オン5.6h／24h、バッテリー45／460mAh、USB-C、無線充電なし、2台接続 | [CMF公式Budsカテゴリ](https://support.cmf.tech/hc/en-us/categories/22758549066001-Buds) のProduct Feature節。Buds Pro・Pro 2とは別カテゴリを確認。各FAQのURLは値ごとに保存。 |
| Nothing Headphone (1) | 40mm、16Ω、329g、Bluetooth 5.3、AAC/SBC/LDAC、IP52、1040mAh、AAC ANCオン35h／オフ80h、LDACオン30h／オフ54h、USB-C／3.5mm接続、2台接続 | [Nothing日本公式](https://jp.nothing.tech/products/headphone-1)。表示本文と公開HTMLの製品仕様データを確認。 |
| Beats Fit Pro | ANC、IPX4（イヤホン本体のみ。ケース非対応）、5分充電で最大1h | [Apple耐汗・耐水](https://support.apple.com/en-us/101579)、[Apple充電と再生時間](https://support.apple.com/guide/beats/about-charging-and-playback-time-devc8a939c17/web) |
| kyu camera | 32GB、115g、1000mAh、前1080p／後720p（各1:1、30fps）、114.3×57.4×15.6mm、USB-C | [kyu公式製品ページ](https://kyu-o.com/products/kyu-camera) のTechnical specifications。本人が所有するとは扱わない。 |

Beats Fit Proの販売ページはPowerbeats Fitへ転送される。現行公式ガイドのケース込み再生時間について元のFit Proの仕様の裏取りが完了していないため、総再生時間は学習・回答せず保留する。後継機の値で補わない。

再生時間はメーカーの最大値。CMFのテスト条件はAAC・音量50%・25°Cで、モデル内に保存。ケース込み／単体、ANCの状態、Nothingのcodecごとの差を分ける。メーカー価格を本人の購入金額と見なさず、購入歴・所有の未共有情報も補わない。
