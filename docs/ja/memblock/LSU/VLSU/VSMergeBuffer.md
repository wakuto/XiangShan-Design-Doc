```markdown
# ベクトルStoreマージユニット VSMergeBuffer

## 機能説明

freelistベースのキューであり、VSSplitモジュールから送信されたリクエストを受信し、バックエンドが発行する各uopに対してエントリを要求し、uopの関連情報を保存し、Storeパイプラインから返されたデータを収集し、そのuopに分割されたすべてのメモリアクセスリクエストを受信した後にバックエンドとStore Queueに書き戻します。

### 特性 1：uopの分割メモリアクセスリクエストの維持

VSSplitモジュールのパイプライン第2ステージでVSMergeBufferにエントリ申請を行い、同サイクルでVSMergeBufferはVSSplitにエントリのインデックスを返し、同時に対応するエントリのallocatedがtrueに設定されます。
エンキューと同時に、対応するエントリのカウンタに現在のuopが分割されたメモリアクセスリクエストの数が書き込まれます。
各uopに1つのエントリを割り当て、各エントリは収集する必要のあるflowの数を維持します。すべて収集されるとuopfinishとマークされ、uop単位で書き戻されます。
uopfinishとマークされたエントリの中から1つを選択してバックエンドに書き戻し、複数のエントリが書き戻し可能な場合はインデックスの小さいものが先に書き戻されます。同時に、対応するフラグがクリアされます。

### 特性 2：例外処理

パイプラインの出力情報に基づき、例外発生時にExceptionVec、vstartなどの対応するデータを正しく設定します。

### 特性 3：StoreMisalignBufferのflush信号に基づくuopのflush要否のマーキング

非整列ベクトルストアメモリアクセスには特殊性があり、StoreMisalignBufferがベクトルストアのflush信号を生成すると、VSMergeBufferに送られます。
VSMergeBufferは対応するエントリをneedRSReplayに設定し、最終的にIssue Queueに再発行を通知します。


## 全体ブロック図
単一モジュールのためブロック図はありません。

## 主要ポート

|                       | 方向 | 説明 |
|------:                |:-----|:-----|
|frompipeline           |In   |Storeパイプラインからの読み取りデータリターンを受信              |
|fromSplit.req          |In   |VSSplitモジュールからのエントリ申請を受信                   |
|fromSplit.resp         |Out  |VSSplitモジュールへのフィードバック、割り当て成功/失敗、割り当てられたエントリ      |
|uopWriteback           |Out  |実行完了したuopをバックエンドに書き戻す                         |
|toLsq                  |Out  |実行完了したuopがバックエンドに書き戻される際にStore Queueのエントリ状態を更新 |
|redirect               |In   |リダイレクトポート                                     |
|feedback               |Out  |バックエンドのIssue Queueへの再発行要否のフィードバック             |
|fromMisalignBuffer     |In   |StoreMisalignBufferからのflush信号を受信     |

## インターフェースタイミング

インターフェースのタイミングは比較的単純なため、テキストでの説明のみとします。

|                       | 説明 |
|------:                |:-----|
|frompipeline           |Valid、Readyあり。データはValid && ready時に有効               |
|fromSplit.req          |Valid、Readyあり。データはValid && ready時に有効               |
|fromSplit.resp         |Validあり。データはValid時に有効                      |
|uopWriteback           |Valid、Readyあり。データはValid && ready時に有効               |
|toLsq                  |Validあり。データはValid時に有効                      |
|redirect               |Validあり。データはValid時に有効                      |
|feedback               |Validあり。データはValid時に有効                      |
|fromMisalignBuffer     |Validなし。データは常に有効と見なされ、対応する信号が発生すると即座に応答    |


```
