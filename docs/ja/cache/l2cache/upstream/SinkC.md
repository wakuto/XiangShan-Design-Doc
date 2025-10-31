# SinkC

## 機能説明
SinkCはバスのCチャネルからのリクエスト（Release/ReleaseData/ProbeAck/ProbeAckData）を受信し、内部バッファの深さは3です。valid/readyハンドシェイクプロトコルを使用してCチャネルをブロックし、以下の操作を実行します。a. リクエストがRelease(Data)の場合、バッファエントリを割り当てて保存し、パイプラインがCリクエストを受け入れる準備ができたときに、RequestArbに送信してメインパイプラインに入ります。データが含まれている場合は、2サイクル遅延させて、リクエストがS3に到達したときにデータをMainPipeに送信します。b. リクエストがProbeAckDataの場合、MSHRに直接フィードバックを送信し、そのデータをReleaseBufに書き込みます。

### 機能1：RefillBufferのオーバーライド
現在、ミッシングリフィル操作は、まずデータをL1に返し、次にリフィルデータ（RefillBuf内）をL2のDataStorageに書き込むようにスケジュールするため、これら2つのステップの間に時間差が生じます。この間にL1からダーティデータがリリースされた場合、最新のデータがL2に書き込まれるように、ReleaseDataも同期的にそのデータをRefillBufに書き込み、既存のリフィルデータを上書きします。

### 機能2：ReleaseBufferのオーバーライド
MSHRがL1D$をプローブする必要があるリリースを処理する場合、このProbeAckDataは、MSHR内のリリースと一致すると、アクティブにデータをReleaseBufに書き込みます。

## 全体ブロック図
![SinkC](./figure/SinkC.svg)
