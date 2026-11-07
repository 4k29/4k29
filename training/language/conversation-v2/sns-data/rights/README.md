# SNS・日本語会話資料の権利監査

確認日：2026-10-27 JST。`matrix.json`は12ソースについて、取得・保存・学習・再配布を別々に判定し、API、返信構造、制限、削除、プライバシー、継続性を記録した。一次資料URL・日時・HTTP・SHAは`fetch-receipt.json`、詳細な技術上の注意と同意取得設計は`RESEARCH_NOTES.md`。**ライブSNS投稿の取得は0件。公開APIだけを学習許諾と解釈していない。**

| 原典 | 取得・保存 | 学習 | 原文/派生資料の再配布 |
|---|---|---|---|
| Bluesky | APIは存在。今回の学習目的の保存権限は未確認 | 投稿者の権利を維持し、Blueskyへの限定許諾。第三者への一括許諾は未確認 | 未確認、保留 |
| Mastodon / Misskey | 公開APIは存在。各サーバー・原投稿者の条件が別途必要 | 未確認、保留 | 未確認、保留 |
| X | 契約・プラン依存。今回取得しない | Developer Agreementのfoundation/frontierモデル学習禁止によりNo-Go | IDs原則等の制限。本文資料として取得しない |
| Reddit | 承認用途の範囲内のみ。今回取得しない | Data API2.4で権利者の明示許諾が必要。未取得のためNo-Go | 一括再配布権は未確認 |
| JMultiWOZ | CC BY-SA4で候補取得可能 | 出版者は学習モデルをdatasetの複製/直接派生とみなさない旨を明記 | 出典・ライセンス・変更表示・継承条件を保持 |
| MRMPC | CC BY-SA4。会話のみ、属性プロフィールは取得しない | 候補処理可。ただし3話者形式・品質・プライバシーは別ゲート | CC条件と個人権利を保持。再特定・なりすまし禁止 |
| OASST2の原日本語 | dataset cardがApache2。synthetic等の原注釈を保持し、人間候補の原文のみ | 非合成/原日本語/全祖先条件・品質確認が必要 | Apache2本文・出典・変更表示を保持。個人情報/第三者転載は別問題 |
| NUCC | CC BY-NC-ND4 | 今回の公開派生コーパス/将来サービス用途を確認できず保留 | 改変配布条件が不適合。原文未取得 |
| Japanese Daily Dialogue | 研究限定、CC BY-NC-ND4 | READMEがchatbotサービス利用禁止。今回No-Go | READMEが再配布禁止。本文未取得 |
| JMRD / RealPersona | 既存資料、今回の新規取得量へ加算しない | 既存監査を維持 | 既存ライセンス条件を維持 |
| DeepL翻訳OASST派生 | メタデータ確認のみ | 人間の日本語原文として採用しない | 今回再配布しない |

JMultiWOZは許諾確認済みだが、別配布TRAINを確認できず、公式TESTを含む一括zipは取得していない。取得量へ加算しない（`jmultiwoz-selective-access.json`）。

一次資料の重要箇所：

- `evidence/x_agreement.txt`： “use the X API or X Content to fine-tune or train a foundation or frontier model” が禁止項目に含まれる。
- `evidence/reddit_data.txt`： “without the express permission of rightsholders” のML/AI学習利用は許諾されない。
- `evidence/bluesky_terms.txt`：投稿者が権利を保持し、Blueskyへ限定ライセンス。これを第三者への許可と拡張しない。
- `evidence/nu-dialogue-jmultiwoz-README.md.txt`：dataset CC BY-SA4と、学習済みモデルの扱いを明記。
- `evidence/OpenAssistant-oasst2-README.md.txt`：dataset `license: apache-2.0`。`rights/DATA-LICENSE.md`に本文・NOTICE調査を記録。

## 検証できなかった条件を許諾扱いしない

Mastodon.socialとMisskey.ioのterms/privacyページはHTTP200でもJavaScriptアプリ殻だった。実質的な規約は読めていない。Blueskyのrateページも一部リダイレクトで本文がないため、公式GitHubドキュメントから別途確認した。PDSの3000 requests/5分をAppViewの枠と混同しない。Mastodon公式既定は300 requests/5分（account/IP）だがサーバー変更がある。Misskeyの1–100は結果件数で、リクエスト/秒ではない。

Blueskyのreply.parent/root、Mastodonのin_reply_to/context、MisskeyのreplyIdを区別する。Misskeyのchildrenは引用renoteも返し、MRMPCのmention_toも正確な親投稿とは異なる。返信構造の存在は意味的な応答の証明ではない。

## 削除・個人情報・帰属

元IDから派生文書・token窓まで追跡し、削除/公開範囲変更/申立ての対象と、文脈を失う子孫を除外する。発話削除後の前後を新たな返信として接続しない。原文をGitへ公開すると履歴からの完全削除が難しいため、未確認の個人情報を公開しない。denylistは学習済みモデルからの忘却を保証しない。別サービス横断で話者同定しない。

CCの帰属・変更表示・継承を維持する。匿名化は著作権許諾を代替せず、CC/Apacheもプライバシーや無断転載を自動的に解決しない。**原典の権利確認済みでも品質・形式・分割が未確認ならTRAINへ採用しない。**
