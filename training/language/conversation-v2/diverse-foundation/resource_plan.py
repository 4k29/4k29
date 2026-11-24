"""Use completed training receipts for CPU projections; resource probes are feasibility only."""
import pathlib,json,shutil
D=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def main():
 rates={};receipts={}
 for arm in ['A','B']:
  r=read(D/'run'/arm/'receipt-06459.json');receipts[arm]=r;rates[arm]=r['retained_targets']/r['elapsed_seconds']
 rows=[]
 for n in [10_000_000,30_000_000,100_000_000]:
  values=[n/v/3600 for v in rates.values()];rows.append(dict(teacher_targets=n,CPU2_driver_hours_range=[min(values),max(values)],with_30pct_allowance_hours_range=[min(values)*1.3,max(values)*1.3],approx_dense_training_FLOPs=6*11_225_280*n,includes_heldout_new_corpus=False))
 probes=read(D/'RESOURCE_PROBES.json')['probes'];usage=shutil.disk_usage(D)
 result=dict(environment=dict(CPU_quota=2,RAM_GiB=8,GPU=0,actual_overlay_free_bytes=usage.free),measured_driver_targets_per_second=rates,receipts=receipts,projections=rows,probes=probes,GPU_throughput_measured=False,caveat='Observed drivers include checkpoint/resume validation and varying CPU contention; range is planning only. New evaluation/acquisition, pauses and larger contexts/models need separate allowance. Dense6NT ignores attention/softmax overhead; no GPU hour estimate is measured.',next_storage_required='10–20GiB additional working headroom before expanding models/corpus, existing Git/history preserved',paid_resources_used=False)
 (D/'RESOURCE_PLAN.json').write_text(json.dumps(result,indent=2)+'\n')
 lines=['# 実測資源と次期学習の見積もり','','無料CPU quota2 / RAM8GiB / GPU0。A/Bの実学習driver時間から見積もる。停止中の壁時計や人間の確認時間はdriver時間と別。次の量の独立コーパスが確保されたという意味ではない。','','|教師targets|CPU2 driver時間の幅|30%余裕込み|概算dense 6NT FLOPs|','|---|---:|---:|---:|']
 for r in rows:
  lo,hi=r['CPU2_driver_hours_range'];a,b=r['with_30pct_allowance_hours_range'];lines.append(f"|{r['teacher_targets']:,}|{lo:.2f}–{hi:.2f}時間|{a:.2f}–{b:.2f}時間|{r['approx_dense_training_FLOPs']:.3g}|")
 lines+=['','この幅は同じ11.23M/context256/CPU2での概算。モデル拡大、context延長、推論・追加評価の時間は別。GPU速度・GPU時間は未測定で、無料で利用可能なGPUも確認されていない。有料資源は使わない。','','|構成|パラメータ|0更新forward/backward最大RSS|Adam moments未割当分|FP32 model+Adam一世代|','|---|---:|---:|---:|']
 for r in sorted(probes,key=lambda z:(z['parameters'],z['config']['context'])):lines.append(f"|dim{r['config']['dim']}/context{r['config']['context']}|{r['parameters']:,}|{r['maximum_RSS_KiB']/1024:.1f}MiB|{r['extra_Adam_RSS_bytes_not_measured']/1024**2:.1f}MiB|{r['FP32_model_plus_Adam_bytes_estimate']/1024**2:.1f}MiB|")
 lines+=['','RSSは単発の乱数モデルforward/backwardだけであり、optimizer更新も能力測定も0。Torch/corpus/activationがありパラメータだけでRAMは決まらない。並行worker・cold開始による非単調な速度をモデル学習速度の比較に使わない。GPU用には同一batchの実測が必要で、16GiB級を計画候補としても適合や速度を保証しない。','','大きい候補50.65Mでは全状態一世代約608MB（十進）、3保存点で約1.82GB、atomic pendingとrolling、Git objectsと作業コピーがさらに必要。現在の空きで容量拡大をそのまま開始しない。追加10–20GiB以上の作業余裕を確保し、原文・encoded corpus・lossless archive・Git保持・atomic世代を含む実予算を固定する。圧縮率やsparse省略量を実空きと混同しない。30M以上の原文を処理するにはストリーム化・indexed scheduleも別途実測する。','','まず採用可能な現代日本語原文を10M→30Mへ拡張し、11M基準の学習・自由生成の実測を行う。容量27.40Mやcontext512は別の比較とし、データ・Tokenizerと同時に変更しない。']
 (D/'RESOURCE_PLAN.md').write_text('\n'.join(lines)+'\n')
 print('Resource plan from actual full-pass receipts',rates)
if __name__=='__main__':main()
