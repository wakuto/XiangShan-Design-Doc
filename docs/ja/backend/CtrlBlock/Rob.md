# Rob

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット: [xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 用語説明

表: 用語説明

| 略称 | 正式名称 | 説明 |
| ---- | -------- | ---- |
| rob  | Reorder Buffer     | リオーダーバッファ |
| rab  | Rename Buffer      | リネームバッファ |
| -    | Redirect           | ctrlblock から送られるリダイレクト情報 |
| -    | Walk               | リダイレクト発生後のロールバック処理 |
| snpt | Snapshot           | ctrlblock から送られるスナップショット情報 |
| wfi  | Wait For Interrupt | 割り込み待ち |

## サブモジュール一覧

表: サブモジュール一覧

| サブモジュール | 説明 |
| -------------- | ---- |
| RobEnqPtrWrapper    | rob のエンキューポインタを維持する |
| NewRobDeqPtrWrapper | rob のデキューポインタを維持する |
| Rab                 | commit または walk 時の各 rat の状態を保持し、rename モジュールと連携する |
| VTypeBuffer         | Vtype について Rab に類似した構造を保持し、decode モジュールと連携する |
| ExceptionGen        | 例外発生モジュール |
| SnapshotGenerator   | スナップショット生成モジュール |

## 設計仕様

- 命令のライトバックとコミットをサポート
- 命令のリダイレクトをサポート
- 割り込み処理をサポート
- Rob 圧縮をサポート
- スナップショットをサポート
- 例外処理をサポート
- ベクトルメモリアクセス命令がライトバック完了後に例外を処理し、vstart を設定できるようサポート
- Rob は 1 サイクルあたり最大 8 エントリの commit / walk をサポート
- Rab は 1 サイクルあたり最大 6 エントリの commit / walk をサポート

## 機能

Rob モジュールは、エンキューポインタを担当する RobEnqPtrWrapper、デキューポインタを担当する NewRobDeqPtrWrapper、commit または walk 時に各 rat の状態を維持する Rab、Vtype の状態を保持する VTypeBuffer、例外を生成する ExceptionGen、スナップショットを生成する SnapshotGenerator から構成される。

Rob モジュール本体は 160 エントリの循環キューであり、ポインタは 1 ビットのフラグと 8 ビットの値で構成される。値が最大値から 1 増えるタイミングでフラグを反転させ、命令の順序を区別する。キューが空のときは enqptr === deqptr でフラグと値の両方が等しく、キューが満杯のときは enqptr.value === deqptr.value だが enqptr.flag =/= deqptr.flag となり、値は等しくフラグのみが異なる。各 RobEntry に含まれる信号は次のとおり。

表: RobEntry 信号一覧

| 信号名 | 説明 |
| ------ | ---- |
| isVset           | Vset 命令かどうか |
| commitType       | 命令のコミット種別 |
| isHls            | 仮想化 load / store 命令かどうか |
| wflags           | fcsr の fflags を更新するかどうか |
| ftqIdx           | pcMem を読み出すための ftq ポインタ |
| ftqOffset        | pc を算出するための ftq オフセット |
| traceBlockInPipe | パイプライン内の trace データ（iretire / ilastsize / itype を含む） |
| instrSize        | Rob が圧縮した命令数 |
| fpWen            | csr の FS を更新するために使用する |
| isRVC            | 圧縮命令かどうか |
| dirtyVs          | csr の VS を更新するために使用する |
| realDestSize     | 命令が書き込むデスティネーションレジスタ数 |
| stdWritebacked   | store 命令がライトバック済みかどうか |
| uopNum           | ライトバックが必要な uop の数 |

Rob は 8 バンク読み出しの設計を採用し、robidx の下位 3 ビットでバンクを分割する。例えば robBanks0 には robidx（10 進）0, 8, 16, 24, 32, ... が含まれ、robBanks1 には robidx 1, 9, 17, 25, 33, ... が含まれる。それぞれ 8 エントリを 1 ライン（0-7, 8-15, 16-23, ...）とし、各バンクは 20 エントリ、全体で 20 ラインとなる。バンク分割の概略図を以下に示す。

![rob_entries](./figure/rob_entries.png)

20 ビットのワンホットラインポインタで RobEntry データを読み出し、8 バンクから現在行と次行のデータ（合計 16 エントリ）を取得する。当サイクルのライトバック情報で更新した後、2 行のうちいずれか 1 行を選んで 8 個の robDeqGroup レジスタへ書き込む（1 行目の命令が当サイクルで全てコミットされた場合は 2 行目を選択）。命令のコミット時には 8 個の robDeqGroup からデータを読み出してコミットする。`hasCommitted`（8 ビット）は現在の行の各命令がコミット済みかを示し、他の命令がコミット可能かどうかの条件の一つとなる。`allCommitted` は現在行の全命令がコミット済みであることを示し、ラインポインタを切り替える制御信号である。`allCommitted` が 1 のときは読み出した 2 行目、つまり後段 8 エントリのデータを更新して robDeqGroup に書き込む。

![rob_enq](./figure/rob_enq.svg)

Rob のエンキュー。Rob が命令を受け入れ可能なとき `io_enq_canAccept` をハイにし、その間 Dispatch は最大 6 命令まで Rob に送信できる。Rob は命令を受信すると enqptr を更新し、入隊要求に基づいて dispatchNum を計算して enqptr を割り当てる。リダイレクトが発生しなければ enqptr を enqptr + dispatchNum に更新する。リダイレクト信号が発生した場合は、リダイレクト命令の robidx（レベルに依存）を基準に enqptr を設定する。エンキュー時、命令が move 削除対象であれば `writebacked` 信号を直接ハイにし、ライトバックなしでコミットできる。デコード段階で例外が検出された命令は rename 段階で `numWB` を 0 に設定し、IQ へディスパッチされず、Rob に入るとライトバック済みとマークされる。とくにベクトルメモリアクセス命令は全ての uop がライトバックされるまで例外を処理できない点に注意する。`allocatePtrVec` は割り当てられた 6 個の enqPtr を表し、分配条件は命令が有効かつ最初の uop（デコードまたは Rob 圧縮で得られた `firstUop` 信号）であること。`canEnqueue`（6 ビット）は各命令が Rob に入れる条件で、命令が有効・最初の uop であり、Rob が受け入れ可能である必要がある。`uopNum` は Rob が圧縮した命令数（Rob 圧縮に対応）または uop の数（ベクトル命令分割に対応）を記録し、入隊時に更新、以降 uop がライトバックされるごとに（同一サイクルで複数ライトバックも可）1 ずつ減算する。store 命令では `uopNum` を 1 に設定し、`stdWritebacked` をローにし、store データの uop は `uopNum` には数えず、ライトバック時に `stdWritebacked` をハイにする。

Rob のライトバック。Exu から Rob へのライトバック制御信号は ctrlBlock 内で 1 サイクル遅延される。Rob 圧縮によって複数の Exu が同一 robidx へライトバックする可能性があるため、ctrlBlock で遅延させると同時に Rob 圧縮の計算を行う。各 Exu は、自身と圧縮される可能性のある Exu のうち、同じ robidx へライトバックする数を集計し、`io` の `writebackNums` を介して Rob に伝達する（圧縮関係が存在しない Exu 間は統計を省き、面積とタイミングを節約する）。

![rob_commit](./figure/rob_commit.svg)

Rob のコミット。デキューポインタ位置の命令は、Rob 状態機械が idle 状態で、命令が有効、uop がすべてライトバック済み、`blockCommit` がローであるときにコミットされる。デキュー位置の命令に例外がある場合、`blockCommit` がハイとなりコミットを阻止し、例外処理が完了するまでその命令はコミットできない。`commitValidThisLine` は deqptr が位置する行の 8 エントリがコミット可能かを示し、エントリが有効で、全 uop がライトバック済み、Rob が割り込みを有効にしておらず、デキュー命令に例外や応答待ちの命令がなく、より古い命令にコミットを阻害されておらず、自身も未コミットであることを条件とする。`allowOnlyOneCommit` のケースでは、デキュー対象 8 エントリ内に例外発生命令があるか、割り込みが有効な場合、Rob は 1 サイクル当たり 1 命令のみコミットを許可する。

Rob のデキュー。Rob はコミット完了した命令をデキューし、コミットされたエントリ数を集計して deqptr の値に加算しデキューポインタを更新、デキューしたエントリの `valid` をローにする。

Rob 状態機械は `s_idle` と `s_walk` の 2 状態を持ち、状態更新は主にリダイレクトに連動する。`s_idle` は通常状態で命令をコミット可能。リダイレクト後は少なくとも 2 サイクル walk 状態を経て idle に戻る。`s_walk` は walk 状態で命令をコミットできず、各モジュールの walk 完了を待って `s_idle` に復帰する。状態機械の切り替えコードは以下のとおり。

```
  /**
   * state changes
   * (1) redirect: switch to s_walk
   * (2) walk: when walking comes to the end, switch to s_idle
   */
  state_next := Mux(
    io.redirect.valid || RegNext(io.redirect.valid), s_walk,
    Mux(
      state === s_walk && walkFinished && rab.io.status.walkEnd && vtypeBuffer.io.status.walkEnd, s_idle,
      state
    )
  )
```

Rob のリダイレクトとスナップショット。`redirect` が valid のサイクルには Rob は命令をコミットせず、walk の開始アドレスに従って Rob の読出しポインタを切り替える。walk の開始アドレスは snapshot と deqptr の 2 つの情報源があり、リダイレクト命令よりも古く直近の位置を選択する。Rob の snapshot は一組の robidx を保持し、入隊最初の命令の robidx を基準に +0, +1, +2, +3, +4, +5, +6, +7 の 8 個を保持する。Rob の snapshot は ctrlblock 内の snapshot で制御され、下図に walkPtr の選択例を示す。

![rob_walkPtr](./figure/rob_walkPtr.svg)

walkPtr の更新: redirect が有効で `io_snpt_useSnpt` が 1 の場合は `io_snpt_snptSelect` に従って対応するスナップショットを選択し、`io_snpt_useSnpt` が 0 の場合は deqPtr を選択する。walkPtr は bank0 のアドレスに整列させる必要がある。redirect が無効で rob が walk 状態にあり walk が終了していない場合、walkPtr はサイクルごとに 8 ずつ増加する。それ以外の条件では walkPtr は更新しない。`lastWalkPtr` は walk の終点であり、redirect の指令が自身を巻き戻すかどうかで決まる。自身を巻き戻す場合は redirect の robidx - 1、巻き戻さない場合は redirect の robidx となる。`donotNeedWalk` 機構により、walk の初サイクルにおいて redirect より古い robidx の命令は walk が不要と判断される。walk 終了判定は `walkPtrTrue > lastWalkPtr` で `walkFinished` を 1 とし、`walkPtrTrue` はバンクアラインを考慮しない walkPtr である。`walkFinished` が 1 になると walk 終了情報を Rab と VTypeBuffer に伝える。`shouldWalkVec` は 8 エントリが walk すべきかを示し、`lastWalkPtr` より古い命令かどうかと `donotNeedWalk` の結果を総合して判断する。

Redirect が有効なとき、当サイクルの Rob は命令をコミットせず、walk ポインタを walk 起点（スナップショット復旧またはデキュー位置）へ更新する。walk の開始アドレスは bank0 に属するエントリの robidx でなければならない。walk の終点 `lastWalkPtr` を記録し、次サイクルに状態機械を walk 状態へ遷移させ、読み出しバンクポインタを walkPtr に合わせ、リダイレクト後ろの命令の `valid` を 0 にする。その次のサイクルで 8 個の robDeqGroup から walk が必要な情報（`realDestSize`、`isVset`）を Rab と VTypeBuffer に渡す。walk 状態中は毎サイクル 8 エントリずつ walk し、`realDestSize` を Rab に、`isVset` を VTypeBuffer に累積して渡す。Rob が `lastWalkPtr` に到達すると Rob 自身の walk は停止するが、Rab と VTypeBuffer の walk が完了するまで idle 状態には戻れない。Rab は 1 サイクルで最大 6 エントリ、VTypeBuffer は 1 サイクルで最大 8 エントリ walk する。

Rob の例外処理。例外が発生した命令以降は実行されないため、Rob は最古の例外のみを保持すればよい。この機能を Rob 例外生成モジュールで実装する。Rob 内部ではコミット中の命令に対して例外判定を行う。例外生成モジュールでは、enq 信号（Rob 入隊信号と同サイクル）でフロントエンドと decode から最大 6 命令分の例外情報を入力し、wb 信号で機能ユニットからのライトバック例外情報（csr、fence、load、store、vload、vstore）を入力して、最古の命令に対応する例外を出力する。`current` 信号は現在保持している例外情報である。enq で入る命令は順序付きのため `priorityMux` で最古の例外を選択できる。一方 wb で入る命令は順不同のため、robidx を比較して最古の例外を選ぶ必要がある。例外処理モジュールはグループ毎に最古命令を選定し、1 サイクル目で各グループの最古を決め、2 サイクル目でそれらの中から最古を選ぶ。2 サイクル目で得た最古の例外情報と `current` を比較し、`current` の方が若ければ `current` を更新する。ベクトルメモリアクセスのライトバック例外は robidx が同一でも uop が複数あるため、最古の robidx に加えて例外で設定する `vstart` も比較し、より小さい `vstart` の例外情報を保持する。

Rob の割り込み処理。割り込みは CSR モジュールから供給され、flushPipe や replayInst を発行する必要がある命令も現状では ExceptionGen が処理する。Rob はまず `flushOut` を ctrlBlock に送り、ctrlBlock がリダイレクトを返してパイプラインを洗浄する。分岐ミスやメモリ違反によるリダイレクトは、pcMem から pc を読んで ftqOffset と組み合わせて target を算出し前段に送る。一方、中断や例外では情報を CSR に送って target を返してもらい、その後フロントエンドへ渡す。割り込みは現在、deqPtr が load / store / fence / csr / vset 以外の命令である場合にのみ応答する。

`wfi_enable` 信号（CSR レジスタからの wait-for-interrupt enable）がハイのとき、wfi 命令が Rob に入隊すると `hasWFI` を 1 にする。`hasWFI` は `blockCommit` をハイにし、Rob のコミットを停止させることでパイプラインを停止し割り込みを待つ。CSR が割り込みを受け取ると `io_csr_wfiEvent` がハイになり、`hasWFI` を 0 に戻す（または 1M サイクル待っても割り込みが到来しなかった場合も 0 に戻す）。その後 Rob は通常どおり命令をコミットできる。

## 全体設計

### 全体ブロック図

### インターフェース一覧

インターフェース仕様書を参照。

## モジュール設計

### 二次モジュール

#### 機能

#### 全体ブロック図

#### インターフェース一覧

インターフェース仕様書を参照。
