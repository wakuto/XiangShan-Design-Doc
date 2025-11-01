# ベクトルロード分割ユニット VLSplit

## 機能説明

ベクトルロード命令のuopを受け入れて処理します。Uopを分割し、Uopのベースアドレスに対するオフセットを計算し、スカラメモリアクセスパイプラインの制御信号を生成します。VLSplitは、VLSplitPipelineとVLSplitBufferの2つの実装モジュールに大別されます。

### 特性1：VLSplitPipelineはuopの二次デコードを実行

ベクトルロード命令の分割パイプライン。ベクトルロード発行キューから発行されたベクトルロード命令のUopを受け入れます。パイプラインでより詳細なデコードとマスクおよびアドレスオフセットの計算を行った後、VLSplitBufferに送信します。一方、VLSplitPipelineはデコード結果に基づいてVLMergeBufferのエントリも要求します。

VLSplitPipelineは2つのパイプラインステージで構成されています。

**S0：**

- 入力されたUop情報に基づいて、より詳細なデコードを実行します。
- 命令タイプに基づいてalignedTypeを生成し、alignedTypeを使用してロードパイプラインのメモリアクセス幅を示します。
- 命令タイプに基づいてpreIsSplit信号を生成します。preIsSplit信号が高い場合は、ユニットストライド命令ではないことを示します。
- vm、emul、lmul、eew、sewなどの命令タイプと情報に基づいて、このUopのマスクを生成します。
- 後続のバックエンドデータマージと書き戻しのために、このUopのVdIdxを計算します。順序不同実行のため、同じ命令のUopが連続して実行されるとは限らないため、このステージでは命令タイプ、emul、lmul、およびuopidxに基づいてVdIdxを計算します。

**S1：**

- UopOffsetとStrideを計算します。
- このUopに必要なFlowNumを計算します。ここで、VMergeBufferに送信されるFlowNumは、VSplitBufferに送信されるものとは異なります。MergeBufferのFlowNumは、このUopがすべての有効なメモリアクセスを完了したかどうかを判断するために使用され、VSplitBufferで使用されるFlowNumは分割に必要です。
- VLMergeBufferエントリを要求します。各Uopは1つのエントリを要求します。
- VLSplitBufferに情報を送信します。

**マスク計算：**

- まず、vm、v0、vstart、およびevlに基づいて、このベクトルロード命令を表すSrcMaskを計算して生成します。ここで、evlは有効ベクトル長であり、ベクトルロード命令の種類によってevlの計算方法が異なります。
    - ロードホール命令の場合、evl = NFIELDS*VLEN/EEWです。
    - ロードユニットストライドマスク命令の場合、evl=ceil(vl/8)です。
	- 上記2種類以外のベクトルロード命令の場合、evl = vlです。
  
- 次に、[この命令の現在のUopより前のすべてのUopのFlowNum]と[現在のUopを含むすべてのUopのFlowNum]、および[現在のUopより前のすべてのVdのFlowNum]を使用して、実際に使用されるFlowMaskを計算します。ここでは、ロードインデックス付きの特殊性により、インデックス付き命令の$signed(emul) > $signed(lmul)の場合、同じVdIdxを持つUopのFlowNumがVdIdx内でオフセットされるようにする必要があります。以下に例を示します。
	- まず、ベクトルvluxei命令の次の構成を想定します。
        - vsetvli t1,t0,e8,m1,ta,ma lmul = 1
        - vluxei16.v v2,(a0),v8 emul = 2
        - vl = 9, v0 = 0x1FF
  
    - この構成では、$signed(emul) > $signed(lmul)であるため、実際には2つのUopが生成されます。これは、インデックスを2つのベクトルレジスタからフェッチする必要があることを示しますが、両方のUopの宛先レジスタは同じVdです。つまり、2つのUopのVdIdxは同じである必要があり、同じターゲットレジスタに書き込まれる必要があります。したがって、ここでは次の結果が生成されます。
        - uopIdxInField = 0, vdIdxInField = 0, flowMask = 0x00FF, toMergeBuffMask = 0x01FF
        - uopIdxInField = 1, vdIdxInField = 0, flowMask = 0x0001, toMergeBuffMask = 0x01FF
        - uopIdxInField = 0, vdIdxInField = 0, flowMask = 0x0000, toMergeBuffMask = 0x0000
        - uopIdxInField = 0, vdIdxInField = 0, flowMask = 0x0000, toMergeBuffMask = 0x0000
  
    - 各Uopについて計算されたFlowNumは8です。詳細については、VSplit.scalaを参照してください。
  
### 特性2：VLSplitBufferはVLSplitPipelineによって生成された二次デコード情報に基づいて分割

VLSplitBufferは、VLSplitPipelineから関連情報を受信し、分割する必要のあるベクトルロードUopをキャッシュする単一エントリのバッファです。

VLSplitBufferは、Uopの詳細に基づいてUopをスカラロードパイプラインに送信できる複数の情報に分割し、実際のメモリアクセスのためにスカラロードパイプラインにディスパッチします。


**エンキューロジック：**

VLSplitBufferは、VLSplitPipelineからエントリ要求と関連情報を受け入れます。VLSplitBufferに空きエントリがある場合、各要求に1つのVLSplitBufferエントリを割り当て、対応するエントリのValidを設定します。

**デキューロジック：**

VLSplitBufferは、VLSplitPipelineからエントリ要求と関連情報を受け入れます。VLSplitBufferに空きエントリがある場合、各要求に1つのVLSplitBufferエントリを割り当て、対応するエントリのValidを設定します。


**分割：**

- VLSplitBufferは、命令タイプに基づいて分割します。
- ユニットストライド命令の場合：
    - ベースアドレスが整列している（キャッシュラインをまたがない）場合、一度に128ビットにアクセスします。
    - ベースアドレスが整列していない（キャッシュラインをまたぐ）場合、分割して2回の128ビットメモリアクセスを開始します。

- 他のベクトルロード命令の場合、命令のセマンティクスの要件に従って要素ごとに分割し、要素ごとにメモリアクセスを行います。
- 各分割では、分割後に生成された関連情報を実際のメモリアクセスのためにスカラロードパイプラインに送信します。
- 分割はsplitIdxカウンタに基づいて判断されます。splitIdxは、現在のエントリがすでに実行した分割の数を示します。splitIdxが必要な分割数より小さく、スカラロードパイプラインに送信できる場合、1回の分割が実行され、各分割でsplitIdxカウンタの値が増加します。splitIdxが必要な分割数以上になると、分割は終了し、エントリはデキューされ、splitIdxカウンタはゼロにリセットされます。

**アドレス計算：**

- 分割時には、スカラロードパイプラインに送信される関連情報を計算する必要もあります。主に、各分割後にメモリアクセスを実行する必要がある仮想アドレスを計算します。
- 仮想アドレスは、命令タイプの分割方法によって計算方法が異なります。

- ユニットストライド命令の場合：
    - ベースアドレスが整列している（キャッシュラインをまたがない）場合、128ビットの整列アクセスを1回直接実行するだけで十分です。
    - ベースアドレスが整列していない（キャッシュラインをまたぐ）場合、分割して2つの連続した128ビット整列アドレスを使用してアクセスします。

- 他のベクトルロード命令の場合、命令のセマンティクスの要件に従って要素ごとに分割し、仮想アドレスは要素とセマンティクスに基づいて計算されます。


**リダイレクションと例外処理：**
リダイレクション信号が到着すると、リダイレクション関連情報に基づいてVLSplitBufferの関連エントリがフラッシュされます。

### 特性3：VLMergeBufferのThreshold信号に基づくバックプレッシャ {#sec:VLS-THRESHOLD}

[@sec:VLM-THRESHOLD] [しきい値バックプレッシャ](VLMergeBuffer.md)を参照してください。
VLMergeBufferから受信すると、VLSplitPipelineはエンキュー要求をバックプレッシャし、バックエンドが新しいuopを送信するのを防ぎます。VLMergeBufferがしきい値バックプレッシャを解除するまで。

## 全体ブロック図

単一モジュールのため、ブロック図はありません。

## 主要ポート

VLSplitの外部インターフェースのみをリストし、内部のVLSplitPipeとVLSplitBufferのインターフェースは含みません。

| ポート名           | 方向 | 説明                             |
| ------------------ | :--- | :------------------------------- |
| `redirect`         | In   | リダイレクトポート               |
| `in`               | In   | Issue Queueからのuop発行を受け取る |
| `toMergeBuffer.req`| Out  | MergeBufferエントリを要求        |
| `toMergeBuffer.resp`| In   | MergeBufferの応答                |
| `out`              | Out  | メモリアクセス要求をLoad Unitに送信 |
| `threshold`        | In   | VLMergeBufferのしきい値信号を受信 |

## インターフェースタイミング

インターフェースのタイミングは比較的単純なため、テキストによる説明のみを提供します。

| ポート名           | 説明                                                       |
| ------------------ | :--------------------------------------------------------- |
| `redirect`         | Validを持つ。データはValidと共に有効                       |
| `in`               | Valid、Readyを持つ。データはValid && readyと共に有効       |
| `toMergeBuffer.req`| Valid、Readyを持つ。データはValid && readyと共に有効       |
| `toMergeBuffer.resp`| Validを持つ。データはValidと共に有効                       |
| `out`              | Valid、Readyを持つ。データはValid && readyと共に有効       |
| `threshold`        | Validを持たない。データは常に有効と見なされ、対応する信号が発生すると応答する |
