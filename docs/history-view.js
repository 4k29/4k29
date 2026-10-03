export function mountHistory(journal){
 const panel=document.querySelector('#question-history'),summary=panel.querySelector('summary'),list=panel.querySelector('.history-records'),status=panel.querySelector('.history-status');
 function update(){
  const review=journal.records.filter(r=>r.needsReview||r.unanswered).length;
  summary.textContent=`history / ${journal.records.length} saved${review?' · '+review+' review':''}`;
  status.textContent=journal.persisted?'このブラウザに最新300件を保存します。回答できた質問の言い回しを学習します。見直し対象・未登録の回答は除外し、外部には送信しません。':'保存を利用できないため、このページ内だけに記録しています。';
  const opened=new Set(Array.from(list.querySelectorAll('details[open]'),row=>row.dataset.recordId));
  list.replaceChildren();
  if(!journal.records.length){const empty=document.createElement('p');empty.textContent='まだ質問の記録はありません。';list.append(empty);return;}
  for(const record of [...journal.records].reverse()){
   const row=document.createElement('details');row.className='history-record';row.dataset.recordId=record.id;row.open=opened.has(record.id);const heading=document.createElement('summary');heading.textContent=(record.needsReview?'[見直し] ':record.unanswered?'[未登録あり] ':'')+record.question;
   const time=document.createElement('time');time.dateTime=record.at;time.textContent=new Date(record.at).toLocaleString('ja-JP',{timeZone:'Asia/Tokyo'})+' JST';
   const answer=document.createElement('p');answer.className='history-answer';answer.textContent=record.answer;
   const button=document.createElement('button');button.type='button';button.setAttribute('aria-pressed',String(record.needsReview));button.textContent=record.needsReview?'見直し対象から外す':'見直しに追加';button.addEventListener('click',()=>{journal.mark(record.id,!record.needsReview);update();});
   row.append(heading,time,answer,button);list.append(row);
  }
 }
 panel.querySelector('#history-export').addEventListener('click',()=>{const url=URL.createObjectURL(new Blob([journal.export()],{type:'application/json'}));const anchor=document.createElement('a');anchor.href=url;anchor.download='4k29-question-history.json';document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);});
 panel.querySelector('#history-clear').addEventListener('click',()=>{journal.clear();update();});
 update();return update;
}
