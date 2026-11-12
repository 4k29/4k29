# 公開可能な人手宿泊対話の確保とCE比較

公開研究checkpointに使えるASDC原文を取得し、条件確認に限定した全CE／返答CEの実モデルpilotを完了した。新DEVの具体応答は両方0/15。返答CEの本文DEV NLLは全CEより低いが、条件を利用する自然な応答の獲得は確認できなかった。正式採用・公開モデル置換はNo-Goを維持する。

## 取得・権利

ASDCの原配布元は [megagonlabs/asdc](https://github.com/megagonlabs/asdc/tree/f37d6575c73602adcb8ae3687520726793baa672)。固定revision `f37d6575c73602adcb8ae3687520726793baa672`、公式READMEのLicense節と完全なLICENSEを確認した。コーパス・注釈・文書はCC BY 4.0、プログラムはApache2.0。Yuta Hayashibe / Megagon Labs、LREC2022/NLP2021への帰属と加工記録を保持する。今回の元の架空対話について、学習・加工・再配布・公開研究checkpointと矛盾する追加禁止条件は見つからなかった。一般的なCC表示を第三者の記事等の包括的な権利確認とは扱わない。

公式archiveは9,233,018 bytes、展開90,835,597 bytes、1590ファイル。`ACQUISITION.json` に取得時刻・revision・全ファイルSHAを保存した。本文全体の取得とTRAIN採用を区別する。

- main：210会話（公式TRAIN125 / DEV41 / TEST44）。架空の宿泊相談を人間が演じた資料。
- vanilla：74,799単位。質問だけ・案内役の質問→顧客の回答が多く、74,799件のassistant教師ではない。
- supplemental utterances：51,390単位。意味正規化SCUD注釈をassistant回答へ流用しない。
- 公式TRAIN/DEVから読み取った112,288単位のうち、実際の顧客→案内役の返信位置は36,476。これも未審査の母集団であり採用量ではない。

[ニュース雑談](https://github.com/fukanarita/newschat-with-impression/tree/fd09d8a7cad99449c5353447b785985fe8ac9a32) は公式MIT表記を確認したが、README例でも `used_tweet=[]` の発話に記事の引用が含まれる。tweetなしだけで第三者権利・外部事実が解消したとは判断せず、対話本文ファイルの取得・学習採用は0件。証拠は公式READMEとLICENSEへの参照であり、記事を新たな学習コーパスとして再配布していない。子育て協議会候補の公式サイトへの照会は403で未確認、FAQ採用0件。ichikaraとその派生原文は今回0件、学習・checkpointに含めていない。

## 審査と採用範囲

応答長・疑問表現等で候補を取得したが、proxyは品質合格に使用していない。固定seed・topic層別で477件を選択。自動保留342件、残る135件の履歴と返答をメインagentが全文読解した。品質保留51件、既知話者分離で追加保留3件、採用81件（TRAIN66 / DEV15）。未提供の宿の在庫・価格・設備・アレルギー対応を断定するもの、欠けた参照、入力にない数字、改変を要する誤字などを保留した。原文を修復して通していない。

採用TRAINは66文書・66 explicit family、返答本文2,058 BPE tokens、全serialized入力4,946 tokens（各BOSを含む）。モデルが読む非padding入力は4,880 positions。返答長は最短24、中央値30、最大48。main6、vanilla52、supplemental8。DEV15文書の返答本文450 tokens。新規取得した採用済み返答本文はTRAIN+DEV計2,508 tokensであり、112,288単位や候補全量を採用量へ加算しない。

採用応答は条件の言い換え、具体的な不足情報の質問、仮の検索条件の提案である。TRAIN66件すべてがこの限定目的に有用と読解したが、「具体的な事実回答が100%」という意味ではない。14件は3発話以上の履歴、52件は複数の文を含む（相槌＋質問も含む記述統計）。理由を展開する回答・根拠付き比較・手順の十分な教師量は確保できていない。本格的な広範囲A/BはNo-Go、ユーザーが許可した条件確認pilotを実施した。採用不足は固定した審査範囲の結論であり、ASDC全体に有用な回答が存在しないという結論ではない。

別途、結果確認後に未採用の `situation.normal.extend` の形式を点検した。TRAIN/DEV746単位・context内の案内役候補2441位置は未採用であり、架空ホテルの属性を入力に根拠なく答える例や欠けた先行文脈があった。この探索は追加TRAIN・DEV・現比較へ混ぜていない。

## 入力・分割・再現性

元のhuman役割をcustomer/user→slot3、operator/agent→slot4へ対応づけ、執筆者IDとは分けた。slot4を全資料共通の万能assistantと再定義していない。宿泊案内役の架空の提案は、実際の予約・検索能力やAI自身の経験の証拠ではない。

出版社の `text_fixed` がある場合だけそれを使い、なければ `text`。文順・元の本文・発話EOSを保持。BOSから全履歴を使用し、context超過例は除外、左切断・文書連結・偽EOSはない。byte復元・独自BPE・shift・PAD/loss mask・原典の発話対応を全採用例で照合した。teacher位置の重複はなく一巡だけ。既存RealPersona TRAINとのcanonical返答一致0件。新TRAIN/DEVの質問・返答・explicit family交差を検査し、返答類似度0.85以上、直前ユーザー質問類似度0.8以上の交差は0件だった。意味familyの完全独立を保証する検査ではない。

MAINの既知operator/customer IDsはTRAIN6名分・DEV3名分で重複なし。ただしcrowd作業者IDは公開されていないため、81会話を81独立執筆者とは数えない。新DEVも独立母語話者評価・封印TESTではない。公開source TESTの形式確認例2件は事前に閲覧していたため記録し、今回のTRAIN/DEVから除外した。プロジェクト封印TESTは開いていない。

原取得1590ファイルのSHAをcacheで再確認して別ディレクトリからパイプラインを再構築し、DATA・teacher監査・DEV・splitの4ファイルがbyte完全一致した。追加の原文取得やモデルforwardはない。

## 実学習と保存

共通初期はPR #108 MIX-579の完全state（SHAは `CHECKPOINT_INDEX.json`）。独自11.23M、BPE3997、context256、継承AdamW moment/step6940、LR1e-5、clip1を固定。同一66入力・17batch・順序を一巡した。

- A：全causal CE、4,880有効教師。
- B：同一入力で返答本文2,058＋真EOS66のみ、2,124有効教師。履歴はAttentionに残る。
- 正規化は各batchの有効教師全体平均。教師数・勾配スケールの差を隠さず、TRAIN lossの数字だけを直接順位付けしない。

事前の実モデル検証では、A/B初回logits一致、Adam非共有、非対象logit勾配0、質問本文の非ゼロactivation勾配を確認。これは意味理解の証明ではない。別プロセスでの更新後再開が完全一致した。保持34更新、捨て原更新4、replay2、実optimizer呼出し40。forward実戻りは17,589、保存logitsの再利用0、初期の旧129生成と自己履歴4件はPR #108の保存済み結果を再利用した。失敗したoptimizer試行・保持更新の破棄は0。

A/Bそれぞれ9・17更新の全状態をatomic保存。計4state、各約134.84MB、5つの32MiB以下chunkへlossless分割し公開研究ブランチに保存。各stateについて新規bare Gitからremote-only cold復元し、chunk・全体SHA・model/Adam/全RNG/sampler/cursor/traceのdigestを照合した。共通初期と旧checkpointは変更していない。

無料public GitHub Actions CPUの [専用実行](https://github.com/4k29/4k29/actions/runs/43153937122) を使用。4論理CPU、Torch2 threads、GPUなし。開始時free約90.85GB、main process peak RSS1,362,612KiB、実モデル処理全体423.41秒。保持step内の実測時間合計はA4.69秒・B4.65秒であり、評価・保存・Git転送を含む全体時間とは分ける。元の作業環境のroot空き0を無視して学習せず、そこではRAM上でデータ処理だけを行った。

## 生成結果と解釈

返答本文DEV NLLは初期5.264289→A4.975131 / B4.924391。しかし新DEVは0/15→両方0/15。たとえば草津の4名2部屋の条件には両方「そうなんですね。」のみで、部屋タイプなど必要な具体確認を生成できない。Bではサロマ湖の希望に「お店の中で…」を反復した。返答NLLの低下を条件利用の成功とは認めない。

captionは両方21/32、共通初期の合格21件をすべて保持、新規合格・退行とも0件。ただし生出力は複数入力で変化しており、件数だけの比較ではない。全32件をprefixと合わせて読み、旧保守的基準を維持した。短い語尾補完と、意味のある段落は区別する。

新段落0/5、展開文章0/45、内容必須0/24、資料付き0/23、自己履歴0/4。新DEVのEOS出現は15→13/15へ減少し、4gram反復proxyは6→A10/B11へ増加した。proxyと人間の有害反復率は同一視しないが、実出力にも「お昼間」「海道」等の無意味な反復がある。EOS・文法的な短い問い返しがあっても、必要内容の欠落は失敗とした。

全文・全token・raw bytes・停止理由を保存し、終端の各144生成と自己履歴4エピソードを評価した。旧結果とtoken完全一致したものは判定を再利用し、変更例は全文または同一反復をlossless圧縮した表示で読解した。生出力は変更していない。評価はメインassistantの非盲検判定であり、人間による独立評価は未実施。

返答CEはこの小標本では同じ返答DEV位置のNLLが約0.05低かったが、内容応答の優位性は示していない。両方のcaption保持だけから、全CE・返答CE一般の優劣も結論できない。全34保持更新でclip発生、勾配中央値A4.931/B6.279。maskの実装不具合や履歴へのAttention遮断は検出されていない一方、質問の意味を利用する能力を獲得した証拠もない。2,058本文tokensの一巡と低LRでは、教師の量・多様性、基盤能力、最適化、容量を切り分けられない。

公開可能な原文・保存先・実A/B経路は成立した。広範な本学習・正式採用・公開モデル置換はNo-Go。追加epochやLR調整へ自動で進まず、次の優先研究を `NEXT_STRATEGY.md` に1件だけ定めた。

## 検証成果物

学習専用CIで4つの入力契約テストと実モデルpreflightを通過した。追加の証拠整合CIは `verify_results.py` により、40実呼出し・34保持・一巡66入力・各mask教師数・4つのcold state・無修正144生成×2・forward ledgerを検査する。ローカル検査と原文からの完全再構築は合格。最終CIのrun URL・結論は `CI_RECEIPT.json` に保存する。旧他sourceの530窓NLLや新しいPython/JS数値比較は再実行していない。source別NLLの分解はASDC内部のmain/vanilla/supplementalであり、3つの独立sourceの比較とは呼ばない。
