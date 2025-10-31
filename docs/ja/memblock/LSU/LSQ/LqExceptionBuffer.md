\newpage
# ロード例外バッファ LqExceptionBuffer

## 機能説明

LqExceptionBufferは、ロード命令によって生成された例外を追跡するために使用され、3つのソースがあります。

* LDU s3からのスカラロード命令例外
* vlMergeBufferからのベクトルロード命令例外
* LoadUncacheBufferからのMMIO非データ例外

robIdxに基づいて例外を引き起こした最も古い命令の仮想アドレス出力を選択します。内部には2ステージのパイプラインがあります。最初のステージはLDUのs3フェーズ中に出力された情報をキャッシュし、2番目のサイクルでrobIdxに基づいて例外を引き起こした最も古い命令を選択し、その仮想アドレスを出力します。

リダイレクション中、LqExceptionBufferにキャッシュされた命令のrobIdxに基づいてフラッシュするかどうかを決定します。

## 全体ブロック図
<!-- svgを使用してください -->
![LqExceptionBufferの全体ブロック図](./figure/LqExceptionBuffer.svg)
