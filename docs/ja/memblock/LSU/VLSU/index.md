# ベクトルメモリアクセス

## サブモジュールリスト

| サブモジュール | 説明 |
| --- | --- |
| [VLSplit](VLSplit.md) | ベクトルロードuop分割モジュール |
| [VSSplit](VSSplit.md) | ベクトルストアuop分割モジュール |
| [VLMergeBuffer](VLMergeBuffer.md) | ベクトルロードフロー合流モジュール |
| [VSMergeBuffer](VSMergeBuffer.md) | ベクトルストアフロー合流モジュール |
| [VSegmentUnit](VSegmentUnit.md) | ベクトルセグメント実行モジュール |
| [VfofBuffer](VfofBuffer.md) | ベクトルfault-only-first命令ライトバックVLレジスタuop収集ライトバックモジュール |


## 機能説明

- RVV 1.0の全メモリアクセス命令を完全にサポート
- ベクトルLoad/Store命令の順不同スケジューリングをサポート
- ベクトルLoad/Store命令から分割されたUopの順不同実行をサポート
- ベクトル順不同違反のチェックと回復をサポート
- 非整列ベクトルメモリアクセスをサポート
- 非メモリ空間へのベクトルメモリアクセスはサポートしない

### パラメータ設定

| パラメータ | 設定（項目数） |
| :---: | :---: |
| VLEN | 128 |
| VLMergeBuffer | 16 |
| VSMergeBuffer | 16 |
| VSegmentBuffer | 8 |
| VFOFBuffer | 1 |

### 機能概要

VLSIssueQueueに入る前に、Dispatch段階でLoad QueueまたはStore Queueのインデックスが割り当てられます。
ベクトルメモリアクセス命令はバックエンドでuopに分割された後、まずVsplitモジュールでデコード、マスクとアドレスオフセットの計算が行われ、同時にMergebufferエントリが要求されます。
新しいベクトルメモリアクセスアーキテクチャでは、スカラのLoadUnit & StoreUnit、およびLoad Queue & Store Queueが再利用されます。

ベクトルLoadとStoreは2つのIssue Queueを共有します。
ベクトルLoadの場合、2つのIssue Queueは2つのVLSplitに接続されます。
ベクトルStoreの場合、2つのIssue Queueは2つのVSSplitに接続されます。
2つのVLSplitはそれぞれLoadUnit0、LoadUnit1に対応します。
2つのVSSplitはそれぞれStoreUnit0、StoreUnit1に対応します。
ベクトルLoadがReplay Queueによる再発行を必要とする場合、他のloadunitに再発行される可能性があります。ベクトルメモリアクセスがパイプラインから実行完了した後、mergebufferによって集約され、ライトバックされます。


## 全体ブロック図

全体ブロック図は更新予定
<!-- svgを使用してください -->
