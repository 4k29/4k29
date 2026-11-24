# Natural source boundaries and generation collapse

PR101の学習済み状態と凍結済み原文を再利用する隔離した研究。詳細設定はPLAN.json。正式採用の旧17/13/9・Pareto・反復上限は変更しない。

主な違いはデータ配分のみ。元のJaQuAD cut窓2slotを、原典の段落全体を保存した短いnative段落2slotに置換。共通JaQuAD1slotと共通RealPersona humanA/B1slotを保持。全slotの入力長・教師位置を一致させ、同じ3470 model/Adam/RNG/LR3e-5/clip1、512更新/379,767targets。BOS/EOSは新しく独立した段落タスクの境界であり、元page境界という意味ではない。JaQuAD抜粋や窓途中にはEOSを作らない。EOS/genre/BOSの分布変化を計測し、純粋なEOS単独因果としない。

短い原段落1,024件/123,767本文tokens/400components。新規原文取得0、PR101の111万独立原文部分集合の再利用。固定23標本と追加16標本を読み、既知の不自然/不正確/参照依存部分を隔離した。原典authorの完全な人間執筆認証や全事実確認は未実施。元source-specific CC BY-SA license、revision/URL/加工来歴を保存。データの個別本文は書き換えない。正式公開モデル用の全面承認ではない。

追加のparagraph DEVは旧DEVの3componentのみで、新しい独立TESTではない。主評価は旧24件の元全文BPE境界版。旧文字prefix24結果をPR101に保持し、再分割差4件を混同しない。相槌、空出力、長い反復や架空情報を自然な完全回答へ読み替えない。全語彙greedyと無修正raw bytes/token列を保存する。独立した日本語母語話者評価は未実施。

`python train.py --arm control` / `--arm boundary`。完了後receiptがあれば追加更新を拒否。実更新2→4を別プロセスで再開し、model/Adam/RNG/trace完全一致を確認。replayも実callへ加算。SIGTERM/SIGINTは次の更新境界でatomic保存し、`--resume`。保存後の完了済み更新は再計算/trace照合して別加算。intentだけの曖昧なcallは停止し、完了数を推測しない。最初のcheckpoint以前の事故はinitial/after2とledgerの明示的照合が必要。

条件付きのclip5はPLANで事前固定。boundary条件が全文改善に失敗し、95%以上clipping・中央値norm>1.5の場合だけ、同一初期状態/同じboundary scheduleのclip閾値だけを5にする診断。CLIP5_GO.jsonを実際のreceipt SHAに結び付けて保存してから実行する。LR/BPE/context/モデルを同時変更しない。

`archive.py <arm>` は新checkpointを32MiB以下へlossless分割、全SHAとfull trajectory/trace再読一致後にrawコピーだけ除く。元Git履歴/正式R25/比較R46は変更しない。保存容量は未採用の旧R43–45のGitとbyte一致したworking copyだけをsparse省略して確保し、STORAGE.jsonに全照合・復元方法を保存。

推論/学習は従来の独自モデル/Tokenizerで、外部学習済み重み/Tokenizer/回答生成API/有料GPU/APIを使用しない。サブエージェントなし。公開モデル/サイト変更、マージ、封印TEST利用なし。
