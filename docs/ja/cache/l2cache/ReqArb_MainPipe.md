# 要求アービタとメインパイプライン {#sec:reqarb-mainpipe}

要求アービタとメモリアクセスパイプラインは、CoupledL2の全体的な5ステージパイプラインを形成し、順に第1ステージ```s1```、第2ステージ```s2```、第3ステージ```s3```、第4ステージ```s4```、第5ステージ```s5```と呼ばれます。その中で、要求アービタReqArbiterは主に```s1```と```s2```を構成し、メインパイプラインMainPipeは主に```s3```、```s4```、```s5```を構成します。

## S0パイプラインステージ

```s0```は要求アービタReqArbiter内にのみ位置し、独立したパイプラインステージとしてはカウントされません。```s0```は、各MSHRエントリのバックプレッシャ信号を生成するためにのみ使用されます。ReqArbiterは、次の条件下でタスクがMSHRを離れてパイプラインに入るのを防ぎます。

- 前のサイクルで、ディレクトリ読み取りを必要とするMSHRタスクがブロックされた
- GrantBufferからのブロッキング信号がある
- 上流のTileLink Cチャネルからのブロッキング信号がある
- 下流のTXDATチャネルからのブロッキング信号がある
- 下流のTXRSPチャネルからのブロッキング信号がある
- 下流のTXREQチャネルからのブロッキング信号がある

## S1パイプラインステージ

```s1```は要求アービタReqArbiter内にのみ位置します。

```s1```では、次の要求ソースに対して調停が実行されます。

- MSHR
- 上流TileLink Cチャネル
- 上流TileLink Bチャネル
- 上流TileLink Aチャネル

上記のリストでは、一番上にある要求ソースが最も高い優先度を持ちます。それらが同時にReqArbiterの```s1```に入ると、最も優先度の高いものがハンドシェイクのために選択され、他のタスクソースはブロックされます。具体的には、MSHRタスクが最も高い優先度を持ち、次に上流のTileLink Cチャネル、上流のTileLink Bチャネル、上流のTileLink Aチャネルが続きます。

```s1```では、ReqArbiterはMainPipeからのブロッキング信号も考慮する必要があります。さらに、要求は```s2```で準備ができたときにのみ```s1```を離れることができます。それ以外の場合、要求はブロックされ、```s1```に保存されます。

調停が完了した後、```s1```でディレクトリに読み取り要求が送信されます。


## S2パイプラインステージ

```s2```は、リクエストアービタReqArbiterとメインパイプラインMainPipe内にあります。

CoupledL2のSRAMの周波数制限のため、Multi-Cycle Path 2（MCP2）が採用されています。これは、各SRAMの読み書き要求が少なくとも2サイクル続く必要があることを意味します。したがって、```s2```で、ReqArbiterはすべての連続した要求を1サイクルブロックして、MainPipe上のホールド時間と要求間隔がMCP2要件に準拠するようにします。

ReqArbiterは```s2```でReleaseBufferまたはRefillBufferを読み取るかどうかを決定し、```s2```でReleaseBufferまたはRefillBufferに読み取り要求を送信します。

次のいずれかの条件下で、ReqArbiterは```s2```でRefillBufferに読み取り要求を送信します。

1. このタスクは、置き換えタスクによってトリガーされ、下流のキャッシュラインの書き戻しと退去を引き起こします（この時点で、書き戻しデータは不要になり、置き換え読み取りデータがDataStorageに書き込まれます）。
2. このタスクは上流のTileLink Aチャネル要求ですが、上流のProbe応答からのデータを使用しません（上流のProbe応答からのデータを使用する場合、ReleaseBufferから読み取る必要があります）。

次のいずれかの条件下で、ReqArbiterは```s2```でReleaseBufferに読み取り要求を送信します。

1. タスクはMSHRタスクであり、下流の要求は上流のProbe応答からデータを読み取る必要があります。
2. このタスクはMSHRタスクであり、上流のTileLink Aチャネル要求は上流のProbe応答からのデータを必要とします。
3. タスクはMSHRタスクではなく、下流のSnoopと下流のライトバック要求タスクがネストされています。

ReqArbiterは```s2```でタスクをMainPipeに送信します。

MainPipeは、```s2```で```s1```のブロッキング信号を生成し、ReqArbiterとRequestBufferに送り返します。MainPipeは、次の状況下でさまざまなコンポーネントとチャネルにブロッキング信号を送信する必要があります。

- タスクが```s2```に到達したときにディレクトリへの書き込み操作を絶対に実行しないと判断できない場合、同じセットの要求をブロックする信号がRequestBufferに送信されます。
- タスクが```s2```に到達したときにディレクトリへの書き込み操作を絶対に実行しないと判断できない場合、同じセットのMSHR要求をブロックする信号がReqArbiterに送信されます。
- タスクが```s2```に到達したときにディレクトリへの書き込み操作を絶対に実行しないと判断できない場合、同じセットの上流TileLink Cチャネル要求をブロックする信号がReqArbiterに送信されます。
- タスクが```s2```に到達すると（```s3```、```s4```、```s5```も同様、つまりMainPipeにまだいるすべてのタスク。以降のセクションでは繰り返し説明しません）、同じアドレスを持つ下流RXSNPチャネル要求をブロックする信号がReqArbiterに送信されます。

## S3パイプラインステージ

```s3```はMainPipeパイプライン内にのみ位置します。要求の判断、分配ロジック、および他のモジュールとの相互作用のほとんどは、```s3```ステージにあります。


### キャッシュライン状態の収集

ReqArbiterが```s1```でディレクトリに発行した読み取り要求は、```s3```で読み取り結果を取得できます。下流のRXSNPチャネルからの要求がMSHRとのネストを引き起こす場合、つまり、下流のSnoop要求のアドレスが未解決のMSHRのアドレスと一致する場合、そのMSHRエントリからのキャッシュライン状態がディレクトリの読み取り結果を上書きします。

### MSHR割り当て

MainPipeは、次のいずれかの条件が満たされたときに```s3```でMSHRを割り当てます。

1. タスクが上流のTileLink Aチャネルから発信された
    - Acquire*、Hint、Get要求がキャッシュラインをミスした
    - Acquire* toTキャッシュラインがBRANCH状態でヒットした
    - CBO*クラスのCMO要求
    - エイリアス置換要求
    - 上流にProbe要求を送信する必要があるタスク
        - Get要求が上流L1に存在するTRUNK状態のキャッシュラインにヒットした
        - CBOClean要求が上流L1に存在するTRUNK状態のキャッシュラインにヒットした
        - CBOFlush要求によってヒットしたキャッシュラインが上流L1に存在する
        - CBOInval要求によってヒットしたキャッシュラインが上流L1に存在する
2. タスクが下流のRXSNPチャネルから発信された
    - Snoopが対応するタイプの対応するキャッシュライン状態にヒットした
    - キャッシュラインヒットを伴うSnoopの転送

下流からの非転送SnoopタイプのSnoop要求の場合、MSHR割り当てを必要とする条件を以下に示します。

| Snoop要求タイプ | ヒット状態 | L1に存在 |
| ------------------- | ---------- | ------------ |
| SnpOnce | TRUNK | はい |
| SnpClean | TRUNK | はい |
| SnpShared | TRUNK | はい |
| SnpNotSharedDirty | TRUNK | はい |
| SnpUnique | - | はい |
| SnpCleanShared | TRUNK | はい |
| SnpCleanInvalid | - | はい |
| SnpMakeInvalid | - | はい |
| SnpMakeInvalidStash | - | はい |
| SnpUniqueStash | - | はい |
| SnpStashUnique | TRUNK | はい |
| SnpStashShared | TRUNK | はい |
| SnpQuery | TRUNK | はい |

### ディレクトリ書き込み

MainPipeは、タスクの要件に応じて```s3```でディレクトリに書き込み要求を送信します。

### DataStorageの読み書き

MainPipeは、タスクの要件に応じて```s3```でDataStorageに読み取りまたは書き込み要求を送信します。

### 要求とメッセージの配信

MainPipeは、タスクの要件に応じて、```s3```で次のチャネル方向のいずれかに要求を送信します。

- 上流TileLink Dチャネル
- 下流TXREQチャネル
- 下流TXRSPチャネル
- 下流TXDATチャネル

具体的な配信方向はタスク自体によって決定されます。詳細については、[@sec:mshr] [MSHR](MSHR.md)を参照してください。

### スヌープ要求の処理

下流からのスヌープ要求は、MSHRを割り当てずに、MainPipeで直接応答アクションを完了する場合があります。スヌープ要求の状態遷移は、MainPipeの```s3```で決定されます。```s3```で発生するスヌープ要求とそれに対応する状態遷移は次のとおりです。

| スヌープ要求タイプ | 初期状態 | 最終状態 | RetToSrc | スヌープ応答 |
| --------------------- | ------------- | ----------- | -------- | -------------------------- |
| SnpOnce | I | I | X | SnpResp_I |
| | UC | UC | X | SnpRespData_UC |
| | UD | UD | X | SnpRespData_UD_PD |
| | SC. | SC. | 0 | SnpResp_SC |
| | | | 1 | SnpRespData_SC |
| SnpClean, | I | I | X | SnpResp_I |
| SnpShared, | UC | SC. | X | SnpResp_SC |
| SnpNotSharedDirty | UD | SC. | X | SnpRespData_SC_PD |
| | SC. | SC. | 0 | SnpResp_SC |
| | | | 1 | SnpRespData_SC |
| SnpUnique | I | I | X | SnpResp_I |
| | UC | I | X | SnpResp_I |
| | UD | I | X | SnpRespData_I_PD |
| | SC. | I | 0 | SnpResp_I |
| | | | 1 | SnpRespData_I |
| SnpCleanShared | I | I | 0 | SnpResp_I |
| | UC | UC | 0 | SnpResp_UC |
| | UD | UC | 0 | SnpRespData_UC_PD |
| | SC. | SC. | 0 | SnpResp_SC |
| SnpCleanInvalid | I | I | 0 | SnpResp_I |
| | UC | I | 0 | SnpResp_I |
| | UD | I | 0 | SnpRespData_I_PD |
| | SC. | I | 0 | SnpResp_I |
| SnpMakeInvalid | - | I | 0 | SnpResp_I |
| SnpMakeInvalidStash | - | I | 0 | SnpResp_I |
| SnpUniqueStash | I | I | 0 | SnpResp_I |
| | UC | I | 0 | SnpResp_I |
| | UD | I | 0 | SnpRespData_I_PD |
| | SC. | I | 0 | SnpResp_I |
| SnpStashUnique, | I | I | 0 | SnpResp_I |
| SnpStashShared | UC | UC | 0 | SnpResp_UC |
| | UD | UD | 0 | SnpResp_UD |
| | SC. | SC. | 0 | SnpResp_SC |
| SnpOnceFwd | I | I | 0 | SnpResp_I |
| | UC | UC | 0 | SnpResp_UC_Fwded_I |
| | UD | UD | 0 | SnpResp_UD_Fwded_I |
| | SC. | SC. | 0 | SnpResp_SC_Fwded_I |
| SnpCleanFwd, | I | I | X | SnpResp_I |
| SnpNotSharedDirtyFwd, | UC | SC. | 0 | SnpResp_SC_Fwded_SC |
| SnpSharedFwd | | | 1 | SnpRespData_SC_Fwded_SC |
| | UD | SC. | X | SnpRespData_SC_PD_Fwded_SC |
| | SC. | SC. | 0 | SnpResp_SC_Fwded_SC |
| | | | 1 | SnpRespData_SC_Fwded_SC |
| SnpUniqueFwd | I | I | 0 | SnpResp_I |
| | UC | I | 0 | SnpResp_I_Fwded_UC |
| | UD | I | 0 | SnpResp_I_Fwded_UD_PD |
| | SC. | I | 0 | SnpResp_I_Fwded_UC |
| SnpQuery | I | I | 0 | SnpResp_I |
| | UC | UC | 0 | SnpResp_UC |
| | UD | UD | 0 | SnpResp_UD |
| | SC. | SC. | 0 | SnpResp_SC |

### タスクの早期終了

MainPipe上のタスクは、次のいずれかの条件が満たされた場合、後続のパイプラインステージに進むことなく、ステージ```s3```で早期に終了できます。

1. タスクがDataStorageからReleaseBufferにデータを移行する必要がなく、次のいずれかの条件を満たす場合：
    - 上流/下流チャネル（上流TileLink D、下流TXREQ、下流TXRSP、下流TXDAT）へのタスクからの要求が```s3```でMainPipeを正常に離れる
    - タスクがMSHR割り当てを必要とする
2. 上流TileLink Dチャネル（AccessAckData、HintAck、GrantData、Grant）へのタスクの要求が再試行される。

## S4パイプラインステージ

MainPipeのタスクで、ステージ```s3```で早期に終了しなかったものは、ステージ```s4```に進みます。タスクは、次のすべての条件を満たす場合、後続のパイプラインステージに入ることなく、ステージ```s4```で早期に終了できます。

- タスクはDataStorageからReleaseBufferにデータを移動する必要はありません
- 上流および下流チャネル（上流TileLink D、下流TXREQ、下流TXRSP、下流TXDAT）への要求は、```s4```でMainPipeをスムーズに終了します。

タスクが```s4```で完了しない場合、```s5```ステージに進みます。


## パイプラインステージS5

MainPipe上のタスクがステージ```s4```で早期に終了しない場合、ステージ```s5```に進みます。

ステージ```s3```でDataStorageへの読み取り要求が開始された場合、対応するキャッシュラインデータは```s5```で取得できます。

```s5```で、MainPipeはタスクの要件と要求のネストに基づいて、DataStorageまたはMainPipeからReleaseBufferにデータを書き込みます。
