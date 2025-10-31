# アトミック命令実行ユニット AtomicsUnit

## 機能説明

AtomicsUnitは、A拡張（LR/SCおよびAMO命令）およびZacas拡張（AMOCAS.W、AMOCAS.D、およびAMOCAS.Q）を含むアトミック命令を実行するために使用されます。デフォルトでは、PMAはDDRアドレス空間内のすべてのAMOおよびAMOCAS命令をサポートします。

アトミック命令の基本的な実行フローは次のとおりです。

1.  **staディスパッチ**：AtomicsUnitはStoreUnitとディスパッチポートを共有し、予約ステーションからのsta uopをリッスンします。
2.  **stdディスパッチ**：アトミック命令はストア命令とStdExeUnit実行ユニットを共有します。StdExeUnitの実行結果はAtomicsUnitに送信され、AtomicsUnitはアトミック命令の実行に必要なすべてのデータを収集する責任があります。
3.  **アドレス変換**：AtomicsUnitはLoadUnit_0とDTLBポートを共有してアドレス変換を行い、同時にPMA/PMPなどの物理アドレスチェックを実行します。
4.  **SBufferのクリア**：現在、アトミック命令はaq/rlフラグが設定された状態で実行されるため、実行前にSBufferをクリアする必要があります。
5.  **DCacheへのアクセス**：DCacheにアトミック操作リクエストを送信します。完了後、DCacheは結果をAtomicsUnitに返します。
6.  **ライトバック**：AtomicsUnitは実行結果をレジスタファイルに書き戻します。

## 全体ブロック図

AtomicsUnitの有限ステートマシンを図に示します。

![AtomicsUnitステートマシン図](./figure/atomicsUnitFSM.svg)

-   **s_invalid**：AtomicsUnitはアイドル状態です。予約ステーションからディスパッチされたsta uopを受信すると、s_tlb_and_flush_sb_req状態に移行します。

-   **s_tlb_and_flush_sb_req**：アドレス変換のためにTLBにアクセスします。TLBミスの場合、ヒットするまでTLBにアクセスし続けます。同時に、SBufferにクリアを要求します。TLBヒット後、デバッグトリガーがアクティブになるか、アドレスの不整合例外が発生した場合、直接s_finish状態に移行してバックエンドに書き戻します。それ以外の場合は、s_pm状態に移行して物理アドレスの権限チェックとさらなる例外処理を行います。TLBアクセス中：
    -   LR命令の場合、読み取り権限が必要です。
    -   SC命令または他のAMO命令の場合、書き込み権限が必要です。

-   **s_pm**：物理アドレスの権限チェックと例外処理。以下の例外のいずれかが発生した場合、s_finish状態に移行してバックエンドに書き戻します。
    -   LR命令がTLBにアクセスして例外を返した場合、対応するLoadPageFault/LoadAccessFault/LoadGuestPageFault例外を報告します。
    -   LR以外の原子命令がTLB例外に遭遇した場合、対応するStorePageFault / StoreAccessFault / StoreGuestPageFault例外を発生させます。
    -   PBMT属性がPMAで、PMA属性がMMIOの場合、LR命令であるかどうかに基づいて、対応するLoadAccessFault / StoreAccessFaultを報告します。
    -   PBMT属性がIOまたはNCの場合、LR命令であるかどうかに基づいて、対応するLoadAccessFault / StoreAccessFaultを発生させます。
    -   PMP属性がMMIOであるか、読み取り/書き込み権限チェック例外が返された場合、LR命令であるかどうかに基づいて、対応するLoadAccessFault/StoreAccessFaultを報告します。

    上記の例外が発生しない場合、SBufferのクリアを開始します。
    -   SBufferが空でない場合、s_wait_flush_sbuffer_resp状態に移行してSBufferがクリアされるのを待ちます。
    -   SBufferがすでにクリアされている場合、s_cache_req状態に移行してDCacheにアクセスします。

-   **s_wait_flush_sbuffer_resp**：SBufferがクリアされるのを待ってから、s_cache_req状態に入りDCacheにアクセスします。

-   **s_cache_req**：すべてのstd uopを収集した後、DCacheにアクセス要求を送信します。ハンドシェイクが成功すると、s_cache_resp状態に入り、DCacheが処理を完了して応答するのを待ちます。
    -   AMOCAS命令はバックエンドから複数のstd uopを受信する必要があることに注意してください。AtomicsUnitは、DCacheに要求を送信する前に、s_cache_req状態ですべてのstd uopが受信されるまで待機する必要があります。

-   **s_cache_resp**：DCacheがアトミック操作を処理し、結果を返すのを待ちます。
    -   DCacheが一時的に要求を処理できず、AtomicsUnitに再送を要求する場合、s_cache_req状態に戻って要求を再送します。
    -   それ以外の場合、再送は不要で、s_cache_resp_latch状態に入ります。

-   **s_cache_resp_latch**：DCacheから返されたデータをシフトし、符号付き/符号なし拡張を実行します。タイミング上の理由から追加のサイクルが追加されています。次のサイクルでs_finish状態に移行します。
    -   DCacheがエラーを返した場合、対応するLoadAccessFault / StoreAccessFaultを記録する必要があります。

-   **s_finish**：アトミック命令の実行結果を書き戻します。
    -   LR命令またはAMO命令の場合、メモリから読み取られた古い値が書き戻されます。
    -   SC命令の場合、SC命令が正常に実行されたかどうかを書き戻します。成功の場合は0、失敗の場合は1です。

    ライトバックハンドシェイクが成功した後：
    -   AMOCAS.Q命令の場合、合計16Bのデータを書き戻す必要があります。前述のように、AMOCAS.Q命令は2つのsta uopを受信する必要があるため、ライトバックには2サイクルかかり、各ライトバックのpdestはそれぞれのuopのpdestに対応します。AMOCAS.Q命令の2つのsta uopには固定のディスパッチ順序はありませんが、ライトバックは順次行う必要があります。したがって、s_finish状態での最初のライトバック中に、最初のsta uopが受信されたことを確認する必要があります（ライトバックpdestの正しさを保証するため）。最初のライトバックが成功した後、2番目のライトバックのためにs_finish2状態に移行します。
    -   AMOCAS.Q命令でない場合、ライトバックハンドシェイクが成功した後、s_invalid状態に入り、ステートマシンは終了します。

-   **s_finish2**：AMOCAS.Q命令の場合、AtomicsUnitは2回目のライトバックを実行して16Bのデータの上位8Bを書き戻す必要があります。ライトバックの条件は、2番目のsta uopが受信されたことを確認することです。ライトバックハンドシェイクが成功すると、s_invalid状態に入り、ステートマシンは終了します。

## Zacas拡張

1.  AMOCAS.W命令は、rs1が指すメモリから4Bのデータをロードし、rdの下位4Bデータと比較します。等しい場合、rs2の下位4Bをrs1が指すメモリに書き込みます。最終的に、メモリからロードされた古い値がrdレジスタに書き戻されます。
2.  AMOCAS.D命令は、rs1が指すメモリから8Bのデータをロードし、rdと比較します。等しい場合、rs2をrs1が指すメモリに書き込みます。最終的に、メモリからロードされた古い値がrdレジスタに書き戻されます。
3.  AMOCAS.Q命令は、rs1が指すメモリから16Bのデータをロードし、rdとrd+1を連結したデータと比較します。等しい場合、rs2とrs2+1を連結した16Bのデータをrs1が指すメモリに書き込みます。最終的に、メモリからロードされた古い値の下位8Bがrdレジスタに、上位8Bがrd+1レジスタに書き戻されます。
    -   rs2とrdのレジスタペアについて、ソースオペランドがx0レジスタの場合、レジスタペアの読み取り結果はすべて0になります。デスティネーションレジスタがx0レジスタの場合、レジスタペアの各レジスタは書き込まれません。

## アトミック命令のUop分割

A拡張では、各命令は1つのsta uopと1つのstd uopに分割され、1回のライトバックを行います（ライトバック回数はsta uopの数と同じで、std uopはライトバックを必要としません）。

AMOCASは、命令uopの分割、ディスパッチ、ライトバックにおいて、他のA拡張の命令とは異なります。AMOCAS命令は、ディスパッチ時にメモリに書き込むデータに加えて比較用のデータも提供する必要があるため、1つのAMOCAS命令は複数のstd uop、さらには複数のsta uopに分割されます。

AMOCAS命令は、fuOpTypeを再利用して複数のstd uopまたは複数のsta uopを区別します。fuOpTypeは合計9ビットで、アトミック命令は6ビットしか使用しないため、上位3ビットはuopIdxをマークするために使用されます。

具体的なuop分割ルールは次のとおりです。

1.  **A拡張命令（LR/SCおよび通常のAMO命令を含む）**：staとstdのuopIdxは両方とも0で、それぞれrs1とrs2のデータを運び、AtomicsUnitのrs1およびrs2_lレジスタに格納されます。AtomicsUnitは1回のライトバック操作を行い、ライトバックのuopIdxは0で、ライトバックのpdestはsta uopのpdestと等しくなります。

    ![A拡張アトミック命令のUop分割図](./figure/atomicsUnitAMOUop.svg)

2.  **AMOCAS.WおよびAMOCAS.D命令**：バックエンドは1つのsta uopと2つのstd uopをディスパッチします。

    -   1つのsta uopのuopIdxは0です。
    -   2つのstd uopのuopIdxはそれぞれ0と1で、それぞれrd（比較用データ）とrs2（比較が成功した場合に格納するデータ）を保存し、AtomicsUnitのrd_lおよびrs2_lレジスタに書き込まれます。
    -   最終的に1回のライトバックが行われ、ライトバックのuopIdxは0で、ライトバックのpdestはsta uopのpdestと等しくなります。

    ![AMOCAS.WおよびAMOCAS.D命令のUop分割図](./figure/atomicsUnitAMOCASWUop.svg)

3.  **AMOCAS.Q命令**：バックエンドは2つのsta uopと4つのstd uopをディスパッチします。

    -   2つのsta uopのuopIdxはそれぞれ0と2で、2つのuopのpdestはpdest1とpdest2と記されます。
    -   4つのstd uopのuopIdxは0〜3で、そのうち0番と2番のuopはそれぞれrdの下位と上位を保存し、rd_lとrd_hレジスタに書き込まれます。1番と3番のuopはそれぞれrs2の下位と上位を保存し、rs2_lとrs2_hレジスタに書き込まれます。
    -   最終的に2回のライトバックが行われ、ライトバックのuopIdxはそれぞれ0と2で、pdestはそれぞれpdest1とpdest2で、ライトバックデータはそれぞれメモリからロードされた古い値の下位と上位になります。

    ![AMOCAS.Q命令のUop分割図](./figure/atomicsUnitAMOCASQUop.svg)

## 例外のまとめ
