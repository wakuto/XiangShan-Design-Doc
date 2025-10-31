# Uncacheロード処理ユニット LoadQueueUncache

| 更新日 | コードバージョン | 更新者 | 備考 |
| --- | --- | --- | --- |
| 2025.02.26 | [eca6983](https://github.com/OpenXiangShan/XiangShan/blob/eca6983f19d9c20aa907987dff616649c3d204a2/src/main/scala/xiangshan/mem/lsqueue/LoadQueueUncache.scala) | [Maxpicca-Li](https://github.com/Maxpicca-Li/) | 初版完成 |
| | | | |

## 機能説明

uncacheロードアクセス要求に対して、LoadQueueUncacheとUncacheモジュールは、LoadUnitパイプラインとバスアクセスの間の中間ステーションとして機能します。バス側に近いUncacheモジュールは、[Uncache](../Uncache.md "Uncache処理ユニット Uncache")で説明されているように機能します。パイプライン側のコンポーネントであるLoadQueueUncacheは、次のタスクを担当します。

1. LoadUnitパイプラインから渡されたuncacheロード要求を受信します。
2. 準備ができたuncacheロード要求を選択し、Uncache Bufferに送信します。
3. Uncache Bufferから処理済みのuncacheロード要求を受信します。
4. 処理済みのuncacheロード要求をLoadUnitに返します。

構造的に、LoadQueueUncacheには現在4つのUncacheEntryのエントリ（数は設定可能）があり、それぞれが独立して要求を担当し、一連のステータスレジスタを利用して特定の処理フローを制御します。各エントリの割り当てとリサイクルを管理するFreeListがあります。LoadQueueUncacheは主に、4つのエントリ間の新しいエントリ割り当て、要求選択、応答ディスパッチ、デキューなどの包括的なロジックを調整します。

### 特性1：エンキューロジック

LoadQueueUncacheは、LoadUnit 0、1、および2からの要求を受信する責任があります。これらの要求は、MMIO要求またはNC要求のいずれかです。まず、システムは要求をrobIdxによって時系列（最も古いものから最も新しいものへ）に並べ替え、最も早い要求が空きエントリへの割り当てを優先されるようにし、特別な状況下での古いエントリのロールバックによるデッドロックを回避します。処理の条件は、要求が再送されず、例外がなく、システムがFreeListの利用可能な空きエントリから要求に順次エントリを割り当てることです。

LoadQueueUncacheが容量制限に達し、まだエントリが割り当てられていない要求がある場合、システムは最も早い未割り当ての要求をロールバック対象として選択します。

### 特性2：デキューロジック

エントリがUncacheアクセス操作を完了してLoadUnitに返されるか、リダイレクトによってフラッシュされると、エントリはデキューされ、FreeList内のそのエントリのフラグが解放されます。同じサイクルで複数のエントリがデキューされる場合があります。LoadUnitに返される要求は、最初のサイクルで選択され、2番目のサイクルで返されます。

その中で、uncacheリターン要求を処理するために利用可能なLoadUnitポートは事前に設定されています。現在、MMIOはLoadUnit 2にのみリターンし、NCはLoadUnit 1\2にリターンできます。リターンに複数のポートが利用可能な場合、uncacheエントリIDをポート数で割った余りを使用して、各エントリがリターンできるLoadUnitポートを指定し、そのポートの候補エントリからリターンするエントリを選択します。

### 特性3：Uncacheインタラクションロジック

（1）`req`の送信

最初のサイクルで、現在準備ができているuncacheアクセスから1つを選択し、2番目のサイクルでそれをUncache Bufferに送信します。送信された要求は、選択されたエントリのIDをマークし、`mid`と呼びます。正常に受信されたかどうかは、`req.ready`によって判断できます。

（2）`idResp`の受信

送信された要求がUncache Bufferに受け入れられた場合、Uncacheの`idResp`は受け入れ後の次のサイクルで受信されます。この応答には、`mid`と、要求に対してUncache Bufferによって割り当てられたエントリID（`sid`と呼ばれる）が含まれます。LoadQueueUncacheは`mid`を使用して対応する内部エントリを特定し、そのエントリに`sid`を格納します。

（3）`resp`の受信

Uncache Bufferが要求のバスアクセスを完了すると、アクセス結果をLoadQueueUncacheに返します。応答には`sid`が含まれます。Uncache Bufferのマージ機能（詳細なマージロジックは[Uncache](../Uncache.md)を参照）により、1つの`sid`がLoadQueueUncacheの複数のエントリに対応する場合があります。LoadQueueUncacheは`sid`を使用してすべての関連する内部エントリを特定し、アクセス結果をそれらに渡します。

## 全体ブロック図

<!-- svgを使用してください -->

![LoadQueueUncache全体ブロック図](./figure/LoadQueueUncache.svg)

## インターフェースタイミング

### エンキューインターフェースタイミングの例

下の図に示すように、5つの連続するNC要求がLoadUnit 0\1\2を介して順番に入力され、現在のLoadQueueUncacheには4つのエントリしかないと仮定します。したがって、最初の4つの要求は通常、利用可能なエントリに割り当てられます。3番目のサイクルに現れる`r5`は、バッファがいっぱいのためエントリを割り当てることができず、5番目のサイクルでロールバックが発生します。図では、各NC要求がサイクルごとに順番に入力されると仮定していることに注意してください。つまり、`r1` < `r2` < `r3`かつ`r4` < `r5`です。ソートが必要な場合は、ソート結果を`io_req`に順次置き換えるだけで、残りのロジックは同じです。

![LoadQueueUncacheエンキューインターフェースタイミング図](./figure/LoadQueueUncache-timing-enq.svg)

<!-- 
{
  signal: [
    {name: 'clk', wave: 'p.....'},
    {name: 'io_req_0_valid', wave: '01.0..'},
    {name: 'io_req_1_valid', wave: '01.0..'},
    {name: 'io_req_2_valid', wave: '010...'},
    {name: 'io_req_0_bits*robIdx*', wave: 'x36x..', data: ['r1','r4']},
    {name: 'io_req_0_bits*robIdx*', wave: 'x47x..', data: ['r2','r5']},
    {name: 'io_req_0_bits*robIdx*', wave: 'x5x...', data: ['r3']},
    {},
    {name: 'freeList_io_doAllocate_0', wave: '0.1.0.'},
    {name: 'freeList_io_doAllocate_1', wave: '0.10..'},
    {name: 'freeList_io_doAllocate_2', wave: '0.10..'},
    {},
    {name: 'io_rollback_valid', wave: '0...10'},
    {name: 'io_rollback_bits*robIdx*', wave: 'x...7x', data: ['r5']},
  
    // freeListとEntryの更新はまだ描画しない
    // {name: 'freeList_io_canAllocate_0', wave: '01.0|.....'},
    // {name: 'freeList_io_canAllocate_1', wave: '01.0|.....'},
    // {name: 'freeList_io_canAllocate_2', wave: '01.0|.....'},
    // {name: 'freeList_io_allocateSlot_0', wave: 'x34x|.....', data: ['s1','s2']},
    // {name: 'freeList_io_allocateSlot_1', wave: 'x34x|.....', data: ['s1','s2']},
    // {name: 'freeList_io_allocateSlot_2', wave: 'x34x|.....', data: ['s1','s2']},
    // {name: 'entries_0_req_valid', wave: '01.0|.....'},
    // {name: 'entries_1_req_valid', wave: '01.0|.....'},
    // {name: 'entries_2_req_valid', wave: '01.0|.....'},
    // {name: 'entries_3_req_valid', wave: '01.0|.....'},
    // {name: 'entries_0_req_bits*robIdx*', wave: 'x34x|.....', data: ['s1','s2']},
    // {name: 'entries_1_req_bits*robIdx*', wave: 'x34x|.....', data: ['s1','s2']},
    // {name: 'entries_2_req_bits*robIdx*', wave: 'x34x|.....', data: ['s1','s2']},
    // {name: 'entries_3_req_bits*robIdx*', wave: 'x34x|.....', data: ['s1','s2']},
  ],
  config: { hscale: 1 },
  head: {
    text:'LoadUnitからのenq',
    tick:1,
    every:1
  },
}
 -->
