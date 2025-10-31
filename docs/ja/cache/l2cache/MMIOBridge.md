# MMIOブリッジ MMIOBridge

MMIOBridgeはCoupledL2の4つのスライスから独立して動作し、IFU/LSUからMMIOおよびUncacheリクエストを受け取ります。CHIバスを介して下流のNoC/LLCと対話し、ペリフェラルの読み書き操作を完了します。デフォルトでは、MMIOBridgeには8つのMMIOBridgeEntryアイテムが含まれており、それぞれが1つのMMIOまたはUncacheリクエストを処理する独立したステートマシンです。

## ステートマシン

ステートマシンエントリは、主に2つのカテゴリに分類されます。

- スケジュール状態エントリ
- 待機状態アイテム

スケジュール状態アイテムは、アクティブアクション状態アイテムとも呼ばれ、主にMMIOBridgeEntryから上流のTileLinkバスおよび下流のCHIバスに送信されるアクティブなタスクとリクエストを追跡するために使用されます。その値はアクティブローであり、不完全な状態を示します。つまり、タスクがまだMMIOBridgeEntryを正常に離れて発行されておらず、ブロッキング条件（必要な先行アクションが完了していない）またはチャネルブロッキングが原因である可能性があります。ハイの値は、対応するタスクが正常に発行されたか、発行する必要がないことを示します。

待機状態エントリは、パッシブアクション状態エントリとも呼ばれ、主にMMIOBridgeEntryが下流のCHIチャネルまたは上流のTileLinkチャネルから期待する応答を追跡するために使用されます。ローの値は不完全な状態を示し、対応する応答がまだ現在のエントリに戻っていないことを意味します。ハイの値は、応答が受信されたか、応答が必要ないことを示します。

ステータスレジスタには以下が含まれます。

| 名前                | 説明                                                                                                                                                 |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ```s_txreq```       | ReadNoSnp / WriteNoSnpPtlリクエストを下流のTXREQチャネルに送信します。                                                                                    |
| ```s_ncbwrdata```   | （書き込み操作用）NCBWrDataパケットを下流のTXDATチャネルに送信します。NCBWrDataを送信するための前提条件は、```w_dbidresp```がアサートされていることです。 |
| ```s_resp```        | CHIの読み書きトランザクションが完了し、AccessAckData/AccessAck応答を上流のTileLink Dチャネルに返します。                             |
| ```w_comp```        | （書き込み操作用）下流のRXRSPチャネルから返されるComp / CompDBIDResp応答を待ちます。                                                  |
| ```w_dbidresp```    | （書き込み操作用）下流のRXRSPチャネルから返されるCompDBIDResp / DBIDResp / DBIDRespOrd応答を待ちます。                                |
| ```w_compdata```    | （読み取り操作用）下流のRXDATチャネルから返されるCompDataを待ちます。                                                                       |
| ```w_pcrdgrant```   | プロトコル層の再送信に遭遇した読み書きリクエストの場合、下流がPCrdGrantを返すのを待つ必要があります。                    |
| ```w_readreceipt``` | （OrderがNoneでない読み取りリクエストの場合）下流のRXRSPチャネルから返されるReadReceiptを待ちます。                                              |

## シーケンシング

MMIOBridgeによって開始されるCHIリクエストは、デフォルトでRequestOrderまたはEndpointOrderになります。コアがTileLinkの読み書きリクエストを開始すると、Aチャネルのカスタムフィールドに**PMA属性を含めて、それがメモリであるかどうかを示します**。

- アドレスのPMA属性がMemoryであるが、PBMT属性がIOまたはNCの場合、開始されるCHIトランザクションのOrderはRequestOrderです。
- アドレスのPMA属性がMemoryであるが、PBMT属性がIOまたはNCの場合、開始されるCHIトランザクションのOrderはEndpointOrderです。

RequestOrderまたはEndpointOrderのいずれであっても、開始されたReadNoSnpは、読み取り操作の順序付けのために下流がReadReceiptを返す必要があります。したがって、MMIOBridgeは各エントリがReadReceiptを待っているかどうか（つまり、```w_readreceipt```がローにプルされているかどうか）を監視します。いずれかのエントリがReadReceiptを待っている場合、どのエントリからも新しいReadNoSnpを下流に送信することはできません。

## メモリ属性

CHIバスプロトコルは、メモリ属性の次の4つの次元を定義します。

- Allocate
- Cacheable
- Device
- EWA (Early Write Acknowledgment)

MMIOBridgeによって開始されるリクエストの場合、AllocateとCacheableは常に0です。DeviceはPMA属性に依存します。PMA属性がMemoryの場合、Deviceは0、それ以外の場合、Deviceは1です。EWAはアドレスがバッファ可能であるかどうかと理解できます。アドレスのPMA属性がMemoryであるか、PMA属性がMemoryではないがPBMT属性がNCである場合、アドレスはバッファ可能と見なされ、EWAは1に設定されます。それ以外の場合、EWAは0に設定されます。

## P-Creditアービトレーション

MMIOBridgeは、CHIバスでのプロトコル層の再送信をサポートしています。CHIバスプロトコルによれば、トランザクションはRetryAckとPCrdGrantを受信した後にのみプロトコル層の再送信を開始できます。RetryAckのTxnIDはTXREQチャネル上のリクエストのTxnIDと一致するため、RetryAckはTxnIDを介してMMIOBridge内のエントリと1対1でマッピングできます。ただし、PCrdGrantはSrcIDとPCrdTypeフィールドがRetryAckと一致することのみを要求し、TxnIDを介してMMIOBridge内のエントリと直接一致させることはできません。

CHIプロトコルの仕様に基づくと、CoupledL2がPCrdGrantを受信した場合、PCrdGrantフィールドに基づいてP-CreditをMMIOBridgeまたは4つのスライスのいずれに調停すべきか、またP-Creditを特定のMMIOBridgeEntryまたはMSHRにどのようにマッピングするかを直接判断することはできません。したがって、P-CreditアービトレーションロジックはCoupledL2のトップレベルに存在します。PCrdGrantを受信すると、CoupledL2はそれを一時的にトップレベルのレジスタに格納します（SrcIDやPCrdTypeなどのキーフィールドを記録）。RetryAckを受信したMSHR/MMIOBridgeEntryは、RetryAckのSrcIDとPCrdTypeをPCrdGrantレジスタバンクと照合します。一致が見つかった場合、対応するレジスタエントリは解放されます。見つからない場合は、一致が成功するまで下流のPCrdGrantを待ちます。
