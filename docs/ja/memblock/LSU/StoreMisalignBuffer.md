# Store非整列メモリアクセスユニット StoreMisalignBuffer

## 機能説明

StoreMisalignBufferは、16バイト境界を越える1つの非整列ストア命令を格納します。実行ロジックは7つの状態を持つステートマシンです。StoreUnit内の命令が非整列で16バイト境界を越えると検出されると、StoreMisalignBufferへのエントリを要求します。StoreMisalignBufferはこのストアをラッチし、2つのストアメモリフローに分割して、StoreUnitに再入力します。

StoreMisalignBufferは、自身が開始したストアアクセスを収集します。両方のストアアクセスが完了した後、ページを越えない非整列であれば、書き戻します。バックエンドへのスカラ非整列書き戻しは、StoreUnit 1がスカラ書き戻しを有効にしていない場合に行う必要があります。満たされない場合、バックエンドへのStoreMisalignBufferの書き戻しはブロックされます。VSMergeBufferへのベクトル非整列書き戻しは、StoreUnit 1がベクトルスカラ書き戻しを有効にしていない場合に行う必要があります。満たされない場合、VSMergeBufferへのStoreMisalignBufferの書き戻しはブロックされます。

4Kページを越えるストアについては、命令がRobの先頭に到達したときにのみ実行できることを要求します。この間に古いストアがStoreMisalignBufferに入ると、現在の4Kページ越えストアを追い出し、needFlushPipeフラグをtrueに設定します。ストアが最終的に書き戻されると、リダイレクトを生成します。

ベクトルの場合、ベクトルストアフローが追い出されると、VSMergeBufferに通知して対応するエントリをneedRsReplayとしてマークさせ、uopを再送させます。

### 特性1：16バイト境界を越える非整列ストアの分割メモリアクセスをサポート

実行されたフローに基づいて異なる遷移が発生します。ステートマシンは、最初のフローが書き戻された後にs_req状態に入り、2番目のフローを送信します。最初のフローが例外を伴ってStoreMisalignBufferに書き戻された場合、2番目のフローを実行せずに例外情報を直接バックエンドに送信します。どのフローの書き戻しも、何らかの理由でリプレイをトリガーする可能性があり、StoreMisalignBufferはリプレイの原因に関係なくそのフローをStoreUnitに再送します。

- sb命令は非整列を発生させることはありません。

- sh操作は、対応する2つのsb操作に分割されます。

![代替テキスト](./figure/StoreMisalign-sh.png)

- swはアドレス分割方法によって異なります。

![代替テキスト](./figure/StoreMisalign-sw.png)

- sdはアドレス分割方法によって異なります。

![代替テキスト](./figure/StoreMisalign-sd.png)

### 特性2：ベクトル非整列操作をサポート

ベクトル非整列フローは、スカラ非整列フローと同様に処理されますが、ベクトルはVSMergeBufferに書き戻され、スカラは直接バックエンドに書き戻される点が異なります。


### 特性3：非メモリ空間への非整列ストアをサポートしない

非メモリ空間での非整列ストアはサポートされていません。非メモリ空間のストアが非整列である場合、StoreAddrMisalign例外が発生します。

### 特性4：ページ越えストアをサポート

ストア操作はSbufferに書き込む必要があるため、ページ越えアクセスの場合は2つの物理アドレスが生成されます。下位ページの物理アドレスはStoreQueueに存在できますが、上位ページの物理アドレスは別のストレージが必要です。我々はそれをStoreMisalignBufferに格納することを選択します。その結果、ページ越えストア操作の場合、命令がStore QueueからSbufferにコミットされるまで待ってから、StoreMisalignBufferの対応するエントリをクリアする必要があります。したがって、書き戻しの目的で、StoreMisalignBufferに現在ラッチされているメタデータとアドレスをStoreQueueに提供します。具体的には、robとStoreQueueから受信した信号に基づいて、現在のストアメタデータをラッチして保持する必要があるかどうかを判断します。

## 全体ブロック図

![代替テキスト](./figure/StoreMisalign-FSM.svg)


**状態紹介**

| 状態 | 説明 |
| ---: | :--- |
| s_idle | 非整列ストアuopの進入を待機 |
| s_split | 非整列ストアを分割 |
| s_req | 分割された非整列ストア操作をStoreUnitにディスパッチ |
| s_resp | StoreUnitの書き戻し |
| s_wb | バックエンドまたはVSMergeBufferへの書き戻し |
| s_block | Store QueueがエントリをSbufferに書き込むまで、命令のデキューをブロック |

## 主要ポート

| | 方向 | 説明 |
| ---: | :--- | :--- |
| redirect | In | リダイレクトポート |
| req | In | StoreUnitからのエンキュー要求を受信 |
| rob | In | Robから関連メタデータ情報を受信 |
| splitStoreReq | Out | StoreUnitに送信される分割フローのメモリアクセス要求 |
| splitStoreResp | In | StoreUnitから書き戻される分割フローのメモリアクセス応答を受信 |
| writeBack | out | バックエンドへのスカラ非整列書き戻し |
| vecWriteBack | Out | VSMergeBufferへのベクトル非整列書き戻し |
| StoreOutValid | In | Store Unitにバックエンドに書き戻されるストア命令が存在 |
| StoreVecOutValid | In | Store UnitにVSMergeBufferに書き戻されるベクトルストア命令が存在 |
| overwriteExpBuf | Out | 浮動 |
| sqControl | In/Out | Store Queueとの対話インターフェース |
| toVecStoreMergeBuffer | Out | フラッシュ関連情報をVSMergeBufferに送信 |


## インターフェースタイミング

インターフェースのタイミングは比較的単純なため、テキスト説明のみを提供します。

| | 説明 |
| ---: | :--- |
| redirect | Validあり。データはValid時に有効 |
| req | Valid、Readyあり。データはValid && ready時に有効 |
| rob | Validなし。データは常に有効と見なされ、対応する信号が発生すると応答 |
| splitStoreReq | Valid、Readyあり。データはValid && ready時に有効 |
| splitStoreResp | Validあり。データはValid時に有効 |
| writeBack | Valid、Readyあり。データはValid && ready時に有効 |
| vecWriteBack | Valid、Readyあり。データはValid && ready時に有効 |
