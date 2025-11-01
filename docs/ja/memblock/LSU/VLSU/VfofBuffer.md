# ベクトル FOF 命令ユニット VfofBuffer

## 機能説明

ベクトル Fault Only First (fof) 命令で VL レジスタを更新する uop を処理し書き戻す。fof 命令では VL 更新専用の uop を追加で切り出し、現状は非投機で実行する。

### 特性 1：メモリアクセスuopの書き戻し情報収集

VfofBuffer は fof 命令のメモリアクセス uop の書き戻し情報を集約し、保持する項は 1 つだけである。VL レジスタを更新する必要が生じた場合は VfofBuffer 内の情報を更新する。
Fault Only First 命令が発行されると、通常どおり VLSplit に入るのに加え vfofBuffer にも 1 項を割り当てる。
この項は VLMergeBuffer から同一 RobIdx の uop 書き戻しを監視するが、バックエンドへの書き戻し自体は妨げず、付随するメタデータを収集して内部で保持する VL を更新する。
VLMergeBuffer が書き戻す uop には例外情報や VL などが含まれるため、それらに基づいて VL を更新すべきか判断し、更新すべきなら VfofBuffer が保持する VL と比較して小さい方に張り替える。

### 特性 2：VLレジスタを修正するuopの書き戻し

VfofBuffer はその命令に属する全メモリアクセス uop の書き戻しが終わってから VL レジスタを更新する uop を書き戻す。
VL を更新する必要がない場合でもこの uop 自体は書き戻されるが、書き込みイネーブルは無効のままである。

## 全体ブロック図

単一モジュールのためブロック図はありません。

## 主要ポート

|                   | 方向 | 説明                              |
| ----------------: | :--- | :-------------------------------- |
|          redirect | In   | リダイレクトポート                |
|                in | In   | Issue Queue からの uop 発行を受信 |
| mergeUopWriteback | In   | VLMergeBuffer からの書き戻し uop を受信 |
|      uopWriteback | Out  | VL を更新する uop をバックエンドに送る |


## インターフェースタイミング

インターフェースのタイミングは比較的単純なため、テキストでの説明のみとします。

|                   | 説明                                          |
| ----------------: | :-------------------------------------------- |
|          redirect | Valid を持つ。データは Valid 時に有効        |
|                in | Valid と Ready を持つ。Valid && Ready 時に有効 |
| mergeUopWriteback | Valid と Ready を持つ。Valid && Ready 時に有効 |
|      uopWriteback | Valid と Ready を持つ。Valid && Ready 時に有効 |
