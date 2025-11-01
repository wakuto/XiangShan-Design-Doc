# Uncache 処理ユニット Uncache

| 更新日時   | コードバージョン                                                                                                                                             | 更新者                                      | 備考     |
| ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- | -------- |
| 2025.02.26 | [eca6983](https://github.com/OpenXiangShan/XiangShan/blob/eca6983f19d9c20aa907987dff616649c3d204a2/src/main/scala/xiangshan/cache/dcache/Uncache.scala) | [Maxpicca-Li](https://github.com/Maxpicca-Li/) | 初版完了 |
|            |                                                                                                                                                              |                                             |          |

## 機能説明

Uncache は LSQ とバスの橋渡しを行い、uncache アクセスに対するバスへの要求と応答を処理する。現状の Uncache はベクトルアクセス、非アラインアクセス、アトミックアクセスをサポートしない。

Uncache の機能概要は以下のとおり。

1. LSQ から渡される uncache 要求（LoadQueueUncache からの uncache load 要求、および StoreQueue からの uncache store 要求）を受け取る
2. 待機中の uncache 要求を選択してバスに送信し、応答を待ち受けて受信する
3. 処理済みの uncache 要求を LSQ に返却する
4. 格納している uncache store 要求のデータを LoadUnit で実行中の load にフォワードする

Uncache Buffer の構造は現在、エントリとステートが 4 項（項数は可変）あり、全体を表す状態 `uState` を持つ。以下に各項目の詳細を示す。

Uncache のエントリ構造は次のとおり。

* `cmd`: 要求が load か store かを示す。現行版では 0 が load、1 が store。
* `addr`: 要求の物理アドレス。
* `vaddr`: 要求の仮想アドレス。フォワード時に仮想と物理のアドレス一致を判断するために用いる。
* `data`: store が書き込むデータ、または load が読み取るデータ。現状では 64 ビット以内のアクセスのみをサポートする。
* `mask`: 要求のアクセスマスク。1 バイトにつき 1 ビットでデータ有無を示し、計 8 ビット。
* `nc`: 要求が NC アクセスかどうか。
* `atomic`: 要求がアトミックアクセスかどうか。
* `memBackTypeMM`: 要求アドレスが PMA では main memory タイプだが PBMT が NC タイプかどうか。主に L2 Cache の NC 関連ロジックに使用。
* `resp_nderr`: バスが当該要求を処理できるかどうかを Uncache に通知する信号。

Uncache のステート構造は次のとおり。

* `valid`: 項が有効かどうか。
* `inflight`: 1 の場合、当該項の要求はすでにバスへ送信済み。
* `waitSame`: 1 の場合、同じデータブロックをアクセスする他の要求がバッファ内に存在し、かつ送信済みであることを示す。
* `waitReturn`: 1 の場合、当該項の要求はバスから応答を受信済みで、LSQ への返却待ちであることを示す。

Uncache の `uState` は、outstanding を無視した場合の単一要求の状態を表す。

* `s_idle`: 既定の状態
* `s_inflight`: バスに要求を送信済みで、応答を未受信
* `s_wait_return`: 応答を受信済みで、LSQ への返却待ち

状態遷移は下図のとおり。

![ustate 状態遷移の概念図](./figure/Uncache-uState.svg)

### 特性 1: エンキュー処理

(1) 各クロックで LSQ からの要求を最大 1 件処理し、バッファに入れられるかを判定する。可能であれば既存項へのマージか新規項への割り当てかを決定する。入隊動作は以下のいずれかとなる。

1. 新規項を割り当てて valid をセット
   1. 同一ブロックアドレスの項が存在しない場合
2. 新規項を割り当てて valid と waitSame をセット
   1. 同一ブロックアドレスの項が存在し、主要マージ条件を満たすが、副次マージ条件を満たさない場合
3. 既存項にマージ
   1. 同一ブロックアドレスの項が存在し、主要マージ条件と副次マージ条件をともに満たす場合
4. 受け入れ拒否
   1. ubuffer が満杯
   2. 同一ブロックアドレスの項が存在し、主要マージ条件を満たさない場合

ここでブロックアドレス (blockAddr) とは 8 バイト境界のアドレスを指す。主要マージ条件は、新規項と既存項がいずれも NC アクセスで、属性が一致し、マージ後の mask が連続かつ自然整列であり、当該項がそのクロックでバスアクセスを実行中または完了していないこと。副次マージ条件は既存項が有効で、まだバスアクセスを送っておらず、そのクロックでバスアクセスに選択されてもいないことである（いったんバスに送信済みあるいは送信中であれば要求は変更できないため、新規項を割り当て、既存項のバス応答が戻るのを待ってから送信する必要がある）。

新規項を割り当てる場合はエントリ内容を設定する。既存項にマージする場合は mask、data、addr などを更新する。addr 更新時は自然整列を保証する必要がある。

> バスアクセスは順序を保証しない。特に outstanding が有効な場合、複数の uncache アクセスが同時に処理される可能性がある。このため同一アドレスの要求が同時にバス上に存在しないようにし、アクセス順序を保証する必要がある。ゆえに新規項が主要・副次マージ条件を両方満たす場合のみ既存項にマージできる。

(2) 次のクロックで割り当てた Uncache Buffer 項目の ID を返す。LoadQueueUncache または StoreQueue はこの ID を保持し、uncache 応答をマッピングするために用いる。Uncache Buffer はマージ機能を持つため、一つの応答が LoadQueueUncache 内の複数項に対応する可能性がある。

### 特性 2: デキュー処理

そのクロックでバスアクセスを完了した項（`valid` と `waitReturn` が 1）から 1 項を選び、LSQ に返却したうえですべてのステートビットをクリアする。

### 特性 3: バスとのやり取りと outstanding ロジック

バスとのやり取りと outstanding ロジックは以下の 2 部分から構成される。

(1) 要求の発行

outstanding が無効な場合、`uState` が `s_idle` の時のみバスに要求を送信できる。有効な項のうち現在バスに送れるもの（ステートビットで `valid` のみが 1）を選び、バスへ送信する。outstanding が有効な場合は `uState` を無視して項を選択・送信できる。`source` ビットには要求項の ID を設定する。

要求をバスに送信する際は、同一ブロックアドレスを持つ他の項の `waitSame` を設定する必要がある。

(2) 応答の受信

バス応答を受信したら、`source` ビットに基づき該当するバッファ項目を特定し、データを更新して `waitReturn` をセットする。

加えて、同一ブロックアドレスを持つ項の `waitSame` をクリアする。

### 特性 4: フォワードロジック

理論上、フォワードロジックは主に NC アクセスを対象とする。outstanding を有効にすると、uncache NC store が StoreQueue から Uncache Buffer に書き込まれた時点で StoreQueue は項をデキューし、維持しなくなる。この時点から Uncache Buffer が当該 store データをフォワードする役割を担う。Uncache Buffer のエンキューロジックにはマージが存在するため、同一アドレスが同時に現れる場合でも最大 2 項までで、片方は必ず `inflight`、もう片方は必ず `waitSame` となる。StoreQueue は順序デキューのため、前者のデータが古く、後者のデータが新しい。

実装上、uncache NC load が Uncache Buffer にフォワード要求を送ると、既存項のブロックアドレスを比較し、マッチする項が見つかる場合がある。その項はバス送信済みの場合と未送信の場合があり、前者は古いデータ、後者は新しいデータで優先度が高い。第 1 サイクルの `f0` では仮想ブロックアドレスの比較を行い、当該クロックで `forwardMaskFast` を返す。第 2 サイクルの `f1` では物理ブロックアドレスの比較とデータ結合を実施し、結果を返却する。

### 特性 5: フラッシュロジック

フラッシュとは、Uncache Buffer 内のすべての項がバスアクセスを完了し LSQ に返却した後にのみ、新しい項を受け入れられる状態に戻ることを指す。fence・atomic・cmo の発生時、あるいはフォワード時に仮想・物理アドレス不一致が発生した場合、Uncache Buffer をフラッシュする。この際 `do_uarch_drain` がセットされ、新規項を受け付けなくなる。全項目が処理を終えると `do_uarch_drain` がクリアされ、通常の受付を再開する。

## 全体ブロック図

<!-- PLEASE USE svg -->

![ubuffer 全体ブロック図](./figure/Uncache.svg)

## インターフェース時系列

### LSQ インターフェース時系列例

以下は 4 つの uncache アクセスを含む詳細なインターフェース例である。第 5 サイクル以前に m1、m2、m3 を順に受信し、各要求の直後のサイクルで `idResp` を返す。第 6 サイクルでは Uncache が満杯で m4 が停止する。第 9+n サイクルで s1 の処理が完了し書き戻すことで項が解放される。したがって第 10+n サイクルで `io_lsq_req_ready` がアサートされ、m4 が受信される。その後のサイクルで他の uncache アクセス要求が順次書き戻される。
![Uncache と LSQ のインターフェース時系列図](./figure/Uncache-timing-with-lsq.svg)

<!--
{
  signal: [
    {name: 'clk',                     wave: 'p......|.......'},
    {name: 'io_lsq_req_valid',        wave: '0101...|..0....'},
    {name: 'io_lsq_req_ready',        wave: '1....0.|.1.....'},
    {name: 'io_lsq_req_bits_id',      wave: 'x3x456.|..x....', data:['m1','m2','m3','m4']},
    {name: 'io_lsq_idResp_valid',     wave: '0.101.0|..10...'},
    {name: 'io_lsq_idResp_bits_mid',  wave: 'x.3x45x|..6x...', data: ['m1', 'm2', 'm3', 'm4']},
    {name: 'io_lsq_idResp_bits_sid',  wave: 'x.3x45x|..5x...', data: ['s1', 's2', 's3', 's4']},
    {name: 'io_lsq_resp_valid',       wave: '0......|10.1010'},
    {name: 'io_lsq_resp_bits_id',     wave: 'x......|3x.4x5x', data: ['s1', 's2', 's3']},
  ],
  config: { hscale: 1 },
  head: {
    text:'LSQ <=> Uncache',
    tick:1,
    every:1
  },
}
-->

### バス インターフェース時系列例

(1) outstanding が無効な場合、各期間で送信できる uncache 要求は 1 つのみ（`uState` により制御）で、d チャネルからの応答を受信して初めて次の uncache 要求を発行できる。
![Uncache とバスのインターフェース時系列図](./figure/Uncache-timing-with-bus.svg)

<!-- 
{
  signal: [
    {name: 'clk',                           wave: 'p..|.....|...'},
    {name: 'auto_client_out_a_ready',       wave: '1..|.....|...'},
    {name: 'auto_client_out_a_valid',       wave: '010|...10|...'},
    {name: 'auto_client_out_a_bits_source', wave: 'x3x|...4x|...', data: ['s1','s2']},
    {name: 'auto_client_out_d_valid',       wave: '0..|10...|10.'},
    {name: 'auto_client_out_d_bits_source', wave: 'x..|3x...|3x.', data: ['s1', 's2']},
  ],
  config: { hscale: 1 },
  head: {
    text:'Uncache <=> Bus',
    tick:1,
    every:1
  },
}
 -->

(2) outstanding が有効な場合、各期間で複数の uncache アクセスを発行できる（`auto_client_out_a_ready` によって流量制御される）。下図では第 2・3 サイクルで連続して 2 つの要求を送信し、第 6+n サイクルと第 8+n サイクルでそれぞれ結果を受信している。

![outstanding 有効時の Uncache とバスのインターフェース時系列図](./figure/Uncache-timing-with-bus-outstanding.svg)

<!-- 
{
  signal: [
    {name: 'clk',                           wave: 'p..|......'},
    {name: 'auto_client_out_a_ready',       wave: '1..|......'},
    {name: 'auto_client_out_a_valid',       wave: '01.0|.....'},
    {name: 'auto_client_out_a_bits_source', wave: 'x34x|.....', data: ['s1','s2']},
    {name: 'auto_client_out_d_valid',       wave: '0...|1010.'},
    {name: 'auto_client_out_d_bits_source', wave: 'x...|3x4x.', data: ['s1', 's2']},
  ],
  config: { hscale: 1 },
  head: {
    text:'Uncache <=> Bus when outstanding',
    tick:1,
    every:1
  },
}
 -->
