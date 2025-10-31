```markdown
# ベクトルFOF命令ユニット VfofBuffer

## 機能説明

ベクトルFault-Only-First (fof) 命令のVLレジスタを修正するuopを処理し、書き戻します。fof命令に対しては、VLレジスタの修正を担当するuopを別途分割します。現在、fof命令は非投機的に実行されます。

### 特性 1：メモリアクセスuopの書き戻し情報収集

VfofBufferは、fof命令のメモリアクセスuopの書き戻し情報を収集する責任を負い、エントリは1つだけです。VLレジスタを更新する必要がある場合、VfofBufferで維持されている情報が更新されます。
Fault-Only-First命令が発行されると、通常のVLSplitへの進入に加えて、vfofBufferにもエントリが1つ割り当てられます。
このエントリは、VLMergeBufferからの同じRobIdxを持つuopの書き戻しを監視しますが、これらのuopがバックエンドに書き戻されるのを妨げることはなく、これらのuopの関連メタデータを収集して自身のVLを更新・維持するだけです。
VLMergeBufferからバックエンドに書き戻されるuopには例外情報やVLなどが含まれており、これらの書き戻し情報に基づいて、このuopがVLの変更を引き起こすべきかどうかを判断する必要があります。VLの変更が必要な場合は、VfofBufferで維持されているVLと比較し、より小さいVLに更新します。

### 特性 2：VLレジスタを修正するuopの書き戻し

VfofBufferは、その命令のすべてのメモリアクセスuopが書き戻された後、VLレジスタを修正するuopを書き戻します。
VLレジスタを修正する必要がない場合でも、このuopは書き戻されますが、書き込みイネーブル信号は有効になりません。

## 全体ブロック図

単一モジュールのためブロック図はありません。

## 主要ポート

|                   | 方向 | 説明                              |
| ----------------: | :--- | :-------------------------------- |
|          redirect | In   | リダイレクトポート                |
|                in | In   | Issue Queueからのuop発行を受信    |
| mergeUopWriteback | In   | VLMergeBufferから書き戻されたデータuopを受信 |
|      uopWriteback | Out  | VLを修正するuopをバックエンドに書き戻す |


## インターフェースタイミング

インターフェースのタイミングは比較的単純なため、テキストでの説明のみとします。

|                   | 説明                                          |
| ----------------: | :-------------------------------------------- |
|          redirect | Validあり。データはValid時に有効              |
|                in | Valid、Readyあり。データはValid && ready時に有効 |
| mergeUopWriteback | Valid、Readyあり。データはValid && ready時に有効 |
|      uopWriteback | Valid、Readyあり。データはValid && ready時に有効 |

```
