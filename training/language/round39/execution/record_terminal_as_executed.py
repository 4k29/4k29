"""SHA-bound explicit judgments after actual complete reading of all42 terminal outputs."""
import pathlib,json,hashlib,subprocess
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';D=E/'terminal-state-diagnostic';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=[
'初文したは自然。以後おじいちゃんの呼称・所有句を長く反復し、何をしているかの対象・主述も崩れて切断。',
'寒さを防ぐために出て来たは従来同一初文と同じ8点。後続の夜の所有句と夜夜の文字へ長くloopし切断。',
'風のなかにかきらがあって行くとから主述・係りが不明のままぼんやり・ぼんぼ等の音列へ長くloopする。初文も閉じない。未知語だけを失敗理由にしない。',
'未完引用内のInter等を長く反復し、初文も全体も閉じない。',
'初文るは自然。内訳の情報端末の主要2億円というカテゴリーの係りと、同じ音声系ソフトの異なる数量の関係が不明。数値や未知名の事実未確認だけで失敗にはしない。有限の内訳EOSで非loop、重複カテゴリーは侵入反復。',
'法律に基づく活動促進と温暖化対策を図る初文は意味を追え、法律根拠の冗長な反復をrepetition1として既存合計9点で初文合格。後続は日中韓国・国会・削減目標・計画が不明な係りで列挙され途中で切れる。変化する法番号・日付・会合の有限列挙でprimary非長期loopだが、基づきと日中韓国の侵入反復を広くloopとする感度は別記。事実を認定しない。',
'目標及び改正施行規則から海域の所有句を初文中で何度も重ね、海域を推進という述語対象も崩れる。以後及び海域・約30年等の長いloop。',
'速報が共同検討を実施するという主体・行為の関係と対象地域の重複が不自然。以後予報・レベル・範囲・対応を変化させる有限の警報説明でprimary非長期loop、付して発表の重複は侵入反復。広いloop代替を別記。',
'解析雨量自体が発表状況を把握するという主体・道具の関係が不自然。解説を案内する後文は自然でもprimary全文不成立。道具省略を許す弱い代替のみ別記。短いEOS非loop。',
'初文からSVGプロパティをを重複。後続はプロパティの値と同じ値の自己参照を長くloopして切断。',
'グローバル属性を設定できる初文は自然。以後要素に設定する要素を指定するという自己参照を長くloop。',
'他オブジェクトのメソッドを返す初文は同一文と同じ10点。未知名だけで失敗にはしない。後続は文字列・配列の配列を返すを長く繰り返して切断。',
'ポリシーを使用してSVGリクエストを提供する初文は言語として自然でAPI事実は認定しない。後続のSVGリクエストを送信するために送信するリクエストを送信するという入れ子を多数重ねる。71tokensEOSでもprimaryloopで全文不成立。',
'情報提供の方法を提供する方法を示すという初文は意味・目的が弱く8点。以後WebGLの所有句を192tokens反復して切断。',
'初文はselected同一のデータなどの客観的な取組でmeaning1・合計9点。厳しいカテゴリー解釈では初文不合格も別記。後続は管理の文字と語の長いloopになり全体は不成立。',
'文化大臣の表現のための会合という係り、閉じない括弧とアジア6回が初文を崩す。以後異なる日付・会合・協力を列挙し覚書を開催と崩れる。有限の変化する会合列挙としてprimary非長期loop、アジア・連携協力の侵入反復をloopとする広い感度も記録。未知会議名の存在だけを失敗理由にしない。',
'初文施策を講じられていますは従来同一文と同じ7点。後続は地方公共団体・地域計画の所有句と同じ項目を長くloopして切断。尊敬・可能の弱い初文代替は感度だけへ保存。']
scores=[[2,2,2,2,2,True],[2,1,1,2,2,True],[0,0,1,0,0,False],[0,0,1,0,0,False],[2,2,2,2,2,True],[2,2,2,1,2,True],[1,0,1,0,1,True],[1,1,1,1,1,True],[1,1,1,2,1,True],[1,1,2,1,1,True],[2,2,2,2,2,True],[2,2,2,2,2,True],[2,2,2,2,2,True],[2,1,2,1,2,True],[2,1,2,2,2,True],[1,0,1,0,0,True],[1,1,2,2,1,True]]
daily=[
'帰りに行くのがいないので、何をしてもらえないのでと主述・因果が崩れ、何をしてもらうのが好きかという不明な問いへ移る。有限39tokensの非長期loopだが句の侵入反復。',
'selectedと完全同一の何か食べたかったか。残り物の夕食への自然な継続にならずprimary0、未提示他者の希望確認という弱い代替は保存。短いEOS非loop。',
'友達との予定から日に会う・日曜日の所有句・曜日の文字へ長くloopして切断。',
'雨が降るのはず・降り降り等の主述と活用の崩れを192tokens反復し、準備を継げない。',
'寝るのが寝るのかなから寝ると寝る・寝るを192tokens反復。',
'行くのが・その後を長く重ね、おかあさん・おかみの所有句へ逸れて長くloopして切断。',
'時刻への返事が天気の毒・天気の人という不明な語結合になり意味がつながらない。有限41tokensでprimary非長期loop、天気の人の重複は侵入反復。',
'疲労の話に天井の友人は今日はと不明な主語・何を食べたいという疑問を返す。今日は3回の侵入反復はあるが有限23tokensのprimary非長期loop。',
'卵の調理の問いに時間にかかわいという不成立な活用から自炊の話へ移り、その後いけない・時間が多い・食べている等の無関係な問いへ崩れる。81tokensEOSの変化する有限の文列でprimary非長期loop、そうですね・今日はの侵入反復を広くloopにする感度は別記。',
'週末の出来事を答えずおいしそうという引用からそうかを20回以上・僕はの長いloopへ移り切断。',
'近況への応答が「おいしい！」と言うという不明な発話行為になり話題がつながらない。短いEOS非loop。',
'既定の雨天の公園予定をどうするかに公園の所有句を7回・11回等重ね、整備を促進するという行政文体へ移る。EOSでも明確な長いloop。']
native=[
'selectedと完全同一。歩行の健康の話への私もお好きですかは話者・好意の対象がつながらずprimary不成立。短いEOS非loop。',
'自然な相槌の後、バイクのレストアにおいしいですという不自然な対象の評価を足す。初めの相槌だけを切り出さず全文不成立。',
'挨拶の切替時刻の話に私も今日は何かお好きですかという対象・話者の不明な問いが返る。短いEOS非loop。',
'酸っぱい飲料の飲み方の話においしいですよね等の同じ相槌を192tokens反復し切断。',
'selectedと完全同一の今日は何かのことですか。暑さ・外出の話に何を尋ねるか不明。短いEOS非loop。',
'selectedと完全同一。女優が好きという直前発話に私も好きですと普通の対象省略で共有の好みを返す最小の意味成立。具体的対象名や新情報はない。',
'積み重ねとメモの話から私もお米がいいへ逸れ、私もおいしいですよね・今度はおいしいですよねを149tokens反復してEOS。意味も全体もloop。',
'selectedと完全同一。パスタの味へのおいしいですねという自然な同意。具体的対象名・新情報はない。']
source=[
'selectedと完全同一のおすすめですか。仕事の内容とポップコーンの香りの話から何を勧めるか不明でprimary不成立。未提示の食べ物の勧めと読む弱い代替のみ保存。短いEOS非loop。',
'お母さんの子供の所有句を長く重ね、子供子・子の文字と句を192tokens反復して切断。',
'R38terminalと同一prefix/全文のそうですね。あとは？で同じprimary不成立。土産店・ロープウェイの話に何を追加で聞くか曖昧。追加の場所を尋ねる省略を許す弱い代替は従来通り保存。短いEOS非loop。',
'スカイダイビングの希望にあなたは何かのことが多いですかという主題・数量の不明な問いを返す。短いEOS非loop。',
'selectedと同じ毎日を192tokens反復し、洗面所の話を継ぐ述語が成立しない。']
spec=[('original17','f48efe71d4ec0afcefd7cda2482fb1946248e39a97fde5f13bc0732d0a929a17',original,set(),{4,5,7,8,15},'original17-manual.json'),('daily12','fc13a4f489bca63c524c427495b441e02418c3c477fe866cc0c0b11cf0e2bca2',daily,set(),{0,1,6,7,8,10},'daily12-reading.json'),('native8','326660394641b032100d0953b79d000dfb391aa8290d22a43d1e71d279783fdc',native,{5,7},{0,1,2,4,5,7},'native8-reading.json'),('mrmp5','cc464b6ecc3a39fbcd5b648371e4e76b2f97cbfb55200cfd98a255ced27218ac',source,set(),{0,2,3},'mrmp5-reading.json')]
for group,expected,reasons,meaning,nonloop,manual in spec:
 p=D/f'{group}-python.json';assert sha(p)==expected;g=read(p);rows=[]
 for i,(x,reason)in enumerate(zip(g['rows'],reasons,strict=True)):
  j=dict(id=x['id'],fullOutputMeaningful=i in meaning,fullOutputLoop=i not in nonloop,intrusiveRepetition=i not in nonloop or(group=='original17'and i in {4,5,7,15})or(group=='daily12'and i in {0,6,7,8}),reason=reason,prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
  if group=='original17':j.update(dict(zip(['grammar','meaning','connection','repetition','breaks','sentenceClosed'],scores[i],strict=True)),firstSentenceScoreProvenance='Actual full terminal prefix and continuation read; same selected first sentences keep component scores')
  if group in ['native8','mrmp5']:j.update(contentBeyondBackchannel=group=='native8'and i in {5,7},explicitContextObjectReference=False,newInformation=False)
  rows.append(j)
 a=dict(generationSha256=sha(p),reviewer='Assistant actual complete reading of all terminal prefixes and continuations; not independent blind human',actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=10000,wholeMeaning=len(meaning),longLoopsPrimary=len(rows)-len(nonloop),eos=sum(x['eos']for x in g['rows']),notNewTest=True,notUsedForSelection=True,rows=rows);a[f'all{len(rows)}FullPrefixesAndContinuationsActuallyRead']=True
 if group=='original17':a.update(meaningPolicySha256=sha(R.parent/'round10/full-meaning-policy.json'),wholeMeaningSensitivityPermittingInstrumentEllipsis=1,nonloopSensitivityCountingAnyFiniteListAsLoop=[4,3,2],firstSentenceSensitivityStrictDataInitiativeCategory=6,firstSentenceSensitivityPermittingColdEscapeAndPassiveHonorific=9)
 if group=='daily12':a.update(wholeMeaningSensitivityAllowingUnstatedDinnerQuestion=1,longLoopsSensitivityCountingFiniteCookingAsLoop=7)
 if group=='native8':a.update(contentBeyondBackchannel=2,explicitContextObjectReferences=0,newInformationResponses=0,minimalAcknowledgmentsOrOpinionActs=2)
 if group=='mrmp5':a.update(contentBeyondBackchannel=0,explicitContextObjectReferences=0,wholeMeaningSensitivityAllowingAdditionalPlaceQuestion=1,wholeMeaningSensitivityAllowingUnstatedRecommendation=1,wholeMeaningSensitivityAllowingBothWeakQuestions=2,independentSpeakerCombinationFamilies=1,distinctPublicSpeakerIds=3,notIndependentFiveSpeakers=True)
 (D/manual).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
 if group=='original17':subprocess.run(['python',str(R.parent/'round10/review.py'),'--generation',str(p),'--manual',str(D/manual),'--out',str(D/'original17-review.json')],check=True,stdout=subprocess.DEVNULL)
 print(group,a['wholeMeaning'],a['longLoopsPrimary'],a['eos'])
