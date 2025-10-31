\newpage
# ロードキュー VirtualLoadQueue

## 機能説明

VirtualLoadQueueは、すべてのロード命令のMicroOpを格納するキューであり、ロード命令間の順序を維持します。これは、ロード命令のROBに似ています。その主な機能は、ロード命令の実行ステータスを追跡することです。

VirtualLoadQueueには、各エントリのロード命令の現在の状態を示すいくつかのステータスビットがあります。

* allocated：エントリにロードが割り当てられているかどうか。ロード命令のライフサイクルを決定するために使用されます。
* isvec：命令がベクトルロード命令であるかどうか。
* committed：エントリがコミットされたかどうか。

### 特性1：エンキュー

* エンキュータイミング：命令ディスパッチフェーズ中に、ロード命令はディスパッチキューからロードキューに送信され、Virtual Load Queueは命令情報を格納するために使用されます。
* パイプライン書き戻しタイミング：ロードがIQから発行され、ロードパイプラインを通過した後、パイプラインのステージS3に到達すると、このロードの実行情報がロードキューにフィードバックされます。
* パイプライン書き戻し情報：dcacheがヒットしたかどうか、ロードが正常にデータを取得したかどうか（dcacheがミスしたが、sbufferおよびストアキューから完全なデータを転送できた場合を含む）、TLBミス、ロードを再送する必要があるかどうか、ロードで例外が発生したかどうか、ロードがMMIO空間にあるかどうか、ベクトルロードであるかどうか、書き込み後読み取りまたは読み取り後読み取り違反が発生したかどうか、およびdcacheバンク競合があったかどうかが含まれます。

### 特性2：デキュー

* デキュータイミング：割り当てられたエントリ（allocatedがハイ）がキューの先頭に到達し、allocatedとcommittedの両方が1である場合、デキューの対象となります。ベクトルロードの場合、各要素がコミットされている必要があります。

## 全体ブロック図
<!-- svgを使用してください -->
![VirtualLoadQueue全体ブロック図](./figure/VirtualLoadQueue.svg)

## インターフェースタイミング

### エンキュー要求受信のタイミング例

![VirtualLoadQueue-enqueue](./figure/VirtualLoadQueue-enqueue.svg){#fig:VirtualLoadQueue-enqueue width=80%}

io_enq_canAcceptとio_enq_sqcanAcceptがハイの場合、ディスパッチ命令を受け入れることができることを示します。io_enq_req_*_validがハイの場合、VirtualLoadQueueへの命令の実際のディスパッチを示し、ディスパッチ情報にはROBの位置、VirtualLoadQueueの位置、ベクトル命令要素の数などが含まれます。ディスパッチ後、対応するallocated信号が立ち上がり、enqPtrExtはディスパッチされた要求の数に基づいて更新されます。

### パイプライン書き戻しタイミングの例

![VirtualLoadQueue-writeback](./figure/VirtualLoadQueue-writeback.svg){#fig:VirtualLoadQueue-writeback width=80%}

io_ldin_*_validがハイの場合、ロードパイプラインのs3ステージがlqに書き戻すことを示し、具体的な内容はio_ldin_* _bits_*です。allocated_5は、lqの5番目のエントリが割り当てられているかどうかを示します。updateAddrValidがアサートされ、リプレイがない場合、committed_5は次のサイクルでハイになります。allocatedとcommittedの両方がハイであることは、エントリをデキューできることを示します。書き戻されるエントリごとにテールポインタが1つインクリメントされます。
