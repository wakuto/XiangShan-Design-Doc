# ライトバックキュー WritebackQueue

## 機能説明

ライトバックキューには18個のWritebackEntryアイテムが含まれており、TL-CのCチャネルを介してL2キャッシュに置換ブロックを書き戻す（リリース）こと、およびプローブリクエストに応答する（ProbeAck）ことを担当します。

### 特徴1：WritebackQueueエントリの割り当てと拒否

タイミングの都合上、wbqが満杯の場合、新しいリクエストは拒否されます。wbqが満杯でない場合、すべてのリクエストが受け入れられ、新しいリクエストには空のエントリが割り当てられます。現在のバージョンでは、WritebackQueueでのリクエストのマージはサポートされなくなりました。

### 特徴2：リクエストのブロッキング条件

TileLink仕様では、同時トランザクションに制限が課されており、マスターが保留中のグラント（つまり、GrantAckがまだ送信されていない）を持っている場合、同じアドレスに対してリリースを発行することはできません。その結果、MissQueueに入るミスリクエストがWritebackQueueに同じアドレスを持つエントリを検出した場合、そのミスリクエストはブロックされます。

## 全体ブロック図

WritebackQueueの全体アーキテクチャを[@fig:DCache-WritebackQueue]に示します。

![WritebackQueueフローチャート](./figure/DCache-WritebackQueue.svg){#fig:DCache-WritebackQueue}


## インターフェースタイミング

### リクエストインターフェースタイミングの例

[@fig:DCache-WritebackQueue-timing]は、L2に書き戻す必要があるリクエストのWritebackQueueでのインターフェースタイミングを示しています。

![WritebackQueueタイミング](./figure/DCache-WritebackQueue-timing.svg){#fig:DCache-WritebackQueue-timing}

## WritebackEntryモジュール
### WritebackEntryステートマシン設計
状態設計：WritebackEntryのステートマシン設計を[@tbl:WritebackEntry-state]と[@fig:DCache-WritebackEntry]に示します。

Table: WritebackEntry状態レジスタの説明 {#tbl:WritebackEntry-state}

| 状態 | 説明 |
| :--- | :--- |
| s_invalid | リセット状態、このWritebackEntryは空のエントリです |
| s_release_req | リリースまたはProbeAckリクエストを送信中 |
| s_release_resp | ReleaseAckリクエストを待機中 |

![WriteBackEntryステートマシン図](./figure/DCache-WritebackEntry.svg){#fig:DCache-WritebackEntry}
