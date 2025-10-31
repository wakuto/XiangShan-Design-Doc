```markdown
# ベクトルLoadマージユニット VLMergeBuffer

## 機能説明

freelistベースのキューであり、VLSplitモジュールから送信されたリクエストを受信し、バックエンドが発行する各uopに対してエントリを要求し、uopの関連情報を保存し、Loadパイプラインから返されたデータを収集し、そのuopに分割されたすべてのメモリアクセスリクエストを受信した後にバックエンドとLoad Queueに書き戻します。

### 特性 1：uopの分割メモリアクセスリクエストの維持

VLSplitモジュールのパイプライン第2ステージでVLMergeBufferにエントリ申請を行い、同サイクルでVLMergeBufferはVLSplitにエントリのインデックスを返し、同時に対応するエントリのallocatedがtrueに設定されます。
エンキューと同時に、対応するエントリのカウンタに現在のuopが分割されたメモリアクセスリクエストの数が書き込まれます。
各uopに1つのエントリを割り当て、各エントリは収集する必要のあるflowの数を維持します。すべて収集されるとuopfinishとマークされ、uop単位で書き戻されます。
uopfinishとマークされたエントリの中から1つを選択してバックエンドに書き戻し、複数のエントリが書き戻し可能な場合はインデックスの小さいものが先に書き戻されます。同時に、対応するフラグがクリアされます。

### 特性 2：データのマージ

Loadパイプラインの出力情報に基づき、uopを単位としてデータをマージします。マージ時には、例外の有無、要素の位置、マスクなどに基づいてマージを行います。

### 特性 3：例外処理

パイプラインの出力情報に基づき、例外発生時にExceptionVec、vstartなどの対応するデータを正しく設定します。

### 特性 4：しきい値によるバックプレッシャー {#sec:VLM-THRESHOLD}

デッドロックを避けるため、VLMergeBufferの空きエントリが6個以下になると、しきい値反応信号がVLSplitに生成されます。これによりVLSplit Pipeにバックプレッシャーがかかります。
[@sec:VLS-THRESHOLD] [VLMergeBufferのThreshold信号に基づくバックプレッシャー](VLSplit.md) を参照してください。

## 全体ブロック図

単一モジュールのためブロック図はありません。

## 主要ポート

|                | 方向 | 説明                                                |
| -------------: | :--- | :-------------------------------------------------- |
|   frompipeline | In   | Loadパイプラインからの読み取りデータリターンを受信    |
|  fromSplit.req | In   | VLSplitモジュールからのエントリ申請を受信             |
| fromSplit.resp | Out  | VLSplitモジュールへのフィードバック、割り当て成功/失敗、割り当てられたエントリ |
|   uopWriteback | Out  | 実行完了したuopをバックエンドに書き戻す             |
|          toLsq | Out  | 実行完了したuopがバックエンドに書き戻される際にLoad Queueのエントリ状態を更新 |
|       redirect | In   | リダイレクトポート                                  |
|       feedback | Out  | バックエンドのIssue Queueへのフィードバック、現在バックエンドでは何も処理しない |
|        toSplit | Out  | VLMergeBufferがしきい値に近づいていることをVLSplitモジュールへフィードバック |

## インターフェースタイミング

インターフェースのタイミングは比較的単純なため、テキストでの説明のみとします。

|                    | 説明                                               |
| -----------------: | :------------------------------------------------- |
|       frompipeline | Valid、Readyあり。データはValid && ready時に有効     |
|      fromSplit.req | Valid、Readyあり。データはValid && ready時に有効     |
|     fromSplit.resp | Validあり。データはValid時に有効                     |
|       uopWriteback | Valid、Readyあり。データはValid && ready時に有効     |
|              toLsq | Validあり。データはValid時に有効                     |
|           redirect | Validあり。データはValid時に有効                     |
|           feedback | Validあり。データはValid時に有効                     |
| fromMisalignBuffer | Validなし。データは常に有効と見なされ、対応する信号が発生すると即座に応答 |


```
