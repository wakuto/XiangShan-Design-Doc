# Rob

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット: [xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 用語説明

表: 用語説明

| 略語 | 正式名称 | 説明 |
|---|---|---|
| rob | Reorder Buffer | リオーダーバッファ |
| rab | Rename Buffer | リネームバッファ |
| - | Redirect | ctrlblockから送られてくるリダイレクト情報 |
| - | Walk | リダイレクト発生後のロールバックプロセス |
| snpt | Snapshot | ctrlblockから送られてくるスナップショット情報 |
| wfi | Wait For Interrupt | 割り込み待ち |

## サブモジュールリスト

表: サブモジュールリスト

| サブモジュール | 説明 |
|---|---|
| RobEnqPtrWrapper | robのエンキューポインタを維持する |
| NewRobDeqPtrWrapper | robのデキューポインタを維持する |
| Rab | commitまたはwalk時の各ratの状態を維持し、renameモジュールと対話する |
| VTypeBuffer | VtypeのRabに似た構造を維持し、decodeモジュールと対話する |
| ExceptionGen | 例外生成モジュール |
| SnapshotGenerator | スナップショット生成モジュール |

## 設計仕様

- 命令のライトバックとコミットをサポート
- 命令のリダイレクトをサポート
- 割り込み処理をサポート
- Rob圧縮をサポート
- スナップショットをサポート
- 例外処理をサポート
- ベクトルメモリアクセス命令がライトバックしてから例外を処理し、vstartを設定することをサポート
- Robは毎周期最大8エントリのcommit/walkをサポート
- Rabは毎周期最大6エントリのcommit/walkをサポート

## 機能

Robモジュールには、エンキューポインタを担当するRobEnqPtrWrapper、デキューポインタを担当するNewRobDeqPtrWrapper、commitまたはwalk時の各ratの状態を維持するRab、Vtypeの状態を維持するVTypeBuffer、例外を生成するExceptionGen、スナップショットを生成するSnapshotGeneratorが含まれます。

Robモジュールの本体は160エントリの循環キューです。ポインタは1ビットのフラグと8ビットの値で構成されます。値が最大値から1増加するとフラグが反転し、命令の順序を区別します。キューが空のとき、enqptr === deqptrで、フラグと値の両方が等しくなります。キューが満杯のとき、enqptr.value === deqptr.valueですが、enqptr.flag =/= deqptr.flagとなり、値は等しいがフラグが異なります。各RobEntryに含まれる信号は以下の表の通りです。

表: RobEntry信号リスト

| 信号名 | 説明 |
|---|---|
| isVset | Vset命令かどうか |
| commitType | 命令のコミットタイプ |
| isHls | 仮想化ロード/ストア命令かどうか |
| wflags | fcsrのfflagsを書き込むかどうか |
| ftqIdx | pcMemを読み取るためのftqのポインタ |
| ftqOffset | pcを計算するためのftqのオフセット |
| traceBlockInPipe | パイプライン内のトレースデータ。iretire、ilastsize、itypeを含む |
| instrSize | Robで圧縮された命令数 |
| fpWen | csrのFSを更新するために使用 |
| isRVC | 圧縮命令かどうか |
| dirtyVs | csrのVSを更新するために使用 |
| realDestSize | 命令が書き込むデスティネーションレジスタの数 |
| stdWritebacked | ストア命令がライトバックされたかどうか |
| uopNum | ライトバックが必要なuopの数 |

Robは8つのバンクに分けて読み出す設計を採用しており、robidxの下位3ビットでバンクを分けます。例えば、robBanks0にはrobidx（10進数）: 0, 8, 16, 24, 32, ...が含まれ、robBanks1にはrobidx（10進数）: 1, 9, 17, 25, 33, ...が含まれます。8エントリごとに1つのライン（0-7, 8-15, 16-23, ...）を構成します。各バンクには20のエントリがあり、合計20のラインがあります。バンク分割の概略図は以下の通りです。

![rob_entries](./figure/rob_entries.png)

ワンホットのラインポインタ（20ビット）を使用してRobEntryデータを読み出し、8つのバンクから現在のラインと次のラインのデータ（合計16エントリ）を読み出します。当サイクルのライトバック情報で更新後、2つのラインから1つのラインを選択して8つのrobDeqGroupレジスタに書き込みます（最初のラインの命令が当サイクルで全てコミットされた場合は2番目のラインを選択）。命令コミット時には8つのrobDeqGroupからデータを読み出してコミットします。hasCommitted（8ビット）は現在のラインの各命令がコミットされたかどうかを示し、他の命令がコミットできるかどうかの条件の1つとなります。allCommittedは現在のラインが全てコミットされたことを示し、ラインポインタを切り替える制御信号です。allCommittedが1の場合、読み出された2番目のラインのデータ、つまり後ろの8つのデータを更新してrobDeqGroupに書き込みます。

![rob_enq](./figure/rob_enq.svg)

Robのエンキュー。Robが命令を受け入れ可能な場合、io_enq_canAcceptをハイにし、DispatchはRobに最大6つの命令を送信できます。Robは命令を受け取るとenqptrを更新し、エンキュー要求に基づいてdispatchNumを計算してenqptrを割り当てます。リダイレクトが発生していない場合、enqptrをenqptr + dispatchNumに更新します。リダイレクト信号が発生した場合、リダイレクト命令のrobidxに基づいてenqptrを設定します（リダイレクトのレベルに関連）。エンキュー時、命令がmove削除を必要とする場合、writebacked信号を直接ハイにし、ライトバックなしでコミットできます。デコード時に命令が例外を発生させた場合、命令はリネーム段階でnumWBを0に設定され、IQにディスパッチされず、Robに入るとライトバック済みとしてマークされます。特に、ベクトルメモリアクセス命令はuopが全てライトバックされるまで例外を処理できません。allocatePtrVecは割り当てられた6つのenqPtrで、割り当て条件は命令が有効で最初のuopであることです（デコードまたはrob圧縮によって得られたfirstUop信号）。canEnqueue（6ビット）は各命令がRobに入れる条件です：命令が有効で最初のuopであり、かつrobが受け入れ可能であること。uopNumはrobが圧縮した命令数（rob圧縮に対応）またはuop数（ベクトル命令分割に対応）を記録し、エンキュー時にuopNumを更新し、その後uopが1つライトバックされるごとに（同じサイクルで複数のuopがライトバックされることも可能）uopNumを1減らします。ストア命令の場合、uopNumは1に設定され、stdWritebackedはローになり、stdのuopはuopNumにカウントされず、ライトバック時にstdWritebackedをハイにします。

Robのライトバック。ExuからRobへのライトバック制御信号はctrlBlockで1サイクル遅延されます。Rob圧縮により複数のExuが同じrobidxにライトバックする可能性があるため、ctrlBlockでの遅延と同時にRob圧縮の計算が行われます。各Exuは、一緒に圧縮される可能性のあるすべてのExu（一部のExu間には圧縮関係が存在しないため、面積とタイミングを無駄にすべて統計する必要はありません）の中で、自分と同じrobidxにライトバックするものの数を統計し、io内のwritebackNumsを介してRobに伝えます。

![rob_commit](./figure/rob_commit.svg)

Robのコミット。デキューポインタ位置の命令は、Robステートマシンがアイドル状態、命令が有効、uopが全てライトバック済み、blockCommitがローの時にコミットされます。デキュー位置の命令に例外が存在する場合、blockCommitがハイになり命令のコミットを阻止し、例外処理が完了するまでその命令はコミットできません。commitValidThisLineはdeqptrがあるラインの8つのエントリがコミット可能かどうかを示します。判断方法は、そのエントリが有効で、そのエントリのすべてのuopがすでにライトバックされており、このときrobが割り込みを有効にしておらず、デキュー命令に例外がなく、デキュー命令にリプライが必要な命令がなく、それより古い命令によってコミットがブロックされておらず、かつそれ自体がまだコミットされていないことです。allowOnlyOneCommitの場合に注意してください。デキューされる8つのエントリの中に例外が発生した命令があるか、または割り込みが有効になっている場合、robは毎周期1つの命令しかコミットを許可しません。

Robのデキュー。Robはコミット後の命令をデキューし、コミットされたエントリの数を統計し、deqptrの値にコミットされたエントリの数を加算してデキューポインタを更新し、デキューされたエントリのvalidをローにします。

Robステートマシン。s_idleとs_walkの2つの状態があり、状態の更新は主にリダイレクトに関連しています。s_idle：通常状態、命令をコミット可能。リダイレクト後、少なくとも2サイクルのwalk状態を経てからidle状態に戻ることができます。s_walk：walk状態、命令をコミット不可。各モジュールのwalkが終了するのを待ってs_idle状態に復帰します。ステートマシンの切り替えコードは以下の通りです。

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
```
