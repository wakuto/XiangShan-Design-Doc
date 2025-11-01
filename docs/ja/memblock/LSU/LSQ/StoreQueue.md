# ストアキュー StoreQueue

## 機能説明

StoreQueueは、すべてのストア命令を保持するキューで、以下の機能を持ちます。

*   ストア命令の実行状態を追跡する
*   ストアのデータを格納し、その状態（到着したかどうか）を追跡する
*   ロードにクエリインターフェースを提供し、ロードが同じアドレスのストアをフォワードできるようにする
*   MMIOストアとNonCacheableストアの実行を担当する
*   ROBによってコミットされたストアをsbufferに書き込む
*   LoadQueueRAWの解放とLoadQueueReplayのウェイクアップのために、アドレスとデータの準備完了ポインタを維持する

ストアは、アドレスとデータのディスパッチを分離して最適化されています。つまり、StoreUnitはストアアドレスをディスパッチするパイプラインであり、StdExeUnitはストアデータをディスパッチするパイプラインです。これらは2つの異なる予約ステーションです。ストアデータは準備ができ次第StdExeUnitにディスパッチでき、ストアアドレスは準備ができ次第StoreUnitにディスパッチできます。

*   StoreQueueの各エントリには、ストア命令の基本情報が格納されています。

    Table: StoreQueueに格納される基本情報

| フィールド | 説明 |
| :--- | :--- |
| uop | ストア命令uop |
| dataModule | 128ビットデータとデータ有効マスク |
| paddrModule | 物理アドレス |
| vaddrModule | 仮想アドレス |


*   StoreQueueの各エントリには、ストアの状態を示すいくつかのステータスビットがあります。

    Table: StoreQueueに格納される状態情報

| フィールド | 説明 |
| :--- | :--- |
| allocated | このエントリのallocated状態を設定して、このストアのライフサイクルの追跡を開始します。 |
| | このストア命令がSbufferにコミットされると、allocated状態はクリアされます。 |
| addrvalid | アドレス変換によって物理アドレスが取得されたかどうかを示し、ロードフォワードチェック時のCAM比較に使用されます。 |
| datavalid | ストアデータが発行され、利用可能かどうかを示します。 |
| committed | ストアがROBによってコミットされたかどうか。 |
| unaligned | 非整列ストア |
| cross16Byte | 16バイト境界を越える |
| pending | このストアがMMIO空間にあるかどうか。主にMMIOのステートマシンを制御するために使用されます。 |
| nc | NonCacheableストア |
| mmio | mmioストア |
| atomic | アトミックストア |
| memBackTypeMM | PMAがメインメモリタイプであるかどうか |
| prefetch | Sbufferにサブミットするときにプリフェッチが必要かどうか |
| isVec | ベクトルストア |
| vecLastFlow | ベクトルストアフローの最後のuop |
| vecMbCommit | マージバッファからROBにコミットされたベクトルストア。 |
| hasException | ストア命令に例外がある |
| waitStoreS2 | Store Unit s2からのmmioと例外の結果を待つ。 |

### 特徴1：データフォワーディング

*   ロードは、それより前にある同じアドレスの最新の依存ストアのデータを見つけるためにStoreQueueをクエリする必要があります。

    *   クエリバス（io.forwrd.sqIdx）をStoreQueueのenqPtrポインタと比較して、ロード命令より古いすべてのStoreQueueエントリを特定します。フラグが一致するかどうかに基づいて2つのケースに分けられます。

        *   同じフラグが設定されている場合、古いストアの範囲は[tail, sqIdx - 1]です（図\ref{fig:LSQ-StoreQueue-Forward-Mask} a)参照）。それ以外の場合、古いストアの範囲は[tail, VirtualLoadQueueSize - 1]と[0, sqIdx]です（図\ref{fig:LSQ-StoreQueue-Forward-Mask} b)参照）。

        ![StoreQueueフォワーディング範囲生成](./figure/LSQ-StoreQueue-Forward-Mask.svg){#fig:LSQ-StoreQueue-Forward-Mask width=90%}


    *   クエリバスは、ルックアップに仮想アドレスと物理アドレスの両方を使用します。物理アドレスの一致が見つかったが仮想アドレスが一致しない場合、またはその逆の場合、対応するロード命令はreplayInstとしてマークされ、ロードがROBヘッドに到達すると再実行されます。

    *   一致するエントリが1つだけで、そのデータが準備できている場合は、直接フォワードします。

    *   一致するエントリが1つだけで、データが準備できていない場合、予約ステーションが再送を担当する必要があります。

    *   複数の一致が見つかった場合は、最も古いストアをフォワードします。

    *   StoreQueueは1バイト単位で動作し、図\ref{fig:LSQ-StoreQueue-Forward}に示すように、ツリーベースのデータ選択ロジックを採用しています。

    \newpage

    ![StoreQueueフォワードデータ選択](./figure/LSQ-StoreQueue-Forward.svg){#fig:LSQ-StoreQueue-Forward width=80%}


*   データフォワーディングに参加するストアは、以下を満たす必要があります。

    *   allocated：このストアはまだストアキュー内にあり、sbufferにはまだ書き込まれていません。

    *   datavalid：このストアのデータは準備できています。

    *   addrvalid：このストアは仮想から物理へのアドレス変換を完了し、物理アドレスを取得しています。

    *   メモリアクセス依存性予測器が有効な場合、SSID（Store-Set-ID）は以前に失敗したロード予測実行の履歴情報をマークします。現在のロードが履歴内のSSIDにヒットした場合、すべての古いストアが完了するのを待ちます。ヒットがない場合は、同じ物理アドレスを持つ古いストアのみが完了するのを待ちます。

### 特徴2：非整列ストア命令

StoreQueueは、非整列ストア命令の処理をサポートしています。各非整列ストア命令は1つのエントリを占有し、dataBufferでアドレスとデータを整列させた後に書き込まれます。

### 特徴3：ベクトルストア命令

図\ref{fig:LSQ-StoreQueue-Vector}に示すように、StoreQueueはベクトルストア命令のエントリを事前に割り当てます。StoreQueueは、vecMbCommitを介してベクトルストアのコミットを制御します。

*   各ストアについて、フィードバックベクトルfbkから対応する情報を取得します。

    ストアがコミット条件（有効で、コミットまたはフラッシュとしてマークされている）を満たしているかどうかを判断し、ストアがuop(i)に対応する命令と一致するかどうかを（robIdxおよびuopIdxを介して）チェックします。ストアは、すべての条件が満たされた場合にのみコミット済みとしてマークされます。VecStorePipelineWidth内のいずれかの命令が条件を満たしているかどうかをチェックします。満たしている場合、ベクトルストアはコミット済みと見なされます。それ以外の場合は、そうではありません。

*   特殊なケースの処理（ストアがページ境界を越える場合）：

    特殊な状況下（ストアがページ境界を越え、storeMisalignBufferに同じuopが含まれている場合）、ストアが条件io.maControl.toStoreQueue.withSameUopを満たす場合、vecMbCommitは強制的にtrueに設定され、他の要因に関係なくストアがコミットされたことを示します。

![ベクトルストア命令](./figure/LSQ-StoreQueue-Vector.svg){#fig:LSQ-StoreQueue-Vector width=25%}


### 特徴4：CMO

StoreQueueはCMO命令をサポートしており、MMIOステートマシン制御を共有します。

*   s_idle：アイドル状態。CMOストアリクエストを受信するとs_reqに遷移します。

*   s_req：Sbufferをリフレッシュし、ラインフラッシュが完了するのを待ってから、CMOReqを介してCMO操作リクエストを送信し、s_resp状態に入ります。

*   s_resp：CMORespから応答を受信すると、s_wb状態に遷移します。

*   s_wb：ROBがCMO命令をコミットするのを待ってから、s_idle状態に遷移します。

### 特徴5：CBO

StoreQueueはCBO.zero命令をサポートしています。

*   CBO.zero命令のデータ部分は、dataModuleに0を書き込みます。

*   CBO.zeroがSbufferに書き込まれるとき：Sbufferをフラッシュし、フラッシュが完了するのを待ってから、cboZeroStoutを介して書き戻します。

### 特徴6：MMIOおよびNonCacheableストア命令

*   MMIOストア命令の実行

    *   MMIO空間へのストアは、ROBの先頭に到達したときにのみ実行できますが、ロードとは少し異なります。ストアがROBの先頭に到達したとき、必ずしもストアキューの末尾にあるとは限りません。一部のストアはすでにコミットされているが、まだストアキューにあり、sbufferに書き込まれていない場合があります。これらのストアは、MMIOストアが続行する前に、まずsbufferに書き込む必要があります。

    *   ステートマシンを使用してMMIOストアの実行を制御します。

        *   s_idle：アイドル状態。MMIOストアリクエストを受信するとs_reqに遷移します。

        *   s_req：MMIOチャネルにリクエストを送信します。リクエストがMMIOチャネルに受け入れられると、s_resp状態に遷移します。

        *   s_resp：MMIOチャネルが応答を返します。それを受信した後、例外が生成されたかどうかを記録し、s_wb状態に遷移します。

        *   s_wb：結果を内部信号に変換し、ROBに書き戻します。成功すると、例外がある場合はs_idleに遷移します。それ以外の場合は、s_wait状態に進みます。

        *   s_wait：ROBがこのストア命令をコミットするのを待ちます。コミット後、s_idle状態に戻ります。

*   NonCacheableストア命令の実行

    *   NonCacheable空間のストア命令は、コミット後まで待ってからStoreQueueから順番に送信する必要があります。

    *   ステートマシンを使用してNonCacheableストアの実行を制御します。

        *   nc_idle：アイドル状態。NonCacheableストアリクエストを受信するとnc_reqに遷移します。

        *   nc_req：NonCacheableチャネルにリクエストを送信します。リクエストがNonCacheableチャネルに受け入れられた後、uncacheOutstanding機能が有効な場合はnc_idleに遷移します。それ以外の場合は、nc_resp状態に入ります。

        *   nc_resp：NonCacheableチャネルからの応答を受け入れ、nc_idle状態に遷移します。

### 特徴7：ストア命令のコミットとSBufferへの書き込み

StoreQueueは早期コミットアプローチを採用しています。
*   早期コミットルール：

    *   コミットフェーズに入るための条件を確認します。

        *   命令が有効であること。

        *   命令のROBヘッドポインタが保留中のコミットポインタを超えていないこと。

        *   命令をキャンセルする必要がないこと。

        *   命令がストア操作の完了を待たないか、ベクトル命令であること。

    *   CommitGroupの最初の命令である場合、

        *   MMIOステータスを確認します：MMIO操作がないか、MMIO操作が存在し、MMIOストアがコミットされていること。

        *   ベクトル命令の場合、それ以外の場合はvecMbCommit条件を満たす必要があります。

    *   CommitGroupの最初の命令でない場合、

        *   コミット状態は前の命令のコミット状態に依存します。

        *   ベクトル命令の場合、vecMbCommit条件を満たす必要があります。

サブミット後、ストアはsbufferに順次書き込むことができます。これらのストアは、まずdataBufferに書き込まれます。これは、より大きなストアキューからの読み取りレイテンシを処理するために使用される2エントリのバッファ（チャネル0および1）です。チャネル0のみが非整列命令を処理できます。設計を簡素化するため、両方のポートで例外が発生した場合でも、1つの非整列デキューのみが許可されます。

*   書き込み有効信号の生成：

    *   0チャネル命令が16バイト境界を越えてミスアラインしている場合：

        *   チャネル0の命令が割り当てられ、コミットされていること。

        *   dataBufferのチャネル0と1が同時に命令を受け入れることができること。

        *   チャネル0の命令がベクトル命令ではなく、アドレスとデータが有効であること。または、vsMergeBufferを持つベクトル命令であり、コミットされていること。

        *   4Kページテーブルを越えないこと。または、4Kページテーブルを越えるがデキュー可能であり、1）チャネル0の場合：例外のあるデータの書き込みを許可する。2）チャネル1の場合：例外のあるデータの書き込みを許可しない。

        *   前の命令がNonCacheable命令ではなかったこと。最初の命令である場合、それ自体がNoncacheable命令であってはなりません。

    *   それ以外の場合、以下の条件を満たす必要があります。

        *   命令が割り当てられ、コミットされていること。

        *   ベクトルではなく、アドレスとデータが有効であるか、ベクトルであり、vsMergeBufferがサブミットされていること。

        *   直前の命令がNonCacheableやMMIO命令ではないこと。最初の命令である場合、自身がNonCacheableやMMIO命令であってはなりません。

        *   未整列ストアの場合、16バイト境界を越えないこと。越える場合は、アドレスとデータが有効であるか、例外が存在する必要があります。

*   アドレスとデータの生成：

    *   アドレスは上下に分割されます。

        *   低位アドレス：8バイト境界に揃えたアドレス。

        *   高位アドレス：低位アドレスに8を加算した値。

    *   データは上下に分割されます。

        *   16バイト境界を跨ぐデータ：元のデータをアドレス下位4ビットが示すバイト数だけ左シフトした値。

        *   低位データ：16バイト境界を跨ぐデータの下位128ビット。

        *   高位データ：16バイト境界を跨ぐデータの上位128ビット。

    *   書き込み選択ロジック：

        *   dataBufferが未整列命令の書き込みを受け付け、チャネル0の命令が未整列かつ16バイト境界を跨ぐ場合：

            *   4Kページを跨がず、もしくは跨ぐがデキュー可能な場合：チャネル0は低位アドレスと低位データでdataBufferに書き込み、チャネル1はStoreMisalignBufferの物理アドレスと高位データで書き込みます。

            *   それ以外の場合：チャネル0は低位アドレスと低位データで、チャネル1は高位アドレスと高位データでdataBufferに書き込みます。

        *   チャネルの命令が16バイト境界を跨がず未整列の場合は、16バイト境界に揃えたアドレスと整列済みデータでdataBufferに書き込みます。

        *   それ以外の場合、元のデータとアドレスをdataBufferに書き込みます。

### 特徴8：Sbufferの強制フラッシュ

StoreQueueは、Sbufferを強制的にフラッシュするために二重しきい値方式（上限閾値と下限閾値）を用います。StoreQueueの有効エントリ数が上限閾値を超えると、Sbufferの強制フラッシュを開始し、有効エントリ数が下限閾値を下回るまで継続します。

\newpage

## 全体ブロック図

![StoreQueue全体ブロック図](./figure/LSQ-StoreQueue.svg){#fig:LSQ-StoreQueue width=90%}

## インタフェースタイミング

### エンキューインタフェースタイミング例

![StoreQueue全体ブロック図](./figure/LSQ-StoreQueue-Enq-Timing.svg){#fig:LSQ-StoreQueue-Enq-Timing width=90%}

\newpage

### データ更新インタフェースタイミング

![データ更新インタフェースタイミング](./figure/LSQ-StoreQueue-Data-Timing.svg){#fig:LSQ-StoreQueue-Data-Timing width=90%}

### アドレス更新インタフェースタイミング

StoreQueueのアドレス更新はデータ更新と類似しており、StoreUnitはs1段でio_lsqを介してアドレスを更新し、s2段でio_lsq_replenishを介して例外を更新します。データ更新と異なり、アドレス更新は1サイクルで完了します。

### MMIOインタフェースタイミング例

![MMIOインタフェースタイミング例](./figure/LSQ-StoreQueue-MMIO-Timing.svg){#fig:LSQ-StoreQueue-MMIO-Timing width=90%}

\newpage

### NonCacheableインタフェースタイミング例

![NonCacheableインタフェースタイミング例](./figure/LSQ-StoreQueue-NC-Timing.svg){#fig:LSQ-StoreQueue-NC-Timing width=90%}

### CBOインタフェースタイミング例

![CBOインタフェースタイミング例](./figure/LSQ-StoreQueue-CBO-Timing.svg){#fig:LSQ-StoreQueue-CBO-Timing width=90%}

\newpage

### CMOインタフェースタイミング例

![CMOインタフェースタイミング例](./figure/LSQ-StoreQueue-CMO-Timing.svg){#fig:LSQ-StoreQueue-CMO-Timing width=90%}
