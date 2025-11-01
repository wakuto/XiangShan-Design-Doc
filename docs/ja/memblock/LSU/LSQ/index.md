# メモリアクセスキュー LSQ

## サブモジュールリスト

| サブモジュール | 説明 |
| --- | --- |
| [VirtualLoadQueue](VirtualLoadQueue.md) | TODO |
| [LoadQueueRAR](LoadQueueRAR.md) | TODO |
| [LoadQueueRAW](LoadQueueRAW.md) | TODO |
| [LoadQueueReplay](LoadQueueReplay.md) | DONE |
| [LoadQueueUncache](LoadQueueUncache.md) | TODO |
| [LoadExceptionBuffer](LqExceptionBuffer.md) | TODO |
| [StoreQueue](StoreQueue.md) | DONE |


## 機能説明

LSQはLoadQueueとStoreQueueの2つの部分を含み、ポートの接続を容易にするためにラッパー層が設けられています。Lsqwrapperの役割は主に配線です。

* LoadQueue

  * LoadQueueRAR: RAR違反チェックキュー

  * LoadQueueRAW: RAW違反チェックキュー

  * LoadQueueUncache: MMIO/Noncacheableロード命令処理キュー

  * LoadQueueReplay: ロード命令スケジューリング再発行キュー

  * LoadExceptionBuffer: ロード命令例外処理キュー

  * VirtualLoadQueue: ロード命令順序維持キュー

* StoreQueue

#### 特性1: ロード命令のLqPtrとストア命令のSqPtrの更新

* タイミングの影響により、LqPtrとSqPtrの割り当ては2つの部分に分割されています。図を参照してください。

  ![LSQ割り当て](./figure/LSQ-LsqEnqCtrl.svg){#fig:LSQ-LsqEnqCtrl width=60%}

  * Dispatch段階

    * 各命令のLoadFlowまたはStoreFlow数を統計し、累加方式でLqPtrまたはSqPtrを計算します。

  * LSQエンキュー段階

    * LoadQueueまたはStoreQueueが維持するenqPtrに基づいて、累加方式で正確なLqPtrまたはSqPtrを計算します。

  * LsqEnqCtrl更新ロジック

    * パイプラインのフラッシュが発生した場合、フラッシュされたロードまたはストア命令数とコミット数に基づいて更新します。

    * パイプラインのフラッシュが発生せず、割り当て要求がある場合、エンキュー数とコミット数に基づいて更新します。

    * それ以外の場合、コミット数に基づいて更新します。

## 全体ブロック図

![LSQ全体フレームワーク](./figure/LSQ.svg){#fig:LSQ width=40%}



ewpage

## インターフェースタイミング

### ロード命令とストア命令のエンキューインターフェースタイミングの例

![エンキュー更新](./figure/LSQ-LsqEnqCtrl-Timing.svg){#fig:LSQ-LsqEnqCtrl-Timing width=90%}
