# Aチャネル要求バッファ RequestBuffer

## 機能説明
- Request Bufferは、一時的にブロックする必要があるAチャネル要求をバッファリングし、同時に解放条件を満たす/ブロック不要なAチャネル要求が先にメインパイプラインに入ることを許可します。
- Request Bufferは、ブロックする必要があるA要求がパイプライン入口を詰まらせるのを防ぎ、それによって後続要求への影響を回避し、キャッシュの処理効率を向上させます。
- 新しく到着したAcquireがMSHRで処理中のプリフェッチ要求と同じアドレスを持つ場合、要求融合を実行でき、Acquireの情報を対応するMSHRに直接渡すことで、MSHRが処理完了後に同時にL1 Acquireに応答できるようになり、Acquireの処理フローを高速化し、ReqBufとMSHRの占有を削減します。

### 特性1：要求融合
RequestBufferが受信したAcquire要求とあるMSHRエントリ内のプリフェッチ要求が同じアドレスを持つ場合、RequestBufferは融合要求（aMergeTask）を対応するMSHRエントリに送信し、そのMSHRエントリはmergeAとしてマークされ、MSHRの関連フィールドが更新されます。

### 特性2：要求受信条件
RequestBuffer入口の要求がどのような状況で受信を許可されるか：
- RequestBufferが満杯でない
- RequestBufferは満杯だが、Acquire要求が前のプリフェッチ要求と融合できる
- RequestBufferは満杯だが、その要求はプリフェッチ要求であり、かつ前に既にAcquire/Prefetch要求がMSHRで処理されている

### 特性3：RequestBufferの割り当て
どの要求がRequestBufferを割り当てるか：
- RequestBufferが満杯でない
- 直接パイプラインにflowできない（すなわちMainPipeまたはあるMSHRエントリとアドレス競合）または、chosenQも発行準備ができている
- 要求融合ができない
  
### 特性4：RequestBufferエントリ内のフィールド
- Rdy：発行/デキュー準備ができているかどうか
- Task：要求自体の情報
- WaitMP：MainPipeのどのステージによってブロックされているか
- WaitMS：どのMSHRエントリによってブロックされているか

### 特性5：RequestBufferの更新と発行方法
- WaitMP（4ビット）：MainPipeはノンブロッキングパイプラインであるため、waitMPは毎サイクル1ビット右シフトし、同時に毎サイクルs1に新しいアドレス競合要求がないかチェックします
  [3] s1、同一セット競合
  [2] s2、同一セット競合
  [1] s3、同一セット競合
  [0] 予約
- WaitMS（16ビット）：MSHRが解放される前のサイクルでwaitMSの対応するビットをリセットします。同時に新しいMSHRエントリが割り当てられた時にアドレス競合（同一セットかつタグ）がないかチェックし、あればwaitMSの対応するビットを設定します
  ワンホットエンコード、各ビットは1つのMSHRを表す
- noFreeWay：同一セットで置換が発生する可能性があるため、[MSHR内の同一セット数 + パイプライン上のS2/S3の同一セット数 >= L2のway数]の場合、現在同一セットのすべてのwayが置換される可能性があることを示します。この時RequestBufからパイプラインへの進入をブロックします。
  s2 + s3 + MSHR >= ways(L2) 
- Rdy条件：以下のすべての条件を満たす時、rdyが高でパイプラインに発行してRequestArbiterに入ることができることを示します
  waitMP + waitMSがすべてゼロにクリアされている
  noFreewayが低
  パイプラインs1ステージに入ろうとしているA/Bチャネル要求にセット競合がない

## 全体ブロック図
![RequestBuf](./figure/RequestBuf.svg)
