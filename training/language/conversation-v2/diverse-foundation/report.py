"""Final factual report from completed receipts, fixed evaluations and explicit manual readings."""
from common import *
import statistics,shutil

def main():
 plan=read(D/'PLAN.json');audit=read(D/'CORPUS_AUDIT.json');status=read(D/'RESUME_STATUS.json');final_models=[];arms={}
 for arm in ['A','B']:
  files=sorted((D/'run'/arm).glob('receipt-*.json'));r=max((read(p)for p in files),key=lambda r:r['retained_updates']);arms[arm]=r
  if r['retained_updates']==plan['full_pass_updates']:final_models.append(f"{arm}-{r['retained_updates']}")
 assert 'A-6459'in final_models
 lines=['# 多様な日本語原文による旧重み・fresh事前学習：最終結果','',
 'GOAL.mdの自然な日本語と内容のある未知入力応答を目的とした隔離研究。サブエージェント、外部学習済み資産、生成API、有料GPU/API、封印TEST、公開置換、マージは使用していない。正式な独立母語話者評価は未実施。',
 '', '## 取得・採用した原文','',
 f"独立本文 **{audit['body_tokens']:,} tokens**、TRAIN {audit['train_units']:,}単位、{audit['components']:,}component。10M独立tokensは未達。原文中に自然に重なる表現と、同じtarget位置の反復を区別する。現在の一回読みの重複target位置は0。",
 '', '|原典|本文tokens|割合|今回の位置づけ|','|---|---:|---:|---|']
 for s,n in audit['source_body_tokens'].items():lines.append(f"|{s}|{n:,}|{n/audit['body_tokens']:.2%}|"+('新規ネット取得'if s=='jma'else'既存原典の再利用')+'|')
 lines+=['', 'PR103再利用2,045,786と既存RealPersona再利用2,456,893、新規JMA15,496を混同しない。百科JaQuAD比率は約82%から37.21%へ低下したが、新しく大量の現代説明文を取得できたという意味ではない。RealPersonaは180,006発話、165,282異なる発話文字列、143の公開匿名話者ID。独立発話文字列に相当する本文2,409,876tokensと、全原文位置の2,456,893tokensは別。内容密度を文字数や質問符だけで認定しない。過去の固定20会話読解と応答審査を再利用した。',
 '', 'JMRDは既存と同一SHAの公式TRAINを再取得して話者を復元したが、259映画familyの第三者コピー等の疑いと最後のfamilyの品質保留により今回のTRAIN0。raw/未審査中間はローカル隔離。KokoroChatのNC/ND、ETCのNCと公開・split条件は保留。MRMPCの3話者を2者へ変換せず、JMultiWOZの旧DEV接続隔離とOASSTの条件付き審査を変更しない。出典・ライセンス・例外・帰属・削除対応の限界はRIGHTS.mdを参照。',
 '', '別のMAFF pilotは54回答ページ/10,471候補本文tokens、proxy通過50/9,515。固定8全文読解の6件は有用候補、2件は事実確認保留。現在のTRAIN追加0。青空文庫は規約とmetadataのみで作品本文0。これらを採用済み量へ加算しない。',
 '', '## 入力・終了・Tokenizer','',
 f"独自BPE3997/context256。full corpus UTF8復元、発話順序、teacher shift、PAD mask、未来遮断、原文位置の一回読みを検証。全teacher {audit['full_pass_targets']:,}、EOS {audit['EOS_teachers']:,}、role {audit['role_teachers']:,}、BOS/PAD教師0。EOSの多くは人間発話終端で、全てが文書終端ではない。原文・原典上の完結paragraph/FAQ sectionと任意のwindow切断を区別し、JaQuAD抜粋と任意256境界へEOSを足していない。",
 '', '人間A/B role3/4はassistantという意味や個人執筆者IDではない。RealPersonaの個人体験をAIの事実応答へ変更していない。JMAは元の質問と全回答段落を順序通り保持したsection task。byte fallbackの途中でcontextを切る窓は開始23/末尾19であり、原文全体の復元失敗ではない。corpus全体のunknown glyph、長さ、context収容率はTOKEN_CONTEXT_AUDIT/TARGET_DISTRIBUTIONに保存。原典source-family分離は全著者・全topicの独立性証明ではない。',
 '', '## 比較条件と実績','',
 'A：旧medium3470重み＋新規Adam。B：同じ11,225,280パラメータの独自構造をseed41029から初期化＋新規Adam。PR103 B/Cの考え方でmodel初期状態を比較し、両者のoptimizer初期状態を揃えた。Aの過去の約2.82Mtargetsの会話学習は消えていない。同じ追加targetsは同じ累積学習量ではない。',
 '', '共通AdamW(.9,.999,eps1e-8,WD.05)、FP32、clip1、4slot、全causal CE、同じTorch/private RNGと固定sampler41030、LR128warmup→2e-4→cosine3e-5を維持。model初期化のRNG消費後に共通training RNGへ戻す。データ/Tokenizer/構造/loss/デコードはarm間で共通。PR103との横断差を純粋なデータ効果とは呼ばない。',
 '', '|条件|保持更新|追加targets|実optimizer呼出し|再開検証呼出し|driver秒|最大RSS KiB|','|---|---:|---:|---:|---:|---:|---:|']
 for arm,r in arms.items():lines.append(f"|{arm}|{r['retained_updates']:,}|{r['retained_targets']:,}|{r['actual_optimizer_calls']:,}|{r['resume_validation_calls']}|{r['elapsed_seconds']:.1f}|{r['maximum_RSS_KiB']:,}|")
 h=read(D/'health/receipt.json');lines+=['',f"補助の識別prefix3原文暗記診断は{h['actual_optimizer_calls']}更新/{h['retained_targets']:,}targets、独立335本文tokensを64回。3件すべて末尾EOSまで完全再現したが、一般化ではない。本学習の重みへ混ぜない。全実績はRESUME_STATUS/VERIFYと各ledger/receiptが正本。再開検証・recovery replay・保持更新・healthを区別し、計画値を完了値にしない。",
 '', '共通1983更新/1,500,394targets時点の固定選択はA（最小補完を含む厳格成功A2/B1）。両者の段落展開は0で、言語能力の優位を示したわけではない。Aを初期登録のone-pass終端まで進め、A失敗時に限るBの未処理残り完了を、A終端結果を見る前にFRESH_COMPLETION_PROTOCOLへ追加登録した。これは元選択の書換えでも新epochでもなく、freshを1.5Mだけで否定しないための別の探索診断。選択DEVの露出・追加診断の条件付き選択偏りは残る。',
 '', '## 固定greedy生成とNLL','',
 '|モデル/更新|旧原文NLL|新9 NLL|JMA NLL|旧24 EOS/反復|新9 EOS/反復|JMA12 EOS/反復|','|---|---:|---:|---:|---|---|---|']
 for p in sorted((D/'evaluation').glob('*-summary.json')):
  r=read(p);q=r['NLL'];z=r['panels'];lines.append(f"|{r['model']}|{q['old_prose']['nll']:.6f}|{q['old_new_family']['nll']:.6f}|{q['JMA']['nll']:.6f}|{z['old24']['EOS']}/{z['old24']['repeat4']}|{z['oldNew9']['EOS']}/{z['oldNew9']['repeat4']}|{z['newJMA']['EOS']}/{z['newJMA']['repeat4']}|")
 lines+=['', 'EOS/反復の各セルは二つの件数を並べたもので、成功率ではない。機械的4gram反復proxyと有害な反復の全文判定を区別する。生成全文はJSON/GENERATIONS.mdに省略・修正なく保存し、token列/raw bytes/入力/停止理由/モデル対応を保持。無効UTF8はnullで、置換や修復を行わない。',
 '', '意味判定の正本はBASELINE_READING、A/B_COMPARISON_READING、MIDPOINT_REVIEW、TERMINAL_REVIEW、B_MIDPOINT_REVIEW/B_TERMINAL_REVIEW。短い文末補完と、新たな内容を展開する段落と、具体的な対話応答は異なる。全語彙greedyが主評価。sampling8件は固定seed/T1/top_p1の分布診断であり、偶然の自然文を主成績へ加えない。日常文8件はassistant作成の補助DEVで、人間原文・独立TESTではない。',
 '', '## 原因の実証範囲','']
 for name in final_models:
  p=D/'probabilities'/f'{name}-summary.json'
  if p.exists():
   r=read(p);lines.append(f"- {name}：最初8tokenの対応する{r['paired_actual_first8_positions']}位置で、gold NLLは正解履歴{r['old24_first8_gold_NLL_correct']:.4f}、自己履歴{r['old24_first8_gold_NLL_self']:.4f}。同履歴の再計算argmax差{r['rescoring_argmax_disagreements']}。反復4gram完成位置の中央値は0始まり{r['median_repeat_completion_position0']}。goldからの分岐自体は意味破綻位置ではなく、goldは唯一の正しい続きを意味しない。早期EOSにより対応位置数が変わる。")
  p=D/'context'/f'{name}.json'
  if p.exists():
   r=read(p)['summary'];lines.append(f"- {name}：同じ長さの正/無関係履歴で同じ567gold位置を比較。正−誤NLL平均{r['mean_correct_minus_unrelated_NLL']:.5f}、正が良い{r['correct_better_than_unrelated_cases']}/9。限定的な履歴利用の証拠で、適切な内容応答の証明ではない。文脈除去は絶対位置/長さの交絡があり、CJK proxyは真の内容語タグではない。")
 lines+=['', '教師履歴でも本文予測は十分でなく、自己生成履歴でさらに悪化する可能性を同時に扱う。TRAIN/DEV、本文/role/EOSを分けたfit/とprobabilities/を参照。roleやEOSを予測できても本文意味が成立するとは限らない。EOS教師増加、clip解除だけで全崩壊を説明できなかったPR102の知見を継承し、今回は閾値を調整して成功扱いしていない。',
 '', 'causal/shift/PAD/dropout、Adam非共有、更新後2→4完全再開、異なる3prefixの暗記、限定JS一致は実装の重大な不整合を支持しないが、全ての潜在不具合を否定する検査ではない。全体のone-passは約0.43targets/parameterで、少量学習の失敗だけで11Mの容量不足とは断定しない。学習量・分布・最適化・表現容量・自己履歴誤差の切り分けは未完。context到達前にも崩れるため、長さ256だけを原因としない。',
 '', '## 内容応答・複数ターン・独立評価','',
 '内容24/資料23/限定36/反転context12/自己履歴4episodeの無修正出力はpanels/。実際の判定はCAPABILITY_REVIEW.json。必要情報のない相槌、無関係な問い返し、事実誤り、ループは成功にしない。3turnに必要なEOSが出なければそこで中断し、EOSや正解履歴を捏造しない。実際の生成turn数とepisode完了を分ける。これらも既に露出した診断で、独立母語話者評価や封印TESTではない。',
 '', '## 保存・検証・失敗','',
 '全状態model/Adam/Torch+private RNG/固定samplerのcursor/trace/PLAN SHAを32MiB以下のlossless chunksに保存。選択点とmidpoint/terminalを区別。rolling128世代を全て永久保存したという意味ではない。archive full SHA/再読tensor digest、Git原本だけからの復元、atomic/stale pending、両armの実更新2→4再開一致を確認。原典→corpus→scheduleもbyte一致再構築した。',
 '', 'FAILED/FAILURESの全記録を保持。評価キー重複や補助module名衝突はoptimizer更新前/ゼロ更新処理の失敗で、学習重みの無効化や隠れた更新を意味しない。source parser footerとcached取得時刻処理を修正し、固定コーパスは変えていない。資源probeの無限clip引数は共有helperの安全guardで拒否され、非更新norm計算へ修正した。本学習clip1は変更していない。',
 '', '公開監査では品質保留JMRD中間本文を除外し、ID/SHA/理由のみ残した。初回pushと取消が競合した後、作成直後の研究tipをexpected-head leaseで置換し、元commitはlocal-audit refへ保存。以前のPR103まで/R25/R46の履歴は変更しない。旧リモートobjectの完全消去は保証しない。最終TRAINにその本文は一度も入っていない。',
 '', '実空きは当該cloudの/workspace overlayでありPC/GitHub容量ではない。lower-layerの古い作業コピー省略は物理空きを増やさなかった。新規checkpoint作業コピーはGit blob/SHA一致後に省略し、Git原本・履歴を保持。巨大な自動repackを避けるlocal gc設定のみ変更。無料CPU2/RAM8GiB/GPU0で実行した。',
 '', '## 次期資源と研究判断','',
 'RESOURCE_PROBESの27.40M/50.65M・context512/1024は乱数モデルの0更新forward/backward資源確認だけで、性能改善の証拠ではない。単一cold batchと他worker競合があるため、その非単調wall速度を本学習時間や容量優位の比較へ使わない。Adam momentsは未割当で、追加8bytes/parameterを見込む。50.65MのFP32全状態は約608MB/世代、Gitを含む複数世代には現空きで余裕がない。GPU速度は未測定。',
 '', '現在の11M実測driver速度から10M/30M/100MtargetsのCPU時間を見積もる際は、検証・保存・replay・他worker負荷を別に足す。データ量/モデル規模/更新数を能力そのものとしない。追加10–20GiB以上の作業余裕と、合法で広い現代説明文・人間会話の独立10M→30M→100Mを段階目標とする。量のため権利・品質を緩めない。',
 '', 'NEXT_STRATEGY.mdに一条件の次期比較と5段階の判断基準を記す。新しい広い原文が不足する間、同じ少数文章を何十周もして独立量を水増ししない。形式/Tokenizer/容量/データを同一比較で一括変更しない。現段階の正式採用・公開置換は**No-Go**。R25、R46、旧17/13/9/Pareto/反復条件を維持し、未実施の正式試験を合格扱いしない。']
 (D/'REPORT.md').write_text('\n'.join(lines)+'\n');write(D/'SUMMARY.json',dict(corpus=audit,arms=arms,actual_work=status,final_models=final_models,formal_adoption='No-Go',public_replacement=False,not_10M_independent_tokens=True));print('Report generated; manual capability review and current CI must be checked',flush=True)
if __name__=='__main__':main()
