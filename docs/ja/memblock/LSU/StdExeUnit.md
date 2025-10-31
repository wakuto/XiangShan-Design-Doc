# Storeデータ実行ユニット StdExeUnit

## 機能説明

スカラーストア命令データパイプライン。StoreQueueの対応する位置にストアデータを書き込むために使用されます。

## 全体ブロック図
![stdExeUnit全体ブロック図](./figure/LSU-StdExeUnit.svg){#fig:LSU-StdExeUnit}

## インターフェースタイミング

### インターフェースタイミングの例

![stdExeUnit有効要求インターフェースタイミング図](./figure/LSU-StdExeUnit-Timing.svg){#fig:LSU-StdExeUnit-Timing}

図\ref{fig:LSU-StdExeUnit-Timing}に示すように、io_ooo_to_mem_issueStd_0_readyとio_ooo_to_mem_issueStd_0_validの両方がハイになった後のハンドシェイクの後、データがio_ooo_to_mem_issueStd_0_bits_src_0である有効な書き込み要求が受信されます。上記の例は、3番目のクロックサイクルで、データがStoreQueueのsqIdx0エントリに書き込まれ、データがsrc0であることを示しています。4番目のクロックサイクルで、io_ooo_to_mem_issueStd_0_readyがローになり、その時点でデータはStoreQueueに書き込まれません。この状況は通常、ベクトルストア命令がStoreQueueにデータを書き込もうとするときに発生します。
