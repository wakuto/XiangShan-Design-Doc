# エラー処理

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/04/24

## 用語集

| 略語 | 正式名称                                | 説明                                               |
| ------------ | ---------------------------------------- | -------------------------------------------------------- |
| ICache/I$    | Instruction Cache                        | L1命令キャッシュ                                     |
| DCache/D$    | Data Cache                               | L1データキャッシュ                                      |
| L1 Cache/L1$ | Level One Cache                          | L1キャッシュ                                                 |
| L2 Cache/L2$ | Level Two Cache                          | L2キャッシュ                                                 |
| L3 Cache/L3$ | Level Three Cache                        | L3キャッシュ                                                 |
| BEU          | Bus Error Unit                           | バスエラーユニット                                           |
| MMIOBridge   | Memory-Mapped I/O Bridge                 | メモリマップドI/Oブリッジ                                |
| ECC          | Error Correction Code                    | 誤り訂正符号                                         |
| SECDED.      | Single Error Correct Double Error Detect | 単一ビット誤り訂正、2ビット誤り検出。 |
| TL           | Tile Link.                               | Tile Linkバスプロトコル                                   |
| CHI.         |                                          | CHIバスプロトコル                                                 |

## 設計仕様

- ECCチェックをサポート
- CHI DataCheckをサポート
- CHI Poisonをサポート

## キャッシュ化されたメモリアクセス要求のエラー処理

基本エラー処理ロジック：エラーを検出したキャッシュレベルがそれを報告し、アドレスに対応するエラーステータスが保存/伝播されます。

    1. L2キャッシュは、L2キャッシュで検出されたECC/DataCheckエラーをBEUに報告し、BEUがソフトウェアにエラーを報告するための割り込みをトリガーします。
    2. L1/L3キャッシュからの要求に対して、L2キャッシュは検出されたエラーの種類に応じて通信でL1/L3キャッシュに通知します。
    3. L1/L3キャッシュからのエラーデータに対して、L2キャッシュはエラーの種類をメタデータに記録します。


### ECC

#### ECCチェックコード

L2キャッシュの現在のデフォルトECCチェックコードはSECDEDです。同時に、L2キャッシュはパリティ、SECなどのチェックコードをサポートしており、Configsで変更してコンパイル時に設定できます。[関連するチェックアルゴリズムのリファレンス](https://github.com/OpenXiangShan/Utility/blob/master/src/main/scala/utility/ECC.scala)

SECDEDでは、nビットのデータに対して、パリティビット数rが 2^r ≥ n + r + 1 を満たす必要があります。

#### ECC処理フロー

L2キャッシュはECC機能をサポートしています。MainPipeがs3ステージでディレクトリとDataStorageにデータをリフィルする際、タグとデータのチェックコードを計算します。前者はタグとともにディレクトリのtagArray（SRAM）に、後者はデータとともにDataStorageのarray（SRAM）に格納されます。

1. タグについては、タグを単位として直接ECCエンコード/デコードが実行されます。
2. データについては、物理設計とより良いエラー検出の必要性に基づき、現在はdataBankBits（128ビット）単位でECCエンコード/デコードが行われます。したがって、SECDEDアルゴリズムの要件下では、512ビットのキャッシュラインに対して、4 * 8 = 32ビットのチェックビットが存在することになります。

メモリアクセス要求がSRAMから読み出すとき、対応するチェックコードが同期して読み出されます。MainPipeは、それぞれs2およびs5ステージでタグとデータのチェック結果を取得します。エラーを検出すると、MainPipeはs5でエラー情報を収集し、CoupledL2はさまざまなスライスからのエラー信号を調停し、BEUに報告します。

### バスポート

#### TLバス

L2キャッシュがL1/L3キャッシュからデータを受信し、エラーを検出した場合（denied/corrupt = 1）、MainPipeはs3でディレクトリに書き込む際に、対応するメタデータのtagErr/dataErrを1に設定します。

L2キャッシュがL1/L3にデータを転送する際、L2キャッシュがECCエラーを検出するか、対応するメタデータにtagErr/dataErr = 1がある場合、対応するチャネル（例：DチャネルGrantBuffer）のdenied/corrupt信号が1に設定されます。それ以外の場合は0に設定されます。

- 特に、TL Dチャネルがデータを返す際、denied = 1の場合、対応するcorruptも1に設定する必要があります。現在の設計では、L2キャッシュはL1キャッシュが対応するデータのコピーを保持しているとは見なしません（L1キャッシュは後続のRelease時に対応するコピーを直接破棄します）。

- 特に、TL Cチャネルにはcorruptフィールドは存在するがdeniedフィールドは存在しないため、opcodeフィールドがdenied/corruptの区別を補助するために使用されます。[SinkC](https://github.com/OpenXiangShan/CoupledL2/blob/master/src/main/scala/coupledL2/SinkC.scala)のように
```
task.corrupt := c.corrupt && (c.opcode === ProbeAckData || c.opcode === ReleaseData)
task.denied := c.corrupt && (c.opcode === ProbeAck || c.opcode === Release)
```

#### CHIバス

L2キャッシュは設定可能なPoison/DataCheckをサポートしています：
- Poisonフィールド：
    - DATでは、8バイトごとに1つのPoisonビットが設定されます。
    - L2キャッシュはPoisonに対してオーバーポイズン戦略を採用しています。
    - PoisonエラーはL2キャッシュによって報告されません。

- DataCheckフィールド：
    - DATでは、8ビットごとに1つのDataCheckビットが設定されます。
    - L2キャッシュでは、DataCheckはデフォルトで奇数パリティです。
    - L2キャッシュでは、DataCheckはデータのみを検証し、パケット全体はチェックしません。
    - DataCheckエラーはL2キャッシュによって報告されます。

L2キャッシュがL3キャッシュからデータを受信し、エラーを検出した場合：

1. respErr = NDERRの場合、対応するデータをL2キャッシュに書き込みませんが、残りのパイプライン処理は完了します（例えば、L1キャッシュからのAcquire要求に対して、L2キャッシュはデータを返し、deniedとcorruptを1に設定します）。
2. respErr = NDERR/DERR、またはpoisonフィールドのいずれかのビットが1、またはdataCheckの奇数パリティでエラーが検出された場合、MainPipeはs3でディレクトリに書き込む際に、対応するメタデータのdataErrを1に設定します。
3. dataCheckがエラーを検出した場合、ECCエラー報告プロセスを再利用します。MainPipeはs5でエラー情報を収集し、BEUに報告します。

L2キャッシュがL3キャッシュにデータを転送する場合：

1. L2キャッシュがタグECCエラーを検出するか、対応するメタデータにtagErr = 1がある場合、respErrをNDERRに、poisonをすべて0に設定します。
2. L2キャッシュがデータECCエラーを検出するか、対応するメタデータにdataErr = 1がある場合、respErrをDERRに、poisonフィールドをすべて1に設定します。
3. L2キャッシュがデータECCエラーを検出するか、対応するメタデータにtagErr = 1かつdataErr = 1がある場合、respErrをNDERRに、poisonをすべて1に設定します。
4. L2キャッシュでエラーが検出されない場合、respErrはOKに、poisonはすべて0に設定されます。
5. dataCheckフィールドには、データのパリティチェックコードが入力されます。

* 現行バージョンでは、L2がサポートするWrite/Snoopトランザクションでは、関連するデータパケット転送でrespErrがNDERRになることは許可されていません（したがって、TXDATのrespErrは実際にはDERRまたはOKのみです）。

コヒーレンス状態の処理（RNがNDERRを含む要求を受信した場合）：

1. 割り当てトランザクションの場合、L2はパイプラインを正常に処理しますが、NDERR要求に関連するデータをディレクトリまたはDataStorageに書き戻さず、キャッシュ状態は変わりません（具体的な関連トランザクションタイプはReadClean, ReadNotSharedDirty, ReadShared, ReadUnique, CleanUnique, MakeUniqueです）。
2. リリーストランザクションの場合、L2はそれらを正常に処理します（具体的な関連トランザクションタイプはWriteBack, WriteEvictFull, Evict, WriteEvictOrEvictです）。
3. スヌープの場合、L2はL1をプローブし（ToN）、SnpResp_IとNDERRで応答し、一律にフォワードしません（CompDataを返信しません）。L2の対応するキャッシュラインをInvalidに設定することは一時的に行いません。
4. その他のトランザクションについては、L2は対応するデータキャッシュの状態がアップグレードされないことを保証します（現行バージョンでは、これは1によって保証されます）。

## 非キャッシュ化メモリアクセス要求のエラー処理

CoupledL2では、MMIOBridgeはTLとCHI間のエラー関連フィールドを変換しますが、エラーを報告しません。

CHIからTLへ（RXDAT/RXRSP）。

1. respErr = NDERRの場合、deniedを1に設定します。
2. respErr = NDERR/DERR、またはpoisonフィールドのいずれかのビットが1、またはdataCheckの奇数パリティでエラーが検出された場合、corruptを1に設定します。
3. それ以外の場合、deniedとcorruptの両方が0に設定されます。

- 具体的には、RXRSP（例：Comp）の場合、TL-SPECでは特定の応答タイプ（例：AccessAck）でcorrupt = 0が要求されるため、respErr = NDERR/DERRの場合、deniedが1に設定されます。
- エラーが発生した場合、ICacheまたはDCacheが後続でハードウェアエラーをトリガーし、それがソフトウェアに報告されて処理されます。

TLからCHIへ（TXDAT）。

1. corrupt = 1の場合、respErrをDERRに、poisonをすべて1に設定します。
2. corrupt = 0の場合、respErrをOKに、poisonをすべて0に設定します。
3. dataCheckフィールドには、データのパリティチェックコードが入力されます。
