# GrantBuffer

## 基本機能
GrantBufはMainPipeからタスクを受け取り、タスクの種類に基づいて転送します。主なカテゴリは次のとおりです。
- プリフェッチ応答（opcode = HintAck）は、プリフェッチ応答キューpftRespQueue（サイズ=10）に入り、FIFO順でプリフェッチャに発行されます。
- チャネルD応答（opcode = Grant/GrantData/ReleaseAck）は、grantQueue（サイズ=16）に入り、FIFO順でバスのチャネルDに発行されます。Grant/GrantAckについては、その情報もinflightGrantバッファ（サイズ=16）に格納され（Grantが送信されたがまだ確認されていないことを示す）、L1がチャネルE経由でGrantAckを返すのを待ってから情報をクリアします。
- マージされたリクエスト（task.mergeA = true）は、上記の両方を同時に実行します。

### 機能1：MainPipeエントリのブロッキング
GrantBufは、[パイプラインエントリ情報 + パイプラインステージS1/S2/S3/S4/S5のステータス + 内部pftRespQueue、inflightGrant、grantQueueのステータス]に基づいて、[リクエストエントリのブロッキング情報]をReqArbに提供します。

3種類のリソースの統計：
- GrantBufリソース不足：占有されているGrantBuf数 + パイプラインステージS1/S2/S3/S4/S5の潜在的なGrantBuf数（sinkAまたはsinkCから）> 16
- チャネルEリソース不足：inflightGrant + パイプラインステージS1/S2/S3/S4/S5でチャネルEを必要とする潜在的なGrantAckの戻り数（sinkAから）> 16
- プリフェッチRespQueueリソース不足：占有されているpftRespQueue数 + パイプラインステージS1/S2/S3/S4/S5の潜在的なpreRespQueue使用量（sinkAから）> 10

S1でMainPipeへのチャネルエントリをブロックする条件
- Aチャネル：上記のリソース不足のいずれか
- チャネルB：inflightGrantバッファにチャネルBと同じアドレスを持つ未完了の操作が含まれている限り
- チャネルC：GrantBufリソース不足

3種類のMSHRリソース不足（最大リソース-1）：
- GrantBufリソース不足：占有されているGrantBuf数 + パイプラインステージS1/S2/S3/S4/S5の潜在的なGrantBuf数（sinkAまたはsinkCから）> 15
- Eチャネルリソース不足：inflightGrant + パイプラインステージS1/S2/S3/S4/S5から潜在的に必要とされるGrantAckの数（sinkAから）> 15
- プリフェッチRespQueueリソース不足：占有されているpftRespQueue数 + パイプラインステージS1/S2/S3/S4/S5の潜在的なpreRespQueue使用量（sinkAから）> 9

MSHRがMainpipeに入るためのブロッキング条件は、上記の3つのシナリオのいずれかです。


### 機能2：早期ウェイクアップ
MainPipeのCustomL1Hintモジュールは、GrantBufの3サイクル前にl1Hint信号を発行し、L1D$のmissqの早期ウェイクアップを容易にします。GrantBufferは、S1でパイプラインエントリをブロックするためのリソース情報を提供し、MainPipeは、パイプラインに既にあるシナリオに基づいてl1Hint信号をいつ発行するかを正確に予測します。

### 機能3：異なるデータ幅の処理
1ビートを含むGrant/ReleaseAckの場合、grantQueueからデキューされ、直接バスに送信されます。2ビートを含むGrantDataの場合、最初のビートはデキュー時に直接バスに送信され、2番目のビートはgrantBufに格納されます。その後、grantBuf内のデータが優先的に送信されます。grantBufが空になった後、grantQueueの次の要素をデキューできます。

## 全体ブロック図
![GrantBuffer](./figure/GrantBuf.svg)
