# Storeアドレス実行ユニット StoreUnit

## 機能説明

ストア命令アドレスパイプラインは、S0/S1/S2/S3/S4の5つのステージに分かれています（図\ref{fig:LSU-StoreUnit-Pipeline}参照）。ストアアドレス発行キューからの要求を受け取り、処理した後、バックエンドとベクターユニットに応答します。処理中、発行キューとStoreQueueにフィードバックを提供し、最終的に書き戻しを実行します。途中で例外が発生した場合、命令は発行キューから再発行されます。

![StoreUnitパイプライン](./figure/LSU-StoreUnit-Pipeline.svg){#fig:LSU-StoreUnit-Pipeline}

### 特性1：StoreUnitはスカラーストア命令をサポート

* ステージ0:

    * VAアドレスを計算

    * アドレスの不整合チェックをuop.cf.exceptionVec(storeAddrMisaligned)に更新

    * DTLB読み取り要求をTLBに発行

    * 命令のマスク情報をs0_mask_outに更新し、StoreQueueに送信

    * データ幅が128ビットのストア命令かどうかを判断

* ステージ1:

    * DTLBクエリ結果をstoreQueueに更新

    * ストア-ロード違反チェック要求をLoadQueueに送信

    * DTLBがヒットした場合、ストア発行情報をバックエンドに送信

* ステージ2:

    * MMIO/PMPチェックとstoreQueueの更新

    * DTLB結果をfeedback_slow経由でバックエンドに更新

* ステージ3

    * バックエンドへの送信時にRAW違反チェックと同期するため、追加のサイクルが必要

* ステージ4

    * スカラーストアがライトバックを開始し、stout経由でバックエンドに送信

### 特性3：StoreUnitはベクトルストア命令をサポート

StoreUnitは、非整列ストア命令をスカラ操作と同様に処理しますが、以下の点が異なります。

* ステージ0:

    * vsSplit実行要求を受け入れます。これはスカラ要求よりも優先度が高く、仮想アドレス計算を必要としません。

* ステージ1:

    * vecVaddrOffsetとvecTriggerMaskを計算

* ステージ2:

    * バックエンドにfeedback_slow応答を送信する必要はありません

* ステージ4:

    * ベクトルストアがライトバックを開始し、vecstout経由でバックエンドに送信します。

### 特性2：StoreUnitは非整列ストア命令をサポート

StoreUnitは、非整列ストア命令をスカラ操作と同様に処理しますが、以下の点が異なります。

* ステージ0:

    * StoreMisalignBufferからの要求を受け入れます。これはベクトルおよびスカラ要求よりも優先度が高く、仮想アドレス計算を必要としません。

* ステージ2:

    * バックエンドにフィードバック応答を送信する必要はありません。

    * 要求がStoreMisalignBufferからではなく、16バイト境界を越えない非整列要求である場合、StoreMisalignBufferで処理する必要があります。

        * io_misalign_bufインターフェースを介してStoreMisalignBufferにエンキュー要求を送信

        * ステージ3には入りません

    * 要求がStoreMisalignBufferからであり、16バイト境界を越えない要求である場合、再試行または書き戻し応答をStoreMisalignBufferに送信する必要があります。

        * io_misalign_soutインターフェースを介してStoreMisalignBufferに応答を送信

        * TLBミスが発生した場合は再試行が必要、それ以外の場合は書き戻し

        * ステージ3には入りません


\newpage

## 全体ブロック図

![StoreUnit全体ブロック図](./figure/LSU-StoreUnit.svg){#fig:LSU-StoreUnit}

\newpage

## インターフェースのタイミング
