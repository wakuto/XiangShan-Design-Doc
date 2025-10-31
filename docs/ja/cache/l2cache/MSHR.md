# MSHR {#sec:mshr}

タスクにMSHRが割り当てられるかどうかは、キャッシュヒットのステータス、L1プロービングの必要性、処理フローの複雑さなどの要因に基づいて、メモリアクセスパイプライン（MainPipe）によって決定されます。詳細については、[@sec:reqarb-mainpipe] [リクエストアービタとメモリアクセスパイプライン](ReqArb_MainPipe.md)を参照してください。

## ライフサイクル

各MSHRには独自のライフサイクルがあります。MSHRエントリはMainPipeによって割り当てられ、MSHRがすべてのタスクを完了し、すべてのステートマシンステータスエントリをクリアすると、そのライフサイクルを終了します。各MSHRは、バスのトランザクションを待機するために長期間有効なままである場合がありますが、有限時間内にライフサイクルを終了する必要があります。そうでない場合、ライブロックまたはデッドロックを示します。

### MSHR ID

各MSHRには独自のID値があり、これはハードコードされており、IDはさまざまなMSHR間で異なります。

MSHRによって開始されたCHIリクエストでは、TxnID値の下位ビットがMSHR IDにバインドされます。

### 割り当て

MainPipeがMSHRエントリの割り当てを要求すると、MSHRCtlモジュール内のMSHRSelectorによって未割り当てのMSHRが選択されます。各MSHRの割り当てに対して、MainPipeは次の情報を提供する必要があります。

- キャッシュラインのヒットステータスとコヒーレンス状態
- MSHRステートマシンの初期状態
- リクエストの必須の元の情報（TileLinkリクエストまたはCHIリクエストから）
- リクエストのネストと進行中のライトバック（L2から下位へのTileLink ReleaseまたはCHI Copy-Back Write）

このすべての情報は、割り当てられたMSHRエントリ内に登録されます。

### 解放

MSHR内のすべてのステートマシンエントリが完了としてマークされると、その場で直ちに解放され、そのMSHRエントリのライフサイクルが終了し、MSHRSelectorによって再度選択および割り当てられる準備が整います。MSHRステートマシンエントリの詳細については、[@sec:mshr-state-machine] [ステートマシン](#sec:mshr-state-machine)を参照してください。


## ステートマシン {#sec:mshr-state-machine}

ステートマシンエントリは、主に2つのカテゴリに分類されます。

- スケジュール状態エントリ
- 待機状態アイテム

スケジュール状態アイテムは、アクティブアクション状態アイテムとも呼ばれ、主にMSHRがMainPipe、下流のCHIチャネル、および上流のTileLinkチャネルにタスクとリクエストをアクティブに送信するのを追跡するために使用されます。その値はアクティブローであり、タスクがまだMSHRを正常に離れて発行されておらず、ブロッキング条件（必要な前提条件が完了していない）またはチャネルブロッキングが原因である可能性がある不完全な状態を示します。ハイの値は、対応するタスクが正常に発行されたか、発行する必要がないことを示します。

待機状態エントリは、パッシブアクション状態エントリとも呼ばれ、主にMSHRが下流のCHIチャネル、上流のTileLinkチャネル、または内部のCoupledL2モジュールから期待する応答を追跡するために使用されます。その値はアクティブローであり、対応する応答がまだMSHRエントリに戻っていない不完全な状態を示します。ハイの値は、対応する応答が受信されたか、不要であることを示します。

ステータスエントリは、MSHRがMainPipeによって割り当てられたときに割り当てられ、内部のMSHRアクションによって変更することもできます。

> このセクションの上流は通常L1キャッシュを指し、下流は通常NoC、LLCなどを指します。

スケジュール状態アイテムはプレフィックスとして```s_```で命名され、その概要は次のとおりです。

| 名前             | 説明                                                                                                                |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------- |
| ```s_acquire```  | 初めて下流に権限昇格要求またはCMO要求を送信する必要がある場合、または再試行された書き戻しまたは追い出し要求を下流に送信する必要がある場合。                                                                              |
| ```s_rprobe```   | 置換またはライトバックのため、プローブ要求を上流に送信する必要がある。                                                 |
| ```s_pprobe```   | 下流のスヌープ要求のため、プローブ要求を上流に送信する必要がある。                                              |
| ```s_release```  | 下流に送信する必要があるライトバックまたは追い出し要求。                                                             |
| ```s_probeack``` | 下流のスヌープ要求のため、スヌープ応答を下流に送信する必要がある。                                             |
| ```s_refill```   | 上流にGrant応答を送信する必要がある。                                                                                     |
| ```s_retry```    | 置換に利用可能なウェイがないため、上流に送信されたGrant応答を再試行する必要がある。                              |
| ```s_cmoresp```  | 上流にCBOAck応答を送信する必要がある。                                                                                    |
| ```s_cmometaw``` | CMOによって引き起こされたMainPipeに送信されるディレクトリ更新要求。                                                                   |
| ```s_rcompack``` | 下流に読み取り要求を送信したため、対応するCompAck応答を送信する必要がある。                                                                                             |
| ```s_wcompack``` | 下流に書き込み要求を送信したため、対応するCompAck応答を送信する必要がある。                              |
| ```s_cbwrdata``` | 下流に書き込み要求を送信したため、対応するCopyBackWrDataを送信してデータを書き戻す必要がある。           |
| ```s_reissue```  | 下流からRetryAckを受信し、MSHRがPCreditを取得したため、要求を下流に再送信する必要がある。 |
| ```s_dct```      | 下流のフォワーディングスヌープ要求のため、他のRNにデータを提供するためにDCTの形式でCompDataを送信する必要がある。    |

待機状態エントリはプレフィックスとして```w_```で命名され、その概要は次のとおりです。

| 名前                   | 説明                                                                                                                                                                                                                                        |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ```w_rprobeackfirst``` | 置換またはライトバックのため、プローブ要求を上流に送信し、上流からの最初のプローブ応答を待つ必要がある。                                                                                                                   |
| ```w_rprobeacklast```  | 置換またはライトバックのため、プローブ要求を上流に送信し、上流からの最後のプローブ応答を待つ必要がある（単一の応答の場合、アクションは```w_rprobeackfirst```と同じ）。                                      |
| ```w_pprobeackfirst``` | 下流のスヌープ要求のため、プローブ要求を上流に送信し、上流からの最初のプローブ応答を待つ必要がある。                                                                                                                 |
| ```w_pprobeacklast```  | 下流のスヌープ要求のため、プローブ要求を上流に送信し、上流からの最後のプローブ応答を待つ必要がある（単一の応答の場合、アクションは```w_pprobeackfirst```と同じ）。                             |
| ```w_grantfirst```     | 下流に権限昇格要求またはCMO要求を送信したため、下流からの最初のComp、CompData、またはDataSepResp応答を待つ必要がある。                                                                              |
| ```w_grantlast```      | 下流に権限昇格要求またはCMO要求を送信したため、下流からの最後のCompDataまたはDataSepResp応答を待つ必要がある（Comp応答を受信した場合、アクションは```w_grantfirst```と同じ）。   |
| ```w_grant```          | 下流に権限昇格要求またはCMO要求を送信したため、下流のComp、CompData、またはRespSepData応答を待機し、CompDataおよびRespSepData応答から必要なDBIDおよびSrcID情報を取得する必要がある。 |
| ```w_releaseack```     | 下流に送信されたライトバックまたは追い出し要求のため、下流からのCompまたはCompDBIDResp応答を待機する。                                                                                                                              |
| ```w_replResp```       | 置換のため、ディレクトリからの置換選択結果を待機する。                                                                                                                                                                    |


## タスクディスパッチ

スケジュール状態エントリが不完全な場合、MSHRは対応するタスクを関連モジュールまたはチャネルに送信しようとします。各MSHRエントリは、MSHRCtlアービトレーションを介して、次のモジュールまたはチャネルに直接タスクを分配できます。

- MainPipe
- 上流TileLink Bチャネル
- 下流TXREQチャネル
- 下流TXRSPチャネル

TXDATチャネルタスクの分配については、MainPipeを通過する必要があります。詳細は[@sec:reqarb-mainpipe] [リクエストアービタとメモリパイプライン](ReqArb_MainPipe.md)を参照してください。

MainPipeに送信されるタスクも、同じサイクルでRequestArbによるアービトレーションを受けます。詳細は[@sec:reqarb-mainpipe] [リクエストアービタとメモリパイプライン](ReqArb_MainPipe.md)を参照してください。

各スケジュール状態項目に対応するタスク分配方向は次のとおりです。

| 名前             | ターゲットモジュール/チャネル       |
| ---------------- | --------------------------- |
| ```s_acquire```  | 下流TXREQチャネル    |
| ```s_rprobe```   | 上流TileLink Bチャネル |
| ```s_pprobe```   | 上流TileLink Bチャネル |
| ```s_release```  | MainPipe                    |
| ```s_probeack``` | MainPipe                    |
| ```s_refill```   | MainPipe                    |
| ```s_retry```    | -                           |
| ```s_cmoresp```  | MainPipe                    |
| ```s_cmometaw``` | MainPipe                    |
| ```s_rcompack``` | 下流TXRSPチャネル    |
| ```s_wcompack``` | 下流TXRSPチャネル    |
| ```s_cbwrdata``` | MainPipe                    |
| ```s_reissue```  | -                           |
| ```s_dct```      | MainPipe                    |

### MainPipe

各MSHRは、そのステートマシンエントリの状態に基づいて、いくつかの異なるタイプのタスクをMainPipeに送信します。

#### ライトバック要求タスク (```mp_release```)

ライトバック要求タスク（```mp_release```）は、ステートマシンエントリ```s_release```によってトリガーされます。このタスクの目的は、MainPipeのTXREQチャネルを介して、必要なキャッシュラインのライトバックまたは追い出し要求を送信することです。ステートマシンエントリ```s_release```が不完全で、現在のMSHR状態が特定の条件を満たす場合、MSHRはライトバック要求タスクをMainPipeに送信しようとします。

```s_release```が不完全とマークされている場合、MSHRの状態は、MainPipeにライトバック要求タスクを送信する前に、すべてのシナリオで次の条件を満たす必要があります。

1. 置換タスクから
    - 置換ウェイの選択が完了している
    - 上流プローブへのすべての応答が受信されている
    - 置換読み取り要求が下流からすべてのデータを受信している
2. CMO要求から
    - 上流プローブへのすべての応答が受信されている

ライトバック要求タスクは、MainPipeがTXREQチャネルで要求を送信することを要求します。

| タスクソース      | 上流Aチャネル要求タイプ | ダーティデータあり | 下流TXREQ要求タイプ |
| ---------------- | ------------------------------- | --------------------------- | ----------------------------- |
| 置換タスク | Acquire*                        | はい                         | WriteBackFull                 |
|                  |                                 | いいえ                          | WriteEvictOrEvict             |
| CMO要求      | CBOClean                        | -                           | WriteCleanFull                |
|                  | CBOFlush                        | はい                         | WriteBackFull                 |
|                  |                                 | いいえ                          | Evict                         |
|                  | CBOInval                        | -                           | Evict                         |

ライトバック要求タスクは、状況に応じて、MSHRが保持する関連データをMainPipeがDataStorageに書き込むことを要求します。

| タスクソース      | 上流Aチャネル要求タイプ | ダーティデータあり | データソース   | DataStorageへの書き込み要否 |
| ---------------- | ------------------------------- | --------------------------- | ------------- | ------------------------------- |
| 置換タスク | Acquire*                        | -                           | RefillBuffer  | はい                             |
| CMO要求      | CBO*                            | 上流からのプローブ         | ReleaseBuffer | はい                             |
|                  |                                 | その他                      | -             | いいえ                              |

さらに、ライトバック要求タスクのCMO要求は、MainPipeがディレクトリ内のキャッシュライン状態を更新し、キャッシュラインのダーティフラグをクリアすることを要求します。

| タスクソース | 上流Aチャネル要求タイプ | 初期状態 | 書き込み状態 |
| ----------- | ------------------------------- | ------------- | ------------ |
| CMO要求 | CBOClean                        | TRUNK         | TIP          |
|             |                                 | TIP           | TIP          |
|             |                                 | BRANCH        | BRANCH       |
|             |                                 | INVALID       | INVALID      |
|             | CBOFlush                        | -             | INVALID      |
|             | CBOInval                        | -             | INVALID      |

#### 下流スヌープ応答タスク (```mp_probeack```)

下流スヌープ応答タスク（```mp_probeack```）は、ステートマシンエントリ```s_probeack```によってトリガーされます。このタスクは、MainPipeのTXRSPまたはTXDATチャネルを介して下流スヌープ応答を送信する役割を果たします。ステートマシンエントリ```s_probeack```の状態が不完全で、現在のMSHR状態が特定の条件を満たす場合、MSHRは下流スヌープ応答タスクをMainPipeに送信しようとします。

```s_probeack```が不完全とマークされている場合、そのMSHR状態は、下流スヌープ応答タスクをMainPipeに送信する前に、次の条件を満たす必要があります。

- 上流プローブへのすべての応答が受信されている

下流スヌープ応答タスクは、MainPipeがTXRSPまたはTXDATチャネルでメッセージを送信し、MSHRでスヌープ応答タイプを指定することを要求します。詳細については、[@sec:mshr-snoop-details] [スヌープ処理](#sec:mshr-snoop-details)を参照してください。

下流スヌープ応答タスクは、以下の条件を満たす場合に、MainPipeがMSHRの保持する関連データをDataStorageに書き込むことを要求します。

- 下流スヌープ要求のターゲット状態がIではない。
- 上流L1がプローブ中にダーティデータを返した（ProbeAckData）。
- 上流L1がプローブ終了前にネストされたダーティデータライトバック（ReleaseData）を開始しない。

下流スヌープ応答タスクは、MainPipeがキャッシュラインの状態を更新することを要求します。詳細については、[@sec:mshr-snoop-details] [スヌープ処理](#sec:mshr-snoop-details)を参照してください。

#### 置換ウェイ問い合わせと上流Grant/CBOAck応答タスク (```mp_grant```)

置換ウェイ問い合わせと上流Grant/CBOAck応答タスク（```mp_grant```）は、ステートマシンエントリ```s_refill```または```s_cmoresp```によってトリガーされ、```s_refill```と```s_cmoresp```は同時に不完全としてマークすることはできません。このタスクの目的は、次のいずれかです。

1. MainPipeがディレクトリに置換ウェイ問い合わせ要求を開始するとき
2. MainPipeがTileLink Dチャネルを介して上流にGrant/GrantDataで応答するとき
3. MainPipeがTileLink Dチャネルを介して上流にCBOAckで応答するとき

ステートマシン項目```s_release```が不完全で、現在のMSHR状態が特定の条件を満たす場合、MSHRは置換ウェイ問い合わせまたは上流Grant応答タスクをMainPipeに送信しようとします。ステートマシン項目```s_cmoresp```が不完全で、現在のMSHR状態が特定の条件を満たす場合、MSHRはCBOAck応答タスクをMainPipeに送信しようとします。

```s_refill```が不完全とマークされている場合、MSHRの状態は、置換ウェイ問い合わせと上流Grant応答タスクをMainPipeに送信する前に、次の条件を満たす必要があります。

- 上流プローブへのすべての応答が受信されている
- 下流からの最初のComp、CompData、またはRespSepData応答が受信されている
- 必要に応じて、下流からすべてのComp、CompData、またはDataSepResp応答を受信する。
- 置換ウェイ問い合わせの再試行が再試行抑制しきい値を超えていない

置換ウェイ再試行要求を複数回連続して送信した後、MSHRは過度に密で連続した再試行によるライブロックを防ぐために、一定期間それらを抑制します。

```s_cmoresp```が不完全とマークされている場合、MSHRの状態は、MainPipeに置換ウェイ問い合わせを送信し、上流CBOAck応答タスクを送信するために、次の条件を満たす必要があります。

- 上流プローブへのすべての応答が受信されている
- ```w_releaseack```に属するComp応答が下流から受信されている
- ```w_grant```に属する下流からのComp応答が受信されている（```w_grant```は```w_releaseack```が完了した後にのみ下流のComp応答を受信できる）。
- 必要に応じて、すべてのCopyBackWrDataが送信されている。

さらに、これらの条件は、CBOAck応答プロセスを除くすべてのCMOサブアクションが完了した後にのみ、```s_cmoresp```がタスクを開始できるという機能を示唆しています。

MSHRが置換ウェイの結果を待つ必要があり、ディレクトリが再試行応答を与えた場合、MSHRは```mp_grant```から置換ウェイ再試行タスクを送信します。

置換ウェイ問い合わせと上流Grantタスクは、MainPipeがディレクトリ内のキャッシュライン状態を更新することを要求しますが、上流CBOAckタスクはそのような更新を要求しません。更新ルールは次のとおりです。

| タスクソース     | 要求タイプ       | 初期状態 | 更新状態 |
| --------------- | ------------------ | ------------- | ------------ |
| ```s_refill```  | Get                | TIP           | TIP          |
|                 |                    | TRUNK         | TIP          |
|                 |                    | BRANCH        | BRANCH       |
|                 |                    | INVALID       | TIP```*```   |
|                 |                    |               | BRANCH       |
|                 | Acquire* toT       | -             | TRUNK        |
|                 | Acquire* toB       | -             | TRUNK```*``` |
|                 |                    | -             | BRANCH       |
|                 | Hint PrefetchWrite | -             | TIP          |
|                 | Hint PrefetchRead  | -             | TIP```*```   |
|                 |                    | -             | BRANCH       |
| ```s_cmoresp``` | -                  | -             | -            |

以下の更新は特定の条件下で発生します：GetはTIPに更新、Acquire* toBはTRUNKに更新、Hint PrefetchReadはTIPに更新

- キャッシュラインが上流L1に存在せず、L2ローカルでTIP権限を持っている
- キャッシュラインで実行されている操作がエイリアス置換ではなく、L2ローカル権限がTIPまたはTRUNKのいずれかである
- キャッシュラインがL2に存在せず、下流に送信された読み取り要求が書き込み権限を返す

置換ウェイ問い合わせと上流Grantタスクがディレクトリでミスした場合、MainPipeにディレクトリで置換対象として選択されたキャッシュラインの対応するタグ値を提供するよう要求します。ただし、これは上流CBOAckタスクには必要ありません。

置換ウェイ問い合わせと上流Grant/CBOAckタスクは、以下の条件のいずれかが満たされた場合に、MainPipeがMSHRの保持する関連データをDataStorageに書き込むことを要求します。

- 下流からCompDataまたはDataSepRespデータ応答を受信した
- Getまたはエイリアス置換プロセスの完了時に上流に送信されたプローブでダーティデータが受信された

#### 下流CopyBackWrDataタスク (```mp_cbwrdata```)

ライトバック要求タスク（```mp_cbwrdata```）は、ステートマシン項目```s_cbwrdata```によってトリガーされます。このタスクの目的は、MainPipeのTXDATチャネルを介して下流に送信する必要があるCopyBackWrDataを完了することです。ステートマシン項目```s_cbwrdata```が完了しておらず、現在のMSHR状態が特定の条件を満たす場合、MSHRはライトバック要求タスクをMainPipeに送信しようとします。

```s_cbwrdata```は通常、```s_release```と```w_releaseack```の次のアクションによって不完全として設定されます。

- ライトバック要求タスクがMSHRを離れているとき、つまり```s_release```状態エントリが完了としてマークされているとき。

WriteEvictOrEvictを送信した後にComp応答を受信した場合、MSHRが下流にCopyBackWrDataタスクを送信することなく、```s_cbwrdata```は```s_cbwrdata```を完了としてマークすることに注意してください。

MSHRの状態は、MainPipeにライトバック要求タスクを送信するために、次の条件を満たす必要があります。

- ライトバック要求タスクがMSHRを離れている、つまり```s_release```ステータスエントリが完了している。

#### 下流DCT CompDataタスク (```mp_dct```)

下流DCT CompDataタスク（```mp_dct```）は、ステートマシンエントリ```s_dct```によってトリガーされます。このタスクは、TXDATチャネルを介してMainPipeのフォワーディングスヌープのDCT部分を完了します。ステートマシンエントリ```s_dct```が不完全で、現在のMSHR状態が特定の条件を満たす場合、MSHRは下流DCT CompDataタスクをMainPipeに送信しようとします。

```s_dct```が不完全とマークされている場合、そのMSHR状態は、下流DCT CompDataタスクをMainPipeに送信する前に、次の条件を満たす必要があります。

- フォワーディングスヌーププロセスにおいて、HNをターゲットとするスヌープ応答タスクがMSHRを離れている、つまり```s_probeack```ステータスエントリが完了している。

下流DCT CompDataタスクは、MainPipeがTXDATチャネルを介してCompData応答を送信することを要求します。DCTの定義によれば、このCompData応答のターゲットは別のプロセッサコア（つまりRN）です。

#### CMOキャッシュ状態更新タスク (```mp_cmometaw```)

CMOキャッシュ状態更新タスク（```mp_cmometaw```）は、ステートマシンエントリ```s_cmometaw```によってトリガーされます。このタスクは、CBOClean操作にWriteCleanFullライトバックが必要ない場合に、MainPipeのキャッシュライン状態を更新します。

```s_cmometaw```が不完全と設定されている場合、MSHRはCMOキャッシュ状態更新タスクをMainPipeに送信し、次の更新を実行できます。

- ProbeAck toNを受信した場合、レコードを更新してキャッシュラインが上流L1に存在しないことを示す
- 状態をクリーンにクリア
- 権限をTIPに更新

### 上流TileLink Bチャネル

上流TileLink Bチャネルへの要求送信は、ステートマシン項目```s_pprobe```または```s_rprobe```によってトリガーされます。さらに、```s_pprobe```と```s_rprobe```は同時に不完全として設定されることはありません。

```s_pprobe```または```s_rprobe```のいずれかが不完全として設定されている場合、MSHRは上流TileLink Bチャネルに要求を送信できます。各シナリオの要求タイプを以下の表に示します。

| タスクソース    | 上流要求タイプ | 下流要求タイプ | キャッシュライン状態 | 送信要求タイプ |
| -------------- | --------------------- | ----------------------- | ---------------- | ----------------- |
| ```s_pprobe``` | -                     | SnpOnce                 | -                | Probe toT         |
|                | -                     | SnpClean                | -                | Probe toB         |
|                | -                     | SnpShared               | -                | Probe toB         |
|                | -                     | SnpNotSharedDirty       | -                | Probe toB         |
|                | -                     | SnpUnique               | -                | Probe toN         |
|                | -                     | SnpCleanShared          | -                | Probe toT         |
|                | -                     | SnpCleanInvalid         | -                | Probe toN         |
|                | -                     | SnpMakeInvalid          | -                | Probe toN         |
|                | -                     | SnpMakeInvalidStash     | -                | Probe toN         |
|                | -                     | SnpUniqueStash          | -                | Probe toN         |
|                | -                     | SnpStashUnique          | -                | Probe toT         |
|                | -                     | SnpStashShared          | -                | Probe toT         |
|                | -                     | SnpOnceFwd              | -                | Probe toT         |
|                | -                     | SnpCleanFwd             | -                | Probe toB         |
|                | -                     | SnpNotSharedDirtyFwd    | -                | Probe toB         |
|                | -                     | SnpSharedFwd            | -                | Probe toB         |
|                | -                     | SnpUniqueFwd            | -                | Probe toN         |
|                | -                     | SnpQuery                | -                | Probe toT         |
| ```s_rprobe``` | Get                   | -                       | TRUNK            | Probe toB         |
|                | Acquire*              | -                       | -                | Probe toN         |
|                | CBOClean              | -                       | TRUNK            | Probe toB         |

### 下流TXREQチャネル

下流TXREQチャネルに送信される要求は、ステートマシンエントリ```s_acquire```または```s_reissue```によってトリガーされます。さらに、```s_acquire```と```s_reissue```は同時に不完全としてマークされることはありません。

```s_acquire```が不完全とマークされている場合、置換タスクについては、権限昇格要求を直ちに下流に送信できます。ただし、CMOタスクについては、CMO要求を下流に送信する前に、次の条件を満たす必要があります。

- 上流プローブへのすべての応答が受信されている
- 下流ライトバック要求がCompまたはCompDBIDRespを受信している
- 下流へのCopyBackWrDataタスクがMSHRを離れているか、不要である

```s_reissue```が保留中として設定されている場合、再試行された要求を下流に再送信する前に、次の条件を満たす必要があります。

- RetryAckが下流から受信されている
- PCrdGrantが下流から受信され、割り当てられている
- ```mp_release```または下流TXREQチャネルタスクがMSHRを離れたが、まだ応答を受信していない状態にある、つまり、```s_release```ステータスエントリは完了しているが```w_releaseack```ステータスエントリは完了していない、または```s_acquire```ステータスエントリは完了しているが```w_grant```ステータスエントリは完了していない

さまざまな条件下でTXREQチャネルで下流に送信される要求タイプは次のとおりです。

| タスクソース     | 不完全な状態   | 上流要求タイプ | 未解決の要求タイプ | 送信要求タイプ  |
| --------------- | ------------------ | --------------------- | ------------------------ | ------------------ |
| ```s_acquire``` | -                  | Get                   | -                        | ReadNotSharedDirty |
|                 |                    | AcquirePerm toT       | -                        | MakeUnique         |
|                 |                    | AcquireBlock toT      | -                        | ReadUnique         |
|                 |                    | AcquireBlock toB      | -                        | ReadNotSharedDirty |
|                 |                    | Hint PrefetchWrite    | -                        | ReadUnique         |
|                 |                    | Hint PrefetchRead     | -                        | ReadNotSharedDirty |
|                 |                    | CBOClean              | -                        | CleanShared        |
|                 |                    | CBOFlush              | -                        | CleanInvalid       |
|                 |                    | CBOInval              | -                        | MakeInvalid        |
| ```s_reissue``` | ```w_grant```      | Get                   | ReadNotSharedDirty       | ReadNotSharedDirty |
|                 |                    | AcquirePerm toT       | MakeUnique               | MakeUnique         |
|                 |                    | AcquireBlock toT      | ReadUnique               | ReadUnique         |
|                 |                    | AcquireBlock toB      | ReadNotSharedDirty       | ReadNotSharedDirty |
|                 |                    | Hint PrefetchWrite    | ReadUnique               | ReadUnique         |
|                 |                    | Hint PrefetchRead     | ReadNotSharedDirty       | ReadNotSharedDirty |
|                 |                    | CBOClean              | CleanShared              | CleanShared        |
|                 |                    | CBOFlush              | CleanInvalid             | CleanInvalid       |
|                 |                    | CBOInval              | MakeInvalid              | MakeInvalid        |
| ```s_reissue``` | ```w_releaseack``` | Acquire*              | WriteBackFull            | WriteBackFull      |
|                 |                    |                       | WriteEvictOrEvict        | WriteEvictOrEvict  |
|                 |                    | CBOClean              | WriteCleanFull           | WriteCleanFull     |
|                 |                    | CBOFlush              | WriteBackFull            | WriteBackFull      |
|                 |                    |                       | Evict                    | Evict              |
|                 |                    | CBOInval              | Evict                    | Evict              |

### 下流TXRSPチャネル

下流TXRSPチャネルへのメッセージ送信は、ステートマシン項目```s_rcompack```または```s_wcompack```によってトリガーされます。このチャネルは、主にCompAckメッセージを下流に送信するために使用されます。その中で、```s_rcompack```と```s_wcompack```は同時に不完全として設定される可能性があり、```s_rcompack```の方が優先度が高くなります。

```s_rcompack```が不完全とマークされている場合、CompAckメッセージを下流に送信するには、次の条件を満たす必要があります。

1. Issue Bとして構成されている場合
    - 下流のCompまたはすべてのCompDataを受信する
2. Issue C以降のバージョンとして構成されている場合
    - 下流のCompまたは最初のCompDataまたはRespSepDataと最初のDataSepRespを受信する

```s_wcompack```が不完全として設定されている場合、CompAckメッセージを下流に送信する前に、次の条件を満たす必要があります。

- ```s_rcompack```が完了しているか、不完全としてマークされていない

## スヌープ処理 {#sec:mshr-snoop-details}

### 非ネストスヌープ

同じアドレスに対する保留中のライトバック要求がない場合、受信したスヌープは非ネストの通常のスヌープであり、スヌープ処理の最も基本的なケースを表します。MSHRでの非ネストスヌープの処理方法は次のとおりです。

| スヌープ要求タイプ    | 初期状態 | 最終状態 | RetToSrc | スヌープ応答                |
| --------------------- | ------------- | ----------- | -------- | -------------------------- |
| SnpOnce               | I             | -           | -        | -                          |
|                       | UC            | UC          | X        | SnpRespData_UC             |
|                       | UD            | UD          | X        | SnpRespData_UD_PD          |
|                       | SC.           | -           | -        | -                          |
| SnpClean,             | I             | -           | -        | -                          |
| SnpShared,            | UC            | SC.         | X        | SnpResp_SC                 |
| SnpNotSharedDirty     | UD            | SC.         | X        | SnpRespData_SC_PD          |
|                       | SC.           | -           | -        | -                          |
| SnpUnique             | I             | -           | -        | -                          |
|                       | UC            | I           | X        | SnpResp_I                  |
|                       | UD            | I           | X        | SnpRespData_I_PD           |
|                       | SC.           | I           | 0        | SnpResp_I                  |
|                       |               |             | 1        | SnpRespData_I              |
| SnpCleanShared        | I             | -           | -        | -                          |
|                       | UC            | UC          | 0        | SnpResp_UC                 |
|                       | UD            | UC          | 0        | SnpRespData_UC_PD          |
|                       | SC.           | -           | -        | -                          |
| SnpCleanInvalid       | I             | -           | -        | -                          |
|                       | UC            | I           | 0        | SnpResp_I                  |
|                       | UD            | I           | 0        | SnpRespData_I_PD           |
|                       | SC.           | I           | 0        | SnpResp_I                  |
| SnpMakeInvalid        | -             | I           | 0        | SnpResp_I                  |
| SnpMakeInvalidStash   | -             | I           | 0        | SnpResp_I                  |
| SnpUniqueStash        | I             | -           | -        | -                          |
|                       | UC            | I           | 0        | SnpResp_I                  |
|                       | UD            | I           | 0        | SnpRespData_I_PD           |
|                       | SC.           | I           | 0        | SnpResp_I                  |
| SnpStashUnique,       | I             | -           | -        | -                          |
| SnpStashShared        | UC            | UC          | 0        | SnpResp_UC                 |
|                       | UD            | UD          | 0        | SnpResp_UD                 |
|                       | SC.           | -           | -        | -                          |
| SnpOnceFwd            | I             | I           | 0        | SnpResp_I                  |
|                       | UC            | UC          | 0        | SnpResp_UC_Fwded_I         |
|                       | UD            | UD          | 0        | SnpResp_UD_Fwded_I         |
|                       | SC.           | SC.         | 0        | SnpResp_SC_Fwded_I         |
| SnpCleanFwd,          | I             | I           | X        | SnpResp_I                  |
| SnpNotSharedDirtyFwd, | UC            | SC.         | 0        | SnpResp_SC_Fwded_SC        |
| SnpSharedFwd          |               |             | 1        | SnpRespData_SC_Fwded_SC    |
|                       | UD            | SC.         | X        | SnpRespData_SC_PD_Fwded_SC |
|                       | SC.           | SC.         | 0        | SnpResp_SC_Fwded_SC        |
|                       |               |             | 1        | SnpRespData_SC_Fwded_SC    |
| SnpUniqueFwd          | I             | I           | 0        | SnpResp_I                  |
|                       | UC            | I           | 0        | SnpResp_I_Fwded_UC         |
|                       | UD            | I           | 0        | SnpResp_I_Fwded_UD_PD      |
|                       | SC.           | I           | 0        | SnpResp_I_Fwded_UC         |
| SnpQuery              | I             | -           | -        | -                          |
|                       | UC            | UC          | 0        | SnpResp_UC                 |
|                       | UD            | UD          | 0        | SnpResp_UD                 |
|                       | SC.           | -           | -        | -                          |

> 「-」およびリストにないキャッシュ状態は、そのような要求が対応する条件下でMSHRに入らないことを示します。

特定のスヌープ要求がいつMSHRを割り当てるかの詳細については、[@sec:reqarb-mainpipe] [リクエストアービタとメモリパイプライン](ReqArb_MainPipe.md)を参照してください。


### ネストされたスヌープ

MSHRが下流のライトバック要求を処理している間も、CoupledL2が下流のスヌープ要求と上流のリリース要求に応答できることを保証する必要があります。この場合、不完全なライトバック要求は、スヌープ要求によってネストされているか、上流のリリース要求によってネストされていると見なされます。CHIプロトコルのサイレントエビクションとEvict要求の初期状態がIであるため、データライトバックを伴わない追い出し要求（Evict）はネストされているとは見なされないことに注意してください。

> 「-」およびリストにないキャッシュ状態は、対応する条件下でのそのような要求がMSHRに入らないか、ネストシナリオの範囲外であることを示します。

特定のスヌープ要求がいつMSHRを割り当てるかの詳細については、[@sec:reqarb-mainpipe] [リクエストアービタとメモリパイプライン](ReqArb_MainPipe.md)を参照してください。

以下のネストされた下流スヌープ要求が発生し、MSHR内で処理される場合があります。

#### 特徴1：スヌープとWriteBackFullのネスト

| スヌープ要求タイプ   | 初期状態 | ネスト前状態 | ネスト後状態 | RetToSrc | スヌープ応答               |
| -------------------- | ------------- | ----------------- | ------------------ | -------- | ------------------------- |
| SnpOnce              | -             | -                 | -                  | -        | -                         |
| SnpClean             | -             | -                 | -                  | -        | -                         |
| SnpShared            | -             | -                 | -                  | -        | -                         |
| SnpNotSharedDirty    | -             | -                 | -                  | -        | -                         |
| SnpCleanShared       | -             | -                 | -                  | -        | -                         |
| SnpCleanInvalid      | -             | -                 | -                  | -        | -                         |
| SnpMakeInvalid       | -             | -                 | -                  | -        | -                         |
| SnpUnique            | -             | -                 | -                  | -        | -                         |
| SnpUniqueStash       | -             | -                 | -                  | -        | -                         |
| SnpMakeInvalidStash  | -             | -                 | -                  | -        | -                         |
| SnpStashUnique       | -             | -                 | -                  | -        | -                         |
| SnpStashShared       | -             | -                 | -                  | -        | -                         |
| SnpOnceFwd           | UD            | UD                | I                  | X        | SnpRespData_I_PD_Fwded_I  |
| SnpCleanFwd          | UD            | UD                | I                  | X        | SnpRespData_I_PD_Fwded_SC |
| SnpSharedFwd         | UD            | UD                | I                  | X        | SnpRespData_I_PD_Fwded_SC |
| SnpNotSharedDirtyFwd | UD            | UD                | I                  | X        | SnpRespData_I_PD_Fwded_SC |
| SnpUniqueFwd         | UD            | UD                | I                  | X        | SnpResp_I_Fwded_UD_PD     |
| SnpQuery             | -             | -                 | -                  | -        | -                         |

#### 特徴2：スヌープとWriteEvictOrEvictのネスト

| スヌープ要求タイプ   | 初期状態 | ネスト前状態 | ネスト後状態 | RetToSrc | スヌープ応答            |
| -------------------- | ------------- | ----------------- | ------------------ | -------- | ---------------------- |
| SnpOnce              | -             | -                 | -                  | -        | -                      |
| SnpClean             | -             | -                 | -                  | -        | -                      |
| SnpShared            | -             | -                 | -                  | -        | -                      |
| SnpNotSharedDirty    | -             | -                 | -                  | -        | -                      |
| SnpCleanShared       | -             | -                 | -                  | -        | -                      |
| SnpCleanInvalid      | -             | -                 | -                  | -        | -                      |
| SnpMakeInvalid       | -             | -                 | -                  | -        | -                      |
| SnpUnique            | -             | -                 | -                  | -        | -                      |
| SnpUniqueStash       | -             | -                 | -                  | -        | -                      |
| SnpMakeInvalidStash  | -             | -                 | -                  | -        | -                      |
| SnpStashUnique       | -             | -                 | -                  | -        | -                      |
| SnpStashShared       | -             | -                 | -                  | -        | -                      |
| SnpOnceFwd           | UC            | UC                | I                  | X        | SnpRespData_I_Fwded_I  |
| SnpCleanFwd          | UC            | UC                | I                  | 0        | SnpResp_I_Fwded_SC     |
|                      |               |                   |                    | 1        | SnpRespData_I_Fwded_SC |
| SnpSharedFwd         | UC            | UC                | I                  | 0        | SnpResp_I_Fwded_SC     |
|                      |               |                   |                    | 1        | SnpRespData_I_Fwded_SC |
| SnpNotSharedDirtyFwd | UC            | UC                | I                  | 0        | SnpResp_I_Fwded_SC     |
|                      |               |                   |                    | 1        | SnpRespData_I_Fwded_SC |
| SnpUniqueFwd         | UC            | UC                | I                  | 0        | SnpResp_I_Fwded_UC     |
| SnpQuery             | -             | -                 | -                  | -        | -                      |

#### 特徴3：スヌープとWriteCleanFullのネスト

| スヌープ要求タイプ   | 初期状態 | ネスト前状態 | ネスト後状態 | RetToSrc | スヌープ応答                |
| -------------------- | ------------- | ----------------- | ------------------ | -------- | -------------------------- |
| SnpOnce              | -             | -                 | -                  | -        | -                          |
| SnpClean             | -             | -                 | -                  | -        | -                          |
| SnpShared            | -             | -                 | -                  | -        | -                          |
| SnpNotSharedDirty    | -             | -                 | -                  | -        | -                          |
| SnpCleanShared       | -             | -                 | -                  | -        | -                          |
| SnpCleanInvalid      | UD            | UD                | I                  | 0        | SnpRespData_I_PD           |
|                      |               | UC                | I                  | 0        | SnpResp_I                  |
|                      |               | SC.               | I                  | 0        | SnpResp_I                  |
| SnpMakeInvalid       | UD            | UD                | I                  | 0        | SnpResp_I                  |
|                      |               | UC                | I                  | 0        | SnpResp_I                  |
|                      |               | SC.               | I                  | 0        | SnpResp_I                  |
| SnpUnique            | UD            | UD                | I                  | X        | SnpRespData_I_PD           |
|                      |               | UC                | I                  | X        | SnpResp_I                  |
|                      |               | SC.               | I                  | 0        | SnpResp_I                  |
|                      |               |                   |                    | 1        | SnpRespData_I              |
| SnpUniqueStash       | UD            | UD                | I                  | 0        | SnpRespData_I_PD           |
|                      |               | UC                | I                  | 0        | SnpResp_I                  |
|                      |               | SC.               | I                  | 0        | SnpResp_I                  |
| SnpMakeInvalidStash  | UD            | UD                | I                  | 0        | SnpResp_I                  |
|                      |               | UC                | I                  | 0        | SnpResp_I                  |
|                      |               | SC.               | I                  | 0        | SnpResp_I                  |
| SnpStashUnique       | -             | -                 | -                  | -        | -                          |
| SnpStashShared       | -             | -                 | -                  | -        | -                          |
| SnpOnceFwd           | UD            | UD                | SC.                | 0        | SnpRespData_SC_PD_Fwded_I  |
|                      |               | UC                | UC                 | 0        | SnpResp_UC_Fwded_I         |
|                      |               | SC.               | SC.                | 0        | SnpResp_SC_Fwded_I         |
| SnpCleanFwd          | UD            | UD                | SC.                | X        | SnpRespData_SC_PD_Fwded_SC |
|                      |               | UC                | SC.                | 0        | SnpResp_SC_Fwded_SC        |
|                      |               |                   |                    | 1        | SnpRespData_SC_Fwded_SC    |
|                      |               | SC.               | SC.                | 0        | SnpResp_SC_Fwded_SC        |
|                      |               |                   |                    | 1        | SnpRespData_SC_Fwded_SC    |
| SnpSharedFwd         | UD            | UD                | SC.                | X        | SnpRespData_SC_PD_Fwded_SC |
|                      |               | UC                | SC.                | 0        | SnpResp_SC_Fwded_SC        |
|                      |               |                   |                    | 1        | SnpRespData_SC_Fwded_SC    |
|                      |               | SC.               | SC.                | 0        | SnpResp_SC_Fwded_SC        |
|                      |               |                   |                    | 1        | SnpRespData_SC_Fwded_SC    |
| SnpNotSharedDirtyFwd | UD            | UD                | SC.                | X        | SnpRespData_SC_PD_Fwded_SC |
|                      |               | UC                | SC.                | 0        | SnpResp_SC_Fwded_SC        |
|                      |               |                   |                    | 1        | SnpRespData_SC_Fwded_SC    |
|                      |               | SC.               | SC.                | 0        | SnpResp_SC_Fwded_SC        |
|                      |               |                   |                    | 1        | SnpRespData_SC_Fwded_SC    |
| SnpUniqueFwd         | UD            | UD                | I                  | 0        | SnpResp_I_Fwded_UD_PD      |
|                      |               | UC                | I                  | 0        | SnpResp_I_Fwded_UC         |
|                      |               | SC.               | I                  | 0        | SnpResp_I_Fwded_UC         |
| SnpQuery             | -             | -                 | -                  | -        | -                          |


## ライトバックのネスト処理

ネストが発生する可能性がある場合、各MSHRはMainPipeからブロードキャストされる要求ネスト情報を受信します。これには、ネストが発生する可能性のあるキャッシュラインのタグとセットアドレス、およびネスト動作が含まれます。特定の信号は、MSHR内の```nestwb```ポートとNestedWriteback Bundleクラスです。

上流のRelease/ReleaseData要求と下流のスヌープ要求の潜在的なネストを考慮すると、MSHR内で必要なさまざまなネスト処理ロジックは次のとおりです。

### 特徴1：置換されるキャッシュラインが上流のReleaseData TtoNとネストしている

このネストは、MSHR内の追い出されたキャッシュラインのタグとセットアドレスが、MainPipeからすべてのMSHRにブロードキャストされたReleaseData TtoNのタグとセットアドレスと一致する場合に発生します。対応する信号名は```c_set_dirty```です。

このネストは通常、CoupledL2が置換のためにすでに上流のL1キャッシュにProbe toN要求を送信しているか、送信中であり、このProbe toNに対するL1キャッシュの応答がCoupledL2によってまだ観測されておらず、L1キャッシュが積極的にCoupledL2にReleaseData TtoNを開始するように促す場合に発生します。

このとき、MSHR内に記録されているキャッシュラインの状態を次のように更新する必要があります。

- ダーティとしてマークする
- 状態をTIPに更新する。
- 上流L1がこのキャッシュラインを保持しなくなった状態に更新する

### 特徴2：置換されるキャッシュラインが上流のRelease TtoNとネストしている

このネストは、MSHR内の置換されたキャッシュラインのタグとセットアドレスが、MainPipeから各MSHRにブロードキャストされたRelease TtoNのタグとセットアドレスと一致する場合に発生します。対応する信号名は```c_set_tip```です。

このタイプのネストは通常、CoupledL2が置換のためにすでに上流のL1キャッシュにProbe toN要求を送信しているか、送信中であり、このProbe toNに対する上流L1キャッシュの応答がCoupledL2によってまだ観測されておらず、上流L1キャッシュが積極的にCoupledL2にRelease TtoNを開始する場合に発生します。

このとき、MSHR内に記録されているキャッシュラインの状態を次のように更新する必要があります。

- 状態をTIPに更新する。
- 上流L1がこのキャッシュラインを保持しなくなった状態に更新する

### 特徴3：置換されるキャッシュラインが下流のスヌープとネストしている

このネストは、MSHR内の置換されたキャッシュラインのタグとセットアドレスが、MainPipeからさまざまなMSHRエントリにブロードキャストされた下流のスヌープのタグとセットアドレスと一致する場合に発生します。対応する信号名は```b_inv_dirty```です。

ここでの下流スヌープは、CHIプロトコルでキャッシュラインの状態を変更できないタイプのスヌープ（SnpQuery、SnpStashUnique、SnpStashSharedなど）を除外する必要があります。

このタイプのネストは通常、CoupledL2が置換によって引き起こされたライトバック要求をすでに下流に送信しているか、送信中であり、下流からCompDBIDResp応答を受信する前に、下流によって新しいスヌープ要求がCoupledL2に開始される場合に発生します。

このとき、MSHR内に記録されているキャッシュラインの状態を次のように更新する必要があります。

- 状態をクリーンにクリア
- 状態をINVALIDに更新
- 上流L1キャッシュがProbeAckDataで応答したために設定されたダーティフラグをクリアする

### 特徴4：下流でネストされたスヌーピングが発生したときにBRANCH状態をディレクトリに書き込む

このネストは、MSHRのタグとセットアドレスが、MainPipeから各MSHRエントリにブロードキャストされた下流のスヌープのタグとセットアドレスと一致し、スヌープ要求がMainPipeにBRANCHキャッシュライン状態を書き込む場合に発生します。

このタイプのネストは通常、CoupledL2が置換によって引き起こされたライトバック要求をすでに下流に送信しているか、送信中であり、下流からCompDBIDResp応答を受信する前に、下流によって新しいスヌープ要求がCoupledL2に開始される場合に発生します。

このとき、MSHR内に記録されているキャッシュラインの状態を次のように更新する必要があります。

- 状態をクリーンにクリア
- キャッシュラインの権限がINVALIDでない場合は、BRANCHに更新する
- 上流L1キャッシュがProbeAckDataで応答したために設定されたダーティフラグをクリアする

### 特徴5：下流でネストされたスヌープが発生したときにINVALID状態をディレクトリに書き込む

このネストは、MSHRのタグとセットアドレスが、MainPipeから各MSHRにブロードキャストされた下流のスヌープのタグとセットアドレスと一致し、スヌープ要求がMainPipeにINVALIDキャッシュライン状態を書き込む場合に発生します。

このタイプのネストは通常、CoupledL2が置換によって引き起こされたライトバック要求をすでに下流に送信しているか、送信中であり、下流からCompDBIDResp応答を受信する前に、下流によって新しいスヌープ要求がCoupledL2に開始される場合に発生します。

このとき、MSHR内に記録されているキャッシュラインの状態を次のように更新する必要があります。

- 状態をクリーンにクリア
- 状態をINVALIDに更新
- 上流L1がこのキャッシュラインを保持しなくなった状態に更新する
- 上流L1キャッシュがProbeAckDataで応答したために設定されたダーティフラグをクリアする
- 置換が必要な要求の場合は、置換するラインを再選択する

## 再試行とPクレジットメカニズム

下流からRetryAck応答を受信した場合、MSHRはPクレジットクエリの有効ビットをアサートし、CHI PCrdTypeおよびSrcIDフィールドをMainPipeに送信します。MainPipeは、MSHR内の対応するトランザクションにPクレジットを割り当てて再試行するかどうかを決定します。Pクレジットの受信と割り当ての詳細については、[@sec:reqarb-mainpipe] [リクエストアービタとメモリパイプライン](ReqArb_MainPipe.md)を参照してください。
