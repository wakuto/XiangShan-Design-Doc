# ベクトルセグメントメモリアクセス命令処理ユニット VSegmentUnit

## 機能説明

本体は 8 エントリのキューで構成され、各エントリには 128 ビットのアドレスレジスタ、128 ビットのデータレジスタ、index/stride レジスタのほか、異なる uop の物理レジスタ番号・書き込みイネーブル・uopidx などを保持するレジスタが備わっています。さらに、1 本の命令に対応するデコード情報を保持するレジスタもあり、内部のステートマシンがセグメント順に従って分割処理を進めます。

`VSegmentUnit.scala` にはコードと対応したコメントが記載されているため、コメントとコードを合わせて読むことで SegmentUnit のロジックを把握できます。

Segment 命令を実行する際は、パイプラインのアウト・オブ・オーダーバックエンドが「先行命令がすべて完了し、後続命令がパイプラインに入らない」ことを保証する必要があります（アトミック命令の待機機構に類似）。同時に、命令に含まれる uop が分割順に SegmentUnit へ入るよう保証する必要があり、この条件下で SegmentUnit は Segment 命令の順序を維持できます。

### 特性 1：Segment 命令の分割

![alt text](./figure/VSegment-split.png)

- segmentIdx：Segment のシーケンス番号。segmentIdx <= vl。現在どの Segment を処理しているかを示し、データの選択やマージにも利用される。
- fieldIdx：field のシーケンス番号。現在の Segment の送信が完了したかどうかを示す。fieldIdx < nfields。
- fieldOffset：同じ Segment 内の各要素の相対オフセット。1 を加算していく累算器として実装される。
- segmentOffset：異なる Segment 間のオフセット。stride 命令では stride を単位とする累算器、unit-stride では nfield * eew を単位とする累算器、index では segmentIdx に対応するインデックスレジスタ要素を指す。
- vaddr = baseaddr + (fieldIdx << eew) + segmentOffset

図は lmul=1、nf=2、vl=16 の構成でのキューポインタ遷移例です。segmentIdx は分割中の Segment を指し、SplitPtr は分割中の field レジスタを指します。segmentIdx=0、splitPtr=0 では最初の uop の最初の要素を分割してメモリアクセスした後、SplitPtr が nf だけ進み、segment0 の field1 をアクセスします。field2 のアクセスが完了するとその Segment の処理が終わり、segmentIdx+1 に進むと同時に SplitPtr は次の Segment の field0 を保持するレジスタへジャンプします。segmentIdx が 8 になると field0 のレジスタ群にとっては次の uop の先頭要素になり、segmentIdx=16 で field2 のアクセスを終えると命令の実行が完了します。Segment Index の場合はインデックスレジスタを選択するポインタもあり、同一 field の異なるレジスタを選択する仕組みと同様に実装されます。

### 特性 2：fault only first 命令の VL レジスタ更新 uop の単独書き戻し

fault only first 命令では、VSegmentUnit は VfofBuffer を利用せずに追加 uop を書き戻します。代わりに状態 s_fof_fix_vl へ遷移し、VL レジスタを更新する uop を書き戻します。

### 特性 3：Segment の非整列メモリアクセス対応

VSegmentUnit の命令は MisalignBuffer を介さず、自身で非整列メモリアクセスを実行します。VSegmentUnit 自身が非整列命令の分割とデータのマージを担当します。

## 状態遷移図

![alt text](./figure/VSegmentUnit-FSM.svg)

**状態説明**

|                      状態 | 説明                                                             |
| ------------------------: | :--------------------------------------------------------------- |
|                    s_idle | SegmentUnit uop の進入を待機                                     |
|       s_flush_sbuffer_req | sbuffer をフラッシュ                                              |
| s_wait_flush_sbuffer_resp | Sbuffer と StoreQueue が空になるのを待機                         |
|                 s_tlb_req | DTLB を検索                                                       |
|           s_wait_tlb_resp | DTLB の応答を待機                                                 |
|                      s_pm | 実行権限をチェック                                               |
|               s_cache_req | DCache の読み取りを要求                                           |
|              s_cache_resp | DCache が応答                                                     |
|     s_misalign_merge_data | 非整列 Load Data をマージ                                        |
|    s_latch_and_merge_data | 各要素の Data を uop 粒度の Data にマージ                        |
|               s_send_data | Sbuffer にデータを送信                                            |
|         s_wait_to_sbuffer | Sbuffer への送信段がクリアされるのを待機、すなわち Sbuffer へ実際に送信されるまで |
|                  s_finish | 命令の実行が完了し、uop 粒度でバックエンドへ書き戻し開始         |
|              s_fof_fix_vl | fault only first 命令のデータ uop を書き戻し、VL レジスタ更新 uop を書き戻す |

## デコード例

### Segment Unit-Stride/Stride

unit-stride は stride = eew * nf の stride 命令として扱われます。この種の命令で利用するオフセットレジスタはスカラレジスタであり、uop の個数はデータレジスタ数に依存するため、uop の分割数は emul * nf になります。例えば emul = 2、nf = 4 のとき、uop は次のように編成されます。
uopIdx = 0、ベースアドレス rs1、ストライド rs2、デスティネーションレジスタ vd
uopIdx = 1、ベースアドレス rs1、ストライド rs2、デスティネーションレジスタ vd+1
uopIdx = 2、ベースアドレス rs1、ストライド rs2、デスティネーションレジスタ vd+2
……
uopIdx = 7、ベースアドレス rs1、ストライド rs2、デスティネーションレジスタ vd+7

### Segment Index

- 分割数は Max（lmul * nf, emul）。最初の field のレジスタ群から順序どおりに分割を開始する必要があります。

- 例：emul=4、lmul=2、nf=2 の場合、uop は次のように分割されます。
    - uopidx=0、ベースアドレス src、オフセット vs2、デスティネーションレジスタ vd
    - uopidx=1、ベースアドレス（dontCare）、オフセット vs2+1、デスティネーションレジスタ vd+1
    - uopidx=2、ベースアドレス（dontCare）、オフセット vs2+2、デスティネーションレジスタ vd+2
    - uopidx=3、ベースアドレス（dontCare）、オフセット vs2+3、デスティネーションレジスタ vd+3

- 例：emul=2、lmul=1、nf=3 の場合、uop は次のように分割されます。
    - uopidx=0、ベースアドレス src、オフセット vs2、デスティネーションレジスタ vd
    - uopidx=1、ベースアドレス（dontCare）、オフセット vs2+1、デスティネーションレジスタ vd+1
    - uopidx=2、ベースアドレス（dontCare）、オフセット（dontCare）、デスティネーションレジスタ vd+2

- 例：emul=8、lmul=1、nf=8 の場合、uop は次のように分割されます。
    - uopidx=0、ベースアドレス src、オフセット vs2、デスティネーションレジスタ vd
    - uopidx=1、ベースアドレス（dontCare）、オフセット vs2+1、デスティネーションレジスタ vd+1
    - uopidx=2、ベースアドレス（dontCare）、オフセット vs2+2、デスティネーションレジスタ vd+2
    - uopidx=3、ベースアドレス（dontCare）、オフセット vs2+3、デスティネーションレジスタ vd+3
    - uopidx=4、ベースアドレス（dontCare）、オフセット vs2+4、デスティネーションレジスタ vd+4
    - uopidx=5、ベースアドレス（dontCare）、オフセット vs2+5、デスティネーションレジスタ vd+5
    - uopidx=6、ベースアドレス（dontCare）、オフセット vs2+6、デスティネーションレジスタ vd+6
    - uopidx=7、ベースアドレス（dontCare）、オフセット vs2+7、デスティネーションレジスタ vd+7

## 主要ポート

|                 | 方向   | 説明                                                    |
| --------------: | :----- | :------------------------------------------------------ |
|              in | In     | Issue Queue からの uop 発行を受信                        |
|    uopwriteback | In     | 実行完了した uop をバックエンドへ書き戻す                |
|         rdcache | In/Out | DCache 要求/応答                                         |
|         sbuffer | Out    | Sbuffer 書き込み要求                                     |
| vecDifftestInfo | Out    | sbuffer 内の DifftestStoreEvent に必要な情報             |
|            dtlb | In/Out | DTLB 読み書き要求/応答                                   |
|         pmpResp | In     | PMP からのアクセス権限情報を受信                         |
|   flush_sbuffer | Out    | sbuffer フラッシュ要求                                   |
|        feedback | Out    | Issue Queue モジュールへのフィードバック                 |
|        redirect | In     | リダイレクトポート                                      |
|   exceptionInfo | Out    | Exception 情報を出力し、MemBlock 内で書き戻し例外情報を仲裁 |
|  fromCsrTrigger | In     | CSR からの Trigger 関連データを受信                      |

## インターフェースタイミング

インターフェースタイミングは比較的単純なため、以下ではテキストで説明します。
|                 | 説明                                               |
| --------------: | :------------------------------------------------- |
|              in | Valid、Ready を備える。データは Valid && ready 時に有効 |
|    uopwriteback | Valid、Ready を備える。データは Valid && ready 時に有効 |
|         rdcache | Valid、Ready を備える。データは Valid && ready 時に有効 |
|         sbuffer | Valid、Ready を備える。データは Valid && ready 時に有効 |
| vecDifftestInfo | sbuffer ポートと同時に有効                          |
|            dtlb | Valid、Ready を備える。データは Valid && ready 時に有効 |
|         pmpResp | Valid、Ready を備える。データは Valid 時に有効       |
|   flush_sbuffer | Valid を備える。データは Valid 時に有効               |
|        feedback | Valid を備える。データは Valid 時に有効               |
|        redirect | Valid を備える。データは Valid 時に有効               |
|   exceptionInfo | Valid を備える。データは Valid 時に有効               |
|  fromCsrTrigger | Valid を持たない。データは常に有効とみなし、信号発生時に即応 |
