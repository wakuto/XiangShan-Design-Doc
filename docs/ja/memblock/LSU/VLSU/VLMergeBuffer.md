# ベクトルLoadマージユニット VLMergeBuffer

## 機能説明

freelist ベースのキューであり、VLSplit モジュールから送られるリクエストを受け取り、バックエンドが発行する各 uop に対してエントリを割り当てる。uop の関連情報を保持し、Load パイプラインから返ってくるデータを集約し、その uop に対して分割発行したすべてのメモリアクセスを受け取ったのち、バックエンドおよび Load Queue に書き戻す。

### 特性 1：uop の分割メモリアクセス要求の管理

VLSplit モジュールのパイプライン第 2 ステージで VLMergeBuffer にエントリを要求し、同周期に VLMergeBuffer は VLSplit へエントリ index を返し、該当エントリの allocated を true に設定する。
エンキューと同時に、対応するエントリのカウンタへ当該 uop が分割されたメモリアクセス数を書き込む。
各 uop に 1 エントリを割り当て、各エントリで収集すべき flow 数を管理する。すべて収集し終えると uopfinish を立て、uop 単位で書き戻す。
uopfinish が立ったエントリから 1 件を選びバックエンドへ書き戻す。複数の候補がある場合は index が小さいものを先に処理し、書き戻し後は対応するフラグをクリアする。

### 特性 2：データのマージ

Load パイプラインの出力情報に基づき、uop 単位でデータをマージする。例外の有無、要素位置、マスクといった情報を考慮して統合する。

### 特性 3：例外処理

パイプラインの出力情報を参照し、例外が発生した場合は ExceptionVec や vstart などの関連データを正しく設定する。

### 特性 4：しきい値によるバックプレッシャー {#sec:VLM-THRESHOLD}

デッドロックを避けるため、VLMergeBuffer の空きエントリが 6 個以下になると VLSplit へ threshold 信号を送出し、VLSplit パイプラインにバックプレッシャーを掛ける。
[@sec:VLS-THRESHOLD] [VLMergeBuffer の Threshold 信号によるバックプレッシャ](VLSplit.md) を参照のこと。

## 全体ブロック図

単一モジュールのためブロック図はありません。

## 主要ポート

|                | 方向 | 説明                                                |
| -------------: | :--- | :-------------------------------------------------- |
|   frompipeline | In   | Load パイプラインからの読み取りデータリターンを受信  |
|  fromSplit.req | In   | VLSplit モジュールからのエントリ申請を受信          |
| fromSplit.resp | Out  | VLSplit モジュールへのフィードバック、割り当て成功/失敗、割り当てられたエントリ |
|   uopWriteback | Out  | 実行完了した uop をバックエンドに書き戻す           |
|          toLsq | Out  | 実行完了した uop がバックエンドに書き戻される際に Load Queue のエントリ状態を更新 |
|       redirect | In   | リダイレクトポート                                  |
|       feedback | Out  | バックエンド Issue Queue へのフィードバック（現在は未使用） |
|        toSplit | Out  | VLMergeBuffer が閾値に近いことを VLSplit モジュールへフィードバック |

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

