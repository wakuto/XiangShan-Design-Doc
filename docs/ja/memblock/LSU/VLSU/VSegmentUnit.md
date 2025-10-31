```markdown
# ベクトルセグメントメモリアクセス命令処理ユニット VSegmentUnit

## 機能説明

本体は8エントリのキューで、各エントリには128ビットのアドレスレジスタ、128ビットのデータレジスタ、インデックス/ストライドアレジスタ、および異なるuopの物理レジスタ番号、書き込みイネーブル、uopidxなどの情報を格納するレジスタがあります。さらに、命令全体のデコード情報を格納するレジスタもあります。内部ではステートマシンを使用して、セグメントの順序に従って分割を実現します。

VSegmentUnit.scalaにはコードと組み合わせたコメントが記述されており、コメントとコードを合わせて読むことで、SegmentUnitの関連ロジックを理解できます。

セグメント命令の実行時、パイプラインのアウトオブオーダーバックエンドは、先行する命令がすべて実行完了し、後続の命令がパイプラインに入らないことを保証する必要があります（アトミック命令の待機メカニズムに類似）。同時に、命令のuopが分割順にSegmentUnitに入ることを保証する必要があります。このとき、SegmentUnitはセグメント命令の順序を保証できます。

### 特性 1：セグメント命令の分割

![alt text](./figure/VSegment-split.png)

- segmentIdx：セグメントのシーケンス番号、segmentIdx <= vl。現在どのセグメントに送信しているかを示し、データの選択やマージにも使用されます。
- fieldIdx：フィールドのシーケンス番号、現在のセグメントの送信が完了したかどうかを示します。fieldIdx < nfields。
- fieldOffset：同じセグメント内の各要素の相対オフセット。1の累算器として実装されます。
- segmentOffset：異なるセグメント間のオフセットを記録します。ストライド命令の場合はストライドを単位とする累算器、ユニットストライドの場合はnfield*eewを単位とする累算器、インデックスの場合はsegmentIdxに対応するインデックスレジスタ要素です。
- vaddr = baseaddr + (fieldIdx << eew) + segmentOffset

上の図はキューポインタのジャンプ例で、lmul=1、nf=2、vl=16の構成での例を示しています。segmentIdxは現在分割中のセグメントを指し、SplitPtrは分割中のフィールドレジスタを指します。
上の図ではsegmentIdxが0、splitPtrが0で、最初のuopの最初の要素を分割してメモリアクセスした後、SplitPtr + nfとなり、segment0のfield1要素のメモリアクセスを行います。
field2のメモリアクセスが完了すると、現在のセグメントの要素アクセスが終了し、segmentIdx+1となり、同時にSplitPtrは次のセグメントのfield0があるレジスタにジャンプします。
segmentIdxが8にインクリメントされると、field0のレジスタグループにとっては次のuopの最初の要素に対応します（上の図の各フィールドレジスタの2番目）。
segmentIdx=16で、field2要素のメモリアクセスが完了すると、命令の実行が終了します。
セグメントインデックスについては、インデックスレジスタを選択するためのポインタもあり、実装方法は上記の同じフィールドの異なるレジスタを選択する方法と類似しています。

### 特性 2：fault only firstのVLレジスタ変更uopの単独書き戻し

fault only first命令の場合、VSegmentUnitはVfofBufferを使用して追加のuopを書き戻しません。
代わりに、s_fof_fix_vlに遷移してVLレジスタを変更するuopを書き戻します。

### 特性 3：セグメントの非整列メモリアクセスのサポート

VSegmentUnit命令は、MisalignBufferを介さずに、自身で非整列メモリアクセスを単独で実行します。
VSegmentUnit自身が非整列命令の分割とデータのマージを行います。

## 状態遷移図

![alt text](./figure/VSegmentUnit-FSM.svg)

**状態説明**

|                      状態 | 説明                                                             |
| ------------------------: | :--------------------------------------------------------------- |
|                    s_idle | SegmentUnit uopの進入を待機                                      |
|       s_flush_sbuffer_req | sbufferをフラッシュ                                              |
| s_wait_flush_sbuffer_resp | SbufferとStoreQueueが空になるのを待機                            |
|                 s_tlb_req | DTLBを検索                                                       |
|           s_wait_tlb_resp | DTLBの応答を待機                                                 |
|                      s_pm | 実行権限をチェック                                               |
|               s_cache_req | DCacheの読み取りを要求                                           |
|              s_cache_resp | DCacheが応答                                                     |
|     s_misalign_merge_data | 非整列Load Dataをマージ                                          |
|    s_latch_and_merge_data | 各要素のDataを完全なuop単位のDataにマージ                        |
|               s_send_data | Sbufferにデータを送信                                            |
|         s_wait_to_sbuffer | Sbufferへの送信パイプラインステージがクリアされるのを待機、つまり実際にSbufferに送信されるまで |
|                  s_finish | この命令の実行が完了し、uop単位でバックエンドに書き戻しを開始      |
|              s_fof_fix_vl | fault only first命令のデータuopが書き戻され、VLレジスタを変更するuopを書き戻す |

## デコード例

### セグメント Unit-Stride/Stride

unit-strideは、stride = eew * nfのストライド命令として処理されます。
この種の命令で使用されるオフセットレジスタはスカラレジスタで、uopの数はデータレジスタの数に依存するため、uopの分割数 = emul * nfとなります。
例えば、emul = 2、nf = 4の場合、uopの番号は次のようになります：
uopIdx = 0、ベースアドレスrs1、ストライドrs2、デスティネーションレジスタvd
uopIdx = 1、ベースアドレスrs1、ストライドrs2、デスティネーションレジスタvd+1
uopIdx = 2、ベースアドレスrs1、ストライドrs2、デスティネーションレジスタvd+2
...
uopIdx = 7、ベースアドレスrs1、ストライドrs2、デスティネーションレジスタvd+7

### セグメント Index

- 分割数：Max（lmul*nf、emul）。最初のフィールドのレジスタグループから順に分割を開始することを保証する必要があります。

- 例：emul=4、lmul=2、nf=2の場合、uopの分割は次のようになります：
    - uopidx=0、ベースアドレスsrc、オフセットvs2、デスティネーションレジスタvd
    - uopidx=1、ベースアドレス（dontCare）、オフセットvs2+1、デスティネーションレジスタvd+1
    - uopidx=2、ベースアドレス（dontCare）、オフセットvs2+2、デスティネーションレジスタvd+2
    - uopidx=3、ベースアドレス（dontCare）、オフセットvs2+3、デスティネーションレジスタvd+3

- 例：emul=2、luml=1、nf=3の場合、uopの分割は次のようになります：
    - uopidx=0、ベースアドレスsrc、オフセットvs2、デスティネーションレジスタvd
    - uopidx=1、ベースアドレス（dontCare）、オフセットvs2+1、デスティネーションレジスタvd+1
    - uopidx=2、ベースアドレス（dontCare）、オフセット（dontCare）、デスティネーションレジスタvd+2

- 例：emul=8、lmul=1、nf=8の場合、uopの分割は次のようになります：
    - uopidx=0、ベースアドレスsrc、オフセットvs2、デスティネーションレジスタvd
    - uopidx=1、ベースアドレス（dontCare）、オフセットvs2+1、デスティネーションレジスタvd+1
    - uopidx=2、ベースアドレス（dontCare）、オフセットvs2+2、デスティネーションレジスタvd+2
    - uopidx=3、ベースアドレス（dontCare）、オフセットvs2+3、デスティネーションレジスタvd+3
    - uopidx=4、ベースアドレス（dontCare）、オフセットvs2+4、デスティネーションレジスタvd+4
    - uopidx=5、ベースアドレス（dontCare）、オフセットvs2+5、デスティネーションレジスタvd+5
    - uopidx=6、ベースアドレス（dontCare）、オフセットvs2+6、デスティネーションレジスタvd+6
    - uopidx=7、ベースアドレス（dontCare）、オフセットvs2+7、デスティネーションレジスタvd+7

## 主要ポート

|                 | 方向   | 説明                                                    |
| --------------: | :----- | :------------------------------------------------------ |
|              in | In     | Issue Queueからのuop発行を受信                          |
|    uopwriteback | In     | 実行完了したuopをバックエンドに書き戻す                 |
|         rdcache | In/Out | DCache要求/応答                                         |
|         sbuffer | Out    | Sbuffer書き込み要求                                     |
| vecDifftestInfo | Out    | sbuffer内のDifftestStoreEventに必要な情報               |
|            dtlb | In/out | DTLB読み書き要求/応答                                   |
|         pmpResp | In     | PMPからのアクセス権限情報を受信                         |
|   flush_sbuffer | Out    | sbufferフラッシュ要求                                   |
|        feedback | Out    | Issue Queueモジュールへのフィードバック                 |
|        redirect | In     | リダイレクトポート                                      |
|   exceptionInfo | Out    | Exception情報を出力し、MemBlock内の書き戻し例外情報の仲裁に参加 |
|  fromCsrTrigger | In     | CSRからのTrigger関連データを受信                        |

## インターフェースタイミング

インターフェースのタイミングは比較的単純なため、テキストでの説明のみとします。
|                 | 説明                                               |
| --------------: | :------------------------------------------------- |
|              in | Valid、Readyあり。データはValid && ready時に有効     |
|    uopwriteback | Valid、Readyあり。データはValid && ready時に有効     |
|         rdcache | Valid、Readyあり。データはValid && ready時に有効     |
|         sbuffer | Valid、Readyあり。データはValid && ready時に有効     |
| vecDifftestInfo | sbufferポートと同時に有効                          |
|            dtlb | Valid、Readyあり。データはValid && ready時に有効     |
|         pmpResp | Valid、Readyあり。データは有効時に有効             |
|   flush_sbuffer | Validあり。データはValid時に有効                     |
|        feedback | Validあり。データはValid時に有効                     |
|        redirect | Validあり。データはValid時に有効                     |
|   exceptionInfo | Validあり。データはValid時に有効                     |
|  fromCsrTrigger | Validなし。データは常に有効と見なされ、対応する信号が発生すると即座に応答 |

```
