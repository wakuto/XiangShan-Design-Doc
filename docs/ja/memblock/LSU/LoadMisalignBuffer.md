# Load非整列メモリアクセスユニット LoadMisalignBuffer

## 機能説明

LoadMisalignBufferには、16バイト境界を越える非整列Load命令が1つ格納されます。実行ロジックは7つの状態を持つステートマシンです。LoadUnitで命令が非整列で16バイト境界を越えると検出されると、LoadMisalignBufferへのエントリを要求します。LoadMisalignBufferはこのLoadをラッチし、2つの別々のLoadメモリアクセス（フロー）に分割してLoadUnitに再入力します。

LoadMisalignBufferは、自身が発行したロードメモリアクセスを収集します。両方のロードメモリアクセスが実行を完了すると、データ連結を行い、その後、LoadUnitに再度ウェイクアップ操作を送信します。この操作は実際にはLoadUnitパイプラインに入って実行されるのではなく、単にウェイクアップ信号をトリガーし、それを3サイクル遅延させます。3サイクル後、LoadMisalignBufferはLoadUnitから再度ライトバック要求を受信し、ウェイクアップ操作から発信されたものとしてマークされます。この時点で、LoadMisalignBufferはデキューし、バックエンドに真にライトバックし、バイパスも行います。

バックエンドへのスカラー非整列ライトバックは、LoadUnit 1がスカラーライトバックを有効にしていないときに実行する必要があります。この条件が満たされない場合、LoadMisalignBufferのバックエンドへのライトバックはブロックされます。VLMergeBufferへのベクトル非整列ライトバックは、LoadUnit 1がベクトル・スカラーライトバックを有効にしていないときに実行する必要があります。この条件が満たされない場合、LoadMisalignBufferのVLMergeBufferへのライトバックはブロックされます。

### 特徴1：16バイト境界を越える非整列Loadの分割メモリアクセスをサポート

すでに実行されたフローに基づいて変更が発生します。ステートマシンは、最初のフローがライトバックされた後、s_req状態に遷移し、次に2番目のフローを送信します。最初のフローが例外を伴ってLoadMisalignBufferにライトバックされた場合、2番目のフローを実行せずに例外情報を直接バックエンドにライトバックします。どちらのフローからのライトバックも、何らかの理由でリプレイをトリガーする可能性があり、LoadMisalignBufferはリプレイの原因に関係なく、そのフローをLoadUnitに再送することを選択します。

-   lb命令は決して非整列になることはありません。

-   lhは2つの対応するlb操作に分割されます。

    ![alt text](./figure/LoadMisalign-lh.png)

-   lwはアドレスに基づいて異なる分割方法があります。

    ![alt text](./figure/LoadMisalign-lw.png)

-   ldはアドレスに基づいて異なって分割されます。

    ![alt text](./figure/LoadMisalign-ld.png)

### 特徴2：ベクトル非整列操作をサポート

ベクトル非整列フローの処理は、スカラー非整列処理と一致していますが、ベクトルはVLMergeBufferにライトバックされ、スカラーは直接バックエンドにライトバックされる点が異なります。


### 特徴3：メモリ空間外の非整列Loadをサポートしない

非メモリ空間での非整列Loadはサポートされていません。非メモリ空間のLoadが非整列である場合、LoadAddrMisalign例外が生成されます。


## 全体ブロック図

![alt text](./figure/LoadMisalign-FSM.svg)

**状態紹介**

| 状態 | 説明 |
| :--- | :--- |
| s_idle | 非整列Load uopの入力を待機中 |
| s_split | 非整列Loadを分割 |
| s_req | 分割された非整列Load操作をLoadUnitにディスパッチ |
| s_resp | LoadUnitのライトバック |
| s_comb_wakeup_rep | 2つの非整列Load操作の結果をマージし、wakeup uopを発行 |
| s_wb | バックエンドまたはVLMergeBufferにライトバック |



## 主要ポート

| | 方向 | 説明 |
| :--- | :--- | :--- |
| redirect | In | リダイレクトポート |
| req | In | LoadUnitからのエンキュー要求を受信 |
| rob | In | 内部で中断 |
| splitLoadReq | Out | LoadUnitに送信される分割フローのメモリアクセス要求 |
| splitLoadResp | In | LoadUnitによってライトバックされた分割フローのメモリ応答を受信 |
| writeBack | out | バックエンドへのスカラー非整列ライトバック。 |
| vecWriteBack | Out | VLMergeBufferへのベクトル非整列ライトバック |
| loadOutValid | In | Load UnitにバックエンドにライトバックしようとしているLoad命令があります |
| loadVecOutValid | In | Load UnitにVLMergeBufferにライトバックするVector Load命令があります |
| overwriteExpBuf | Out | ぶら下がり |
| loadMisalignFull | Out | LoadMisalignBuffer満杯フラグ |


## インターフェース時序

インターフェースのタイミングは比較的単純なので、テキストでの説明のみを提供します。

| | 説明 |
| :--- | :--- |
| redirect | Validを持つ。データはValidと共に有効 |
| req | Valid、Readyを持つ。データはValid && readyと共に有効 |
| rob | 内部で中断 |
| splitLoadReq | Valid、Readyを持つ。データはValid && readyと共に有効 |
| splitLoadResp | Validを持つ。データはValidと共に有効 |
| writeBack | Valid、Readyを持つ。データはValid && readyと共に有効 |
| vecWriteBack | Valid、Readyを持つ。データはValid && readyと共に有効 |
| loadOutValid | Validを持たない。データは常に有効と見なされ、対応する信号が発生すると即座に応答 |
| loadVecOutValid | Validを持たない。データは常に有効と見なされ、対応する信号が発生すると即座に応答 |
| overwriteExpBuf | ぶら下がり |
| loadMisalignFull | Validを持たない。データは常に有効と見なされ、対応する信号が発生すると即座に応答 |
