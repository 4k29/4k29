"""Write this completed R45 report from actual bound assessments, not future grades."""
import pathlib,json,re
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';P=R.parent/'round44';read=lambda p:json.loads(p.read_text());a=read(E/'final-assessment.json');old=read(P/'execution/final-assessment.json');num=read(E/'final-numerical-verification.json');audit=read(E/'optimizer-audit.json');coverage=read(E/'sampling-coverage-10000.json');gap=read(E/'human-train-gap/complete.json')
assert a['actualCompletedUpdates']==10000 and not a['adopted'] and not a['fullOutputReviewPending'];assert read(E/'mechanical-status.json')['pipelineExitCode']==0
assert 'pass 962' in (E/'repository-tests.log').read_text();pub=json.loads((E/'public-evaluation.log').read_text().splitlines()[-1]);assert pub['passed']==pub['replies']==2580
rows=[]
for state in ['selected','terminal']:
 for label,key,n in [('従来','original17',17),('日常','daily12',12),('実会話','native8',8),('別資料','mrmp5',5)]:
  if key=='original17':
   x=a[state+'Original'];y=old[state+'Original'];w=(y['fullOutputMeaningful'],x['fullOutputMeaningful']);l=(17-y['fullOutputNonLoop'],17-x['fullOutputNonLoop'])
  else:x=a[state+'Supplemental'][key];y=old[state+'Supplemental'][key];w=(y['wholeMeaning'],x['wholeMeaning']);l=(y['longLoopsPrimary'],x['longLoopsPrimary'])
  rows.append(f'| {state} {label}{n} | {w[0]}/{n} → {w[1]}/{n} | {l[0]} → {l[1]} |')
text='''# R45 RESULTS — correct-context CE係数0.1→0.2だけの比較

実10000 optimizer更新を完了した。会話DEV NLLは微改善したが、選択重みの日常全文0/12、従来0/17のまま。日常の長い反復はselected/terminalとも増え、terminalの日常全文は旧2/12→新1/12へ低下。従来17/13/9 scopes・両ジャンルの厳格ゲート、固定実用床、paired実用条件、Pareto条件を満たさず不採用。公開モデル/サイト/R25採用anchorは維持する。

## 同じ入力と生成条件での比較

旧R44/新R45ともselected9500/Adam29500、terminal10000/Adam30000。同じ共通DEV0/毎500の最小selector、own全語彙greedy192、Python1thread、無修正生成を維持。42 exposed DEV入力の4状態168全文を[全文集](execution/ALL_FOUR_STATE_GENERATIONS.md)に保存し、全token IDsも各JSONに保持した。新84全文を実際に読み、83種類のprefix+全文を照合。独立84/168問題、新TEST、blind人手評価ではない。

| 状態と群 | 全文意味成立 旧→新 | 長い反復 旧→新 |
| --- | --- | --- |
'''+ '\n'.join(rows)+f'''

従来17の初文/非loop/全文意味はselected旧4/5/0→新5/5/0、terminal旧5/4/1→新5/6/0。日常EOSはselected10→8、terminal9→8。短いEOS、初文成立、非loopだけで能力改善と判定しない。

共通DEV selected {a['controlCommonDevNll']:.12f}→{a['commonDevNll']:.12f}、terminal {a['controlTerminalCommonDevNll']:.12f}→{a['terminalCommonDevNll']:.12f}と悪化。会話DEV99 selected {a['controlHumanDevNll']:.12f}→{a['humanDevNll']:.12f}、terminal {a['controlTerminalHumanDevNll']:.12f}→{a['terminalHumanDevNll']:.12f}と微改善したが、固定上限0.9107185711429243には未達。共通DEVはaozora/bunka/env/jma/mdn/mic/statの7siteで人間会話を含まない。会話DEVへselectorを途中変更していない。

## 全文で見えた失敗と境界例

1kでは公園への「行きたいですね。公園とか行きたいですね。」が有限二文の共感として主意味1/12（旧0）だったが、厳しい雨への代案/反復解釈では0。この境界的な早期例はselected9500では「行ってみたいなので行かないですか？」となり再現しなかった。1k会話NLL0.93881607→0.93861722、5k0.92542710→0.92522157と小さな差で、途中結果による学習条件変更はしていない。5kの自由生成は事前計画どおり追加しなかった。

selectedでは「気に入れてます」「友人がいつもり」「天気の毒」等の短い活用/語形/主述崩れが残る。terminalも寝る/雨/引用語のメタ説明/味覚を長く循環する。selected実会話のサジーへの単発「おいしいですね」は個人の味の感想として主whole1としたが、飲み方の相談への関連を厳しく取れば0で、新native3/8は2/8へ戻る。新情報や具体的助言は最小の会話行為の必須条件にしない一方、全文の重い反復や接続崩れを後半の自然な一節だけで合格にはしない。

terminalの日常は公園への二文の希望1件が成立。厳しく反復/雨への代案を求めれば0。terminal従来のデータ収集分析を支えるデータ収集分析という一文は、対象の二層の区別がない自己参照として主whole0、メタ分析の省略と読む別解なら1/17。有限で異なる火山説明/三つのSVG命題はprimary非loopだが侵入反復があり、広くloopと取る感度を保存。CMP16の十回連打や長い雨/配列の文循環はloopとして区別した。深い子供の名詞修飾が一つの短い有限文に収まる場合は旧例同様primary非loopであり、意味成立は別に評価した。

同一全文は旧判定を維持し、旧selected42はR44凍結manifestと再生成raw core一致で履歴へrebind。旧terminal42は検証済み履歴。新84の同一全文、R39〜R45の同一初文6項目（151一致）、今回1kの同一全文主判定も照合した。未知名/架空設定/外部事実の真偽/cap/新情報欠如だけでは失格にせず、文章の事後修正もしていない。

## 一条件・実更新・保存

唯一の学習変更はpolicy.contextPreference.coefficientの0.1→0.2。R44と全10 core learning files、35データfiles、RP40%/JMRD5%/非会話55%の相対比、own BPE5455語彙/40-30-30、pool1024/403documents、teacherUL1/selfUL0.1/EOSaux0.3、every10/batch2/cyclic/eval/fork_rng、8層192dim/4heads/FFN768/context256/4655808params、batch8/CPU2FP32 deterministic、LR2.2499999999999998e-5/seed2049、10000dose、selector/生成/全gateを固定。wrong-contextは診断のみ。R44terminalの延長ではなく、同じR28 latest full model/Adam20000/Python・Torch RNGからの兄弟比較である。

実更新0のcommit5b82cd7d81ddf83b7ab0088bd7c9508edc49bd42で426入力を凍結。全行boundary/mask、90strata各row/周辺確率、1024組source/token/concat/donor、43契約、初期DEV0.9718989571266189・model/Adam/RNG一致、finite勾配、35静的実行ファイル/93 Python/7 shellの構文を監査。係数は勾配を見る前に0.2へ固定し探索せず、初期標本勾配比0.5046487はaux2組/CE3行の比較で全複合lossや学習後の最適性ではない。

計算時間{audit['elapsedTrainingSeconds']:.3f}秒、実10000/Adam30000。初期0・実200/1000/5000・selected9500/Adam29500・terminal10000/Adam30000の6 fullstates、optimizer/RNG、lossless parts、selected-weights.pt/model.js、全data/code SHAと実counterを保存した。[再現手順](REPRODUCTION.md)を参照。selectedは比較用の選択重みで、公開採用重みではない。

主draws80000、target15720338、bytes54747251、最終Python/Torch RNGはR44と完全一致。aux1000calls/2000pairs、46537正解target/93074両文脈score/266752両入力tokens、1024distinct（各1〜2回）。self-negativeは1000rollouts/31751生成tokens/11498negative位置で旧と異なる。追加のthrowaway optimizer更新や訓練再実行は0。全logged lossはfiniteで係数の式と実traceに一致した。

総training lossは旧0.1/新0.2の目的関数が異なるため直接の改善指標ではない。raw総lossを改変せず、CE/未係数aux/validationを分け、loss-comparison-scope.jsonで範囲を明示。CSVは100更新ごとの1 minibatch、10更新ごとのaux2組、0/毎500の全共通DEVであり、全TRAIN平均ではない。

## TRAIN診断と使用量

selected TRAIN64文脈利得0.11944759→0.12252911、正利得50→51。pool内7件のNLL3.29613563→3.24795754/利得0.20107194→0.21497222、他57件3.37704740→3.37128502/利得0.10942355→0.11117645。両方TRAINで未見ではない。pool1024全体はNLL3.25124479→3.19639088/利得0.19603087→0.21392614と改善し、poolへの効果が相対的に大きい。7件はpool先頭0〜6で1k時点に各1回、終点に各2回aux学習済み。gold発話のteacher-forcing確率や文脈利得が、自由生成の文法/意味へ十分移らなかった。

TRAIN99標本NLL0.88794772→0.88782031、DEVとの差0.02974767→0.02976290。内容/長さ/話題はDEVとmatchedでなく、全TRAIN平均でもない。DEV99は重複1組を含む。

事後の読み取り専用sampler replayで、5kの40000抽選は33191/189166行、10kの80000抽選は57089/189166行（30.1793%）、13215/15764documentsを抽選した。終点RNGはcheckpointと一致。view/windowの同じ原文との重複や親モデルの学習歴があるため、残りを未学習/未見と呼ばず、追加doseが意味を改善する証明にもしない。新しい条件やcheckpoint選択にこの集計を使用していない。

pool原典の過去16例の読解履歴はSHAで再利用し、新たな意味監査とはしない。全1024 source/token監査と1024全文意味監査を区別する。既知DEV/単一seed/greedy/非blind評価という限界を保ち、R39の過去policy表示exposure incidentも履歴に残す。reserved TESTへモデル/tokenizerを適用しない。legacy sequence-saturationのoldはR25anchor9500で、今回対照R44selected9500と同じstep番号でも別モデル。legacy gapはR11canonical/R12cached標本で今回全TRAINではない。

## 数値・実行・容量

新84全文はPy/JS・raw FP32/7decimal exportとも84一致。最大reference logit差Py/JS {num['maxMeasuredNewPythonJavascriptReferenceLogitError']:.12g}、raw/export {num['maxMeasuredNewRawExportReferenceLogitError']:.12g}、固定2e-4未満。referenceは標本で全step/全hardware保証ではない。旧selectedの今回JS42/raw25、旧original17raw未再実行、旧terminalは履歴。R10既知near-tie16/17とSHA117e5f69480f8856262090b46825efb9a2333732791c88e9a8b7484a8e406769を隠さない。数値失敗時も成果保存のSHA検証を行えるよう整理したが、数値の採用条件84/84+既存toleranceは維持し、今回は実測PASS。

43 Python契約、Node962/962、既存public43問2580応答2580/2580とJS構文検証を実施。public成功は実験モデルの言語合格ではない。23:05頃の環境再接続でもdetached trainerは継続し、9400/Adam29400を照合した。再起動/再学習はしていない。初期snapshot作成前のread-only照合はFileNotFoundとなったが、作成待ちauditで回復し初期R28一致と係数0.2を確認。pipelineはexit0で予定機械評価を完了した。

容量確保では、全part/結合/raw SHAとGit追跡を検証したR43旧raw6状態の重複作業コピーのみを除去し448075684bytesを確保。一意な状態はGitのlossless partsへ保持した。さらに同一Git blob/SHAの旧不変データ46作業コピーをhardlink共有し約828MBの重複を減らした。R44/R45のパスは置換せず、全パス/内容/履歴を保持し426入力SHAも再検証。今後共有データを変更するなら先に独立コピーを作る。以前の93旧prepared filesのlocal sparse除外も履歴削除ではない。WORKSPACE_STORAGE.mdと各証拠JSONを参照。

## 原因と次の一条件

1. 容量: 約466万paramsの制約は候補だが容量固定なので因果未分離。直ちに大規模化しない。
2. データ: 同じ資料でpool正解確率の改善は大きく、別TRAIN/DEVや生成への移行は小さい。量/質/ジャンルと更新量を混同しない。
3. 分割: boundary/maskと全bytesは一致しても語形が崩れる。固定BPEの因果は未分離でvocab変更を混ぜない。
4. LR/optimizer: finite状態/全moment/実counter/初期一致に破綻の根拠はない。R16〜R45のpolicy.learningRateは同じ2.25e-5で、現在のRP40%・R28初期stateでのLR比較は未検証。次の一条件としてLR感度を分離する理由がある。
5. context: 短いEOS発話でも活用/対象が崩れるため256上限だけでは説明できない。
6. 不足学習/過学習: 使用量と標本gapは示したが、未抽選行=未学習ではなく全TRAIN過学習とも断定しない。終点で反復が増えたため盲目的な追加doseを選ばない。
7. 推論: 同じDecoderと84全文数値一致から、今回の崩れをPy/JS分岐で説明する根拠はない。R10既知問題は別に残す。
8. 評価: 会話を含まない共通selector、既知DEV、小標本、非blind、省略解釈が制約。NLL/文脈利得も全文意味とは別で、単一の短い相槌増加を能力の証明にしない。

次案はR44を科学対照とするLRだけ2倍（2.2499999999999998e-5→4.4999999999999996e-5）。R45の不採用係数0.2を持ち越さず、定義した対照R44と同じ係数0.1を維持する。初期R28の重み・Adam tensors/step・RNGは同じ、param-group LRだけ宣言どおり変更。RP40%/JMRD5%・資料/pool/own BPE・全他loss・8x192/context・seed/10000dose/selector/生成/gateを固定。R45から見た二条件の混合試験ではなく、R44に対する一条件比較である。R44/R45terminalの延長、新資料/role tags/容量/dose変更を混ぜず、公開/R25anchorを維持する。
'''
(R/'RESULTS.md').write_text(text)
(R/'README.md').write_text('''# R45 — 文脈CE係数0.1→0.2だけの比較

実10000更新完了。会話DEV NLLは微改善したが、selected日常全文0/12・従来0/17、terminal日常1/12・従来0/17。日常反復は旧より増え、厳格gate/固定実用条件/Paretoは未達で不採用。公開モデル/サイト/R25anchorは維持。

[結果・原因分析](RESULTS.md) / [旧新4状態168全文](execution/ALL_FOUR_STATE_GENERATIONS.md) / [再現](REPRODUCTION.md) / [次の一条件](NEXT_EXPERIMENT.md)。新84全文（83種類）を実際に読み、同一全文/初文と1k判定も照合。Py/JSとraw/exportは84全文一致、R10既知16/17は別記した。

0/200/1000/5000/selected9500/terminal10000のfull model/Adam/RNG・lossless parts・全SHA・loss CSVを保存。426入力は開始前commit5b82cd7で固定。初期read-only照合の作成待ちと接続側monitor再構築はあったが、trainer再起動/追加optimizer更新は0。

次は不採用係数を持ち越さずR44を科学対照に、LRだけ2倍の別ラウンドを提案。R45中は未訓練・実更新0。共有された不変データを将来編集する際は、先に独立コピーを作る。
''')
(R/'NEXT_EXPERIMENT.md').write_text('''# R45終了時の次案 — この案の実更新0

R44を科学対照に学習率だけ2倍、2.2499999999999998e-5→4.4999999999999996e-5へ事前固定する。R45の係数0.2は日常反復を悪化させ、NLL/文脈利得の小改善が全文へ移らなかったため不採用とし、対照R44の係数0.1を維持する。R16〜R45で同じLRが続いており、RP40%条件下でのLR最適性は未検証。容量や単純な追加doseより先に一条件の感度を測る。

同じR28 full model/Adam20000 tensors・step/Python・Torch RNGから開始。optimizer param-group LRだけ変更し、他moments/groupsを混ぜない。初期forward/全DEVは変わらないことを確認し、実0 checkpointのLR例外も明示する。R44/R45terminalを延長しない。

資料35files/own5455 BPE40-30-30/主RP40%+JMRD5%/pool1024/CE係数0.1/他全loss/8層192dim/context256/seed/実10000dose/selector/greedy生成/厳格gateを固定。R45を直接対照にcoefとLRの二条件を変える試験ではなく、R44に対してLRだけ異なる兄弟比較。R45は既存失敗参照として保存する。新資料/role表現/容量/追加doseを同時導入しない。

LRは勾配/結果を見て探索しない。finite状態とclip/実counter・RNG/target exposureを検証し、旧新selected/terminal全168全文・新84実読解・humanDEV99・TRAIN64の7/57・pool1024・PyJS/rawを比較。悪化/数値分岐も隠さず、NLLだけで採用せず、公開モデル/R25anchorは維持する。
''')
(R/'REPRODUCTION.md').write_text('''# R45の復元と実施範囲

実10000更新は完了済み。開始前commit5b82cd7d81ddf83b7ab0088bd7c9508edc49bd42で426入力を実更新0に凍結。policy.json/source-manifest.jsonに条件と全data/code SHA、execution/launch.jsonにUTC/command、run.shに固定CLIを保存。R44最終CI証拠もcontrol-final-ci.jsonに固定した。

保存成果の照合はrepo rootから次を実行する。

```bash
python training/language/round45/execution/verify_final_artifacts.py --require-tracked
```

raw checkpointやtrain.tokens.binがない場合は隣接*.chunks.jsonと各part/結合SHAを確認してlossless復元する。初期0/Adam20000、実200/20200、1000/21000、5000/25000、selected9500/29500、latest10000/30000の6 fullstatesを保存。selected-weights.pt/model.jsは比較用で今回不採用。R25anchor/publicへ置換していない。再開時にselected重みとlatest optimizerを混ぜない。

既存完了runを再訓練しない。再現学習が必要なら別clone/出力で成果を保護し、426入力SHAと初期R28 latest full model/Adam20000/RNG、全初期DEV一致を確認して固定CLIを使う。部分runのみ同一条件resumeとし、予定値でなくstep/Adam/traceで照合。R45は環境再接続でもtrainerが継続し、訓練再実行・余分なoptimizer更新0だった。

全10 core filesはR44とbytes同一、学習差はcontextPreference.coefficient0.1→0.2のみ。静的実行ファイル/mjsを含む事前検証、43契約、全行境界/mask、初期勾配/DEV/fullstateはexecutionの各preflightとログに保存。初期checkpoint作成前のread-only FileNotFoundはpostlaunch_initial_audit.pyの作成待ちで解決し学習に影響しなかった。

原典cacheは/workspace/daily-conversation-source-audit/human-only-raw。資料/取得commit/利用条件/speaker train-dev-test splitはR44と同じ固定資料。新しい原典の意味読解はしておらず、同一SHAの過去履歴の再利用と全source/token検証を区別。reserved TESTへモデル/tokenizerを適用せず、外部重み/tokenizer/生成API/教師生成正例/回答修正を使用しない。

reading-notes-as-executed.jsonとrecord_final_readings_as_executed.pyは実際に読んだ今回の生成SHA専用binderで、未来の出力の自動意味graderではない。同一全文/初文・今回1kの主判定も照合する。再計算は別出力へ保存し既存の生成/読解を不用意に上書きしない。全168無修正全文はALL_FOUR_STATE_GENERATIONS.md、token IDsは各generation JSON。数値範囲はfinal-numerical-verification.json、既知R10near-tie16/17を保持。

loss CSVはinstantaneous-training-loss-curve.csv/context-auxiliary-curve.csv/paired-ce-curve.csv。係数が異なる総training lossを旧新で直接比較しない。前二者はminibatch/aux2組の標本で全TRAIN平均ではない。TRAIN99/DEV99は非matched、TRAIN64の7/57も両方TRAIN。sampling-coverage-5000/10000.jsonはposthocの抽選使用量で、未抽選行=未見文でも追加dose有効の証明でもない。

容量確保のR43旧raw6状態はtracked lossless partsから完全復元可能。旧不変データ46コピーのhardlink共有では内容/全パス/履歴と426SHAを保持しR44/R45パスは置換しなかった。共有データを編集する際は先に独立copy/atomic replaceを行う。sparse旧prepared93filesの扱いと詳細はWORKSPACE_STORAGE.mdと各storage JSON。Git履歴や一意な状態は削除していない。
''')
print('Wrote final R45 outcome, limitations, reproduction and one LR-only proposal; no new training performed.')
