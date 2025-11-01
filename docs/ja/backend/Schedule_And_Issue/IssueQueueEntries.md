# IssueQueueEntries

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット: [xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 用語説明

表: 用語説明

| 略称 | 正式名称 | 説明 |
| --- | --- | --- |
| IQ  | IssueQueue | 発行キュー |

## 設計仕様

- EnqEntry・SimpleEntry・ComplexEntry の 3 種類の発行キュー項目をサポート
- デュアルポート読み書きをサポート
- 書き戻しウェイクアップと推測ウェイクアップをサポート
- EnqEntry の直接デキューをサポート
- エントリ間の命令転送をサポート
- ウェイクアップ取消フィードバックをサポート

## 機能

### 全体機能

Entries は発行キューで uop を保持するモジュールで、内部に複数の entry を備え、各 entry が 1 本の uop を格納する。entry は発行キュー入隊ポートに対応する EnqEntry と、より多数用意される OthersEntry に大別される。

Entries は全 entry の発行・状態情報を集約して発行キュー制御ロジックへ渡し、制御ロジックからの選択結果を受けて発行対象 uop の完全な情報を出力する。また IQ（自身または他 IQ からの高速ウェイクアップ）や WriteBack（書き戻しウェイクアップ）からのウェイクアップ信号、datapath 等からのキャンセル信号（og0Cancel、og1Cancel など）、発行後のフィードバック信号を受け取り、整合させたうえで各 entry に配信する。

Entries は entry 間の移動ロジックも担当する。EnqEntry は IQ 入口の uop を受け、OthersEntry が就緒であれば所定ルールに従って転送する。EnqEntry は前サイクルの uop を転送しながら次サイクルの uop を同時に入隊させる無停止動作を実現する。高度な構成では OthersEntry を SimpleEntry と ComplexEntry に分け、SimpleEntry から ComplexEntry への転送方針も Entries が制御する。

### 転送戦略

ComplexEntry は最終滞留項で転送不可。SimpleEntry は ComplexEntry へ転送でき、EnqEntry は ComplexEntry と SimpleEntry の双方へ転送できる。発行されていない項のみ転送可能で、発行済み項が失敗フィードバックを受けると発行済みフラグを消し再び転送可能になる。発行成功フィードバックを受けると無効化され、転送不要となる。

EnqEntry から OthersEntry への転送は ComplexEntry を最優先、SimpleEntry を次点とし、転送は全量かゼロかのいずれかとなる。ComplexEntry に十分な空きがあり SimpleEntry が全て空の場合だけ ComplexEntry へ転送し、それ以外は SimpleEntry へ転送する。SimpleEntry から ComplexEntry への転送は 1 サイクルあたり最大 num_enq（EnqEntry 数と同数）件で、ComplexEntry の空きごとに 1 件ずつ転送できる。SimpleEntry からの転送は EnqEntry より優先され、転送順序は年齢順（古い項目優先）で IQ の年齢マトリクスから求める。

![示意図](./figure/Entires_trans.svg)

### 発行とデキュー

Entries は各 entry の `valid` と `canIssue` を収集して IQ に渡し、IQ はデキュー対象位置 `deqSelOH` と出口の受け入れ可否 `deqReady` を返す（現在 `deqReady` は常にハイ）。両方が有効なとき、その entry はデキュー対象となり `deqSel` が送られる。

`deqSel` を受けた entry は直ちに消去せず発行済み状態にマークし、発行ポートと経過サイクルを記録する。発行成功を示す後続 `resp` を受信して初めてクリアする。

Entries は全 `resp` を集約し、該当 entry へ届ける。非メモリ IQ では `og0resp`・`og1resp` の 2 種で、entry のデキューポートと発行後サイクルに応じて選択する。entry の `robIdx` が `resp` の `robIdx` と一致した場合のみ受け入れる。

メモリ IQ では `resp` が多彩で IQ ごとに構成が異なるため、`lqidx`・`sqidx` を照合して選択する。

発行時には選択された entry の uop 情報も IQ に戻す。タイミング上 `deqSelOH` を直接用いず、IQ から渡される `enqEntryOldest`、`simpEntryOldest`、`compEntryOldest` で各系統の候補を選び、`comp` → `simp` → `enq` の優先度で最終 uop を決定する。

### ウェイクアップとキャンセル

Entries 自体はウェイクアップの演算を行わず、受け取ったウェイクアップ／キャンセル信号を全 entry に配布するだけである。ただしタイミング上、同サイクルに発生するキャンセル処理は Entries が担当する。キャンセル源の遅延が大きいため通常のルートで IQ の選択に間に合わない。そこで IQ には当サイクルのウェイクアップ結果のみを渡して選択させ、最終的に Entries が各出口の候補 uop にキャンセル判定を適用する。

## 全体ブロック図

![示意図](./figure/Entires_top.svg)

## インターフェース時系列

![示意図](./figure/Entires_signal.png)

`io_*` 信号群は IQ へ入る命令で、1 サイクル最大 2 本の入隊命令とウェイクアップ信号を伴う。タイミング対策として、入隊命令が同時にウェイクアップされるケースではウェイクアップを 1 拍遅延する（図中 `enqDelay_wakeup`）。この遅延ウェイクアップは推測ウェイクアップのバイパス時系列と同様に `srcStateNext` に影響し、`canIssueBypass` を変化させる。ComplexEntry における同サイクルウェイクアップ・同サイクル発行と類似した挙動になる。

## 二次モジュール EnqEntry & OthersEntry

### 機能

EnqEntry と OthersEntry の機能はほぼ共通で、EnqEntry のみ入隊ポート直結ゆえに入隊時ウェイクアップ処理が 1 段追加される。

Entry の主要機能は `valid`、`canIssue`、`issued`、`status` の 4 つ。

- `valid`: entry の有効状態。uop が入ると enq 情報をレジスタに書き込み `valid` をセットする。`flush`、`tranSel`、`issueResp`（発行成功）のいずれか成立でクリアする。
- `issued`: uop の発行状態。`deqSel` 受信で発行済みとし、`issueResp` が失敗またはオペランドがキャンセルされ就緒でなくなると未発行へ戻す。
- 全ソースオペランドが就緒かつ未発行なら `canIssue` をアサートする。
- `status`: ソースオペランド種別 `srcType`、状態 `srcState`、データ入手先 `dataSources`、ロード依存 `srcLoadDependency`、ウェイクアップ元 EXU `srcWakeUpL1ExuOH`、ウェイクアップ後経過サイクル `srcTimer` などから構成される。

`wakeUpFromWB` と `wakeUpFromIQ` はウェイクアップ対象の `pdest` とレジスタ種別（`xp`/`fp`/`vp`）を伝達し、番号と種別が一致するとそのオペランドを就緒とする。

`og0Cancel`・`og1Cancel` はキャンセルすべき EXU を伝える。対象 EXU が当該オペランドをウェイクアップした EXU と一致し、`srcTimer` が発行段に対応する遅延と一致すればそのオペランドをキャンセルする。`ldCancel` は指定されたロード段が `srcLoadDependency` と一致した場合にキャンセルする。同一オペランドでウェイクアップとキャンセルが同時に届いた場合はキャンセルを優先する。

ソース状態の出力は即時出力と遅延出力の 2 系統があり、高速／低速ウェイクアップに対応する。即時出力はレジスタから読み出した状態を同サイクルで更新して出力し、遅延出力は更新後レジスタへ書き戻して次サイクルに出力する。WB ウェイクアップは常に低速で、IQ ウェイクアップは設定により高速（ComplexEntry）または低速（SimpleEntry）となる。EnqEntry は実装上常に高速扱いである。

EnqEntry は入隊時ウェイクアップが追加で必要となる。入隊直後にウェイクアップ／キャンセルを完了させるのはタイミング的に困難なため、EnqEntry に書き込んだ次サイクル冒頭で処理する。まず遅延ウェイクアップ／キャンセル信号（`enqDelay*`）でレジスタ直出しの状態を更新し、その後に通常のウェイクアップ／キャンセルを行う。入隊ウェイクアップは uop が EnqEntry に入った最初のサイクルのみ適用され、それ以降はレジスタ直出し状態をそのまま使用する。

まとめ：
1. Entry は IssueQueue 内部で uop の主要情報を保持する構造で、リザベーションステーションに相当する。
2. 昆明湖の整数 IssueQueue 標準構成では Entry を 24 項備える。
3. Entry は EnqEntry・SimpleEntry・ComplexEntry の 3 区分で挙動が異なる。
4. EnqEntry は 2 項で入隊ポートに対応し、各サイクルで IQ に入る 2 命令は必ずここに格納される。
5. SimpleEntry が 6 項、ComplexEntry が 16 項で構成される。

### 全体ブロック図

![示意図](./figure/Entires_valid.svg)

![示意図](./figure/Entires_entryReg.svg)

`imm` は即値、`payload` は命令元情報を保持し、entry 内で追加処理は行わない。

![示意図](./figure/Entires_status.svg)

`srcStatus` は各 uop のソースオペランド状態を示す。`issued` は発行状態を示し、発行成功まで `validReg` を変更できないため発行途中かどうかを判別する。

![示意図](./figure/Entires_issueTimer.svg)

`issueTimer` と `deqPortIdx` は転送機構に対応するための信号である。uop は OG0・OG1 の 2 段を経て EXU に到達して初めて発行成功とみなす。途中失敗時は IQ に再発行を通知するが、転送機構がない場合は `entryIdx` で位置特定できる。転送機構があると発行後に別位置へ移動するため、`issueTimer` を発行時に更新し毎サイクル加算、`deqPortIdx` に出隊ポートを記録する。図の時系列どおり OG0/OG1 の `resp` はこれら 2 信号で対象 uop を特定する。

![示意図](./figure/Entires_srcStatus.svg)

ウェイクアップで `srcState` を更新し、`srcWakeupL1ExuOH` で推測ウェイクアップ源の EXU を記録する。

![示意図](./figure/Entires_WBwakeup.svg)

書き戻しウェイクアップは uop 実行最終サイクルで発生し、同サイクルのウェイクアップ＆発行はサポートされない。

![示意図](./figure/Entires_wakeup.svg)

`dataSource` は推測ウェイクアップの経路を示す。書き戻しウェイクアップ時は `reg` を設定し、推測ウェイクアップで当サイクル発行すると `forward`、待機サイクルを跨ぐごとに `forward → bypass → reg → reg` と遷移する。

![示意図](./figure/Entires_ldcancel.svg)

`srcLoadDependency`（3 ビット）は各 uop のロード依存を記録する。`ldCancel` が発生すると依存チェーン上の uop をまとめてクリアする。
