"""Explicit selected daily12 judgments after full unedited reading."""
import pathlib,json,hashlib
R=pathlib.Path(__file__).resolve().parents[1];E=R/'execution';p=E/'daily-new-python.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(p)=='305511ba62a7efc1c02bab7bc72b1a1019098cf64692a101623fec365a36d54a';g=json.loads(p.read_text());reasons=[
'帰りに行くのが行くのは何かの事だろうと思いますかという不成立な主題・名詞化と自問になり、仕事帰りの行動がつながらない。有限19tokensの非長期loopだが行くの侵入反復。',
'残り物を使う夕食の話が何か食べたかったかという不明な相手への疑問になり、主体・因果が成立しない。短いEOS非loop。未提示他者の希望確認という弱い代替のみ別記。',
'友達との予定を継がず日常生活の不成立な予想から週間天気予報へ逸れる。先まで・週間天気予報を長く反復して192tokens切断。',
'準備を継がず雨が降り降り・雨雨という活用と文字のloop、後半も雨が降ってを長く繰り返し切断。',
'今夜は寝るのかなから寝るのは何か寝てるんですかと主述・問いが崩れる。有限19tokensEOSでprimary非長期loopだが睡眠句の侵入反復。広くloopに数える感度も記録。',
'趣味の開始行動を継がず行くのが・その後を重ね、おかあさんの所有句とおおおの長い反復へ逸れて切断。',
'待ち合わせ時刻に対して天気の毒が出るのかという語結合も意味も不明な質問を返す。短いEOS非loop。',
'疲労への応答がなく天井に出てきた、今日は一緒に出てきた、いつもののこと等を反復し、後半それを・その時に・いつまでもの長いloopへ崩れる。',
'卵の調理相談に自分は何かの時間を作るのが多いのでしょうかという対象不明の自問が返り、文脈がつながらない。短いEOS非loop。',
'週末の体験に天気はどうしてもかなりそうですねと不成立の述語を返し、話題と行為が成立しない。短いEOS非loop。',
'近況への応答が天井の話はどんな話を聞いているのかという不明な話題・係りに逸れる。短いEOS非loop。',
'雨で予定の公園をどうするかという相談に、公園の公園という不自然な所有句と既知の予定への再質問を返す。有限14tokensEOSでprimary非長期loop、所有句は侵入反復。発話の言い直しとして許す弱い意味代替のみ別記。'];loops={2,3,5,7};rows=[]
for i,(x,reason)in enumerate(zip(g['rows'],reasons,strict=True)):
 rows.append(dict(id=x['id'],fullOutputMeaningful=False,fullOutputLoop=i in loops,intrusiveRepetition=i in loops or i in {0,4,11},reason=reason,prefixAndTextSha256=hashlib.sha256(json.dumps(dict(prefix=x['prefix'],text=x['text']),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
a=dict(generationSha256=sha(p),reviewer='Assistant actual complete reading of all12 selected daily prefixes and continuations; not independent blind human',actualRetainedUpdates=10000,selectedStep=9000,evaluatedStep=9000,all12FullPrefixesAndContinuationsActuallyRead=True,wholeMeaning=0,longLoopsPrimary=4,eos=sum(x['eos']for x in g['rows']),wholeMeaningSensitivityAllowingUnstatedDinnerQuestion=1,wholeMeaningSensitivityAllowingParkSpeechRestart=1,wholeMeaningSensitivityAllowingBothWeakReadings=2,longLoopsSensitivityCountingFiniteSleepAsLoop=5,notNewTest=True,notUsedForSelection=True,rows=rows);(E/'daily-new-reading.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in a.items()if k!='rows'}))
