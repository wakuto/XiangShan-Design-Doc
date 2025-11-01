# セカンダリーモジュール PMP&PMA

PMP には以下のモジュールが含まれ、PMA チェックは PMP モジュール内で実施される。

1. PMP（分散配置された PMP & PMA レジスタ）
    1. PMP pmp（Frontend）
    2. PMP pmp（Memblock）
    3. PMP pmp（L2TLB）
2. PMPChecker（PMP & PMA チェッカ、同サイクルで結果を返す）
    1. PMPChecker PMPChecker（Frontend）
    2. PMPChecker PMPChecker_1（Frontend）
    3. PMPChecker PMPChecker_2（Frontend）
    4. PMPChecker PMPChecker_3（Frontend）
    5. PMPChecker PMPChecker（L2TLB）
    6. PMPChecker PMPChecker_1（L2TLB）
3. PMPChecker_8（PMP & PMA チェッカ、次サイクルで結果を返す）
    1. PMPChecker_8 PMPChecker（Memblock）
    2. PMPChecker_8 PMPChecker_1（Memblock）
    3. PMPChecker_8 PMPChecker_2（Memblock）
    4. PMPChecker_8 PMPChecker_3（Memblock）
    5. PMPChecker_8 PMPChecker_4（Memblock）
    6. PMPChecker_8 PMPChecker_5（Memblock）

## 設計仕様

1. 物理アドレス保護をサポート
2. 物理アドレス属性をサポート
3. PMP と PMA の並列チェックをサポート
4. 動的チェックと静的チェックをサポート
5. 分散配置された PMP と PMA をサポート
6. 例外処理機構をサポート

## 機能

### 物理アドレス保護への対応

香山プロセッサは Physical Memory Protection（PMP）チェックをサポートする。PMP のエントリ数は既定で 16 だがパラメータで変更できる。タイミング要件を満たすため、分散コピー方式を採用する。CSR ユニット内の PMP レジスタが CSRRW などの命令を処理し、フロントエンド取込、バックエンドのメモリアクセス、ページテーブルウォーカ（PTW）の各箇所に PMP レジスタのコピーを持たせる。CSR の書き込み信号を取り込んで CSR ユニット内の PMP レジスタと一貫性を保つ。

PMP レジスタのフォーマットや初期値などは香山オープンソースプロセッサユーザマニュアルおよび RISC-V 特権仕様を参照。

### 物理アドレス属性への対応

物理アドレス属性（PMA）は PMP と同様の手法で実装した。PMP Configure レジスタの予約ビット 2 つを利用し、`atomic` と `cachable` として原子操作の可否とキャッシュ可能性を表す。PMP レジスタに初期値はないが、PMA レジスタには既定の初期値を持たせ、プラットフォームのアドレス属性と一致するよう手動設定する。PMA レジスタは M モード CSR の予約アドレス空間を利用し、既定で 16 エントリ（パラメータで変更可）である。

PMA のデフォルト設定は香山オープンソースプロセッサユーザマニュアルを参照。

### PMP と PMA の並列チェック

PMP と PMA を並列に照会し、どちらか一方でも違反があれば不正操作と判定する。コア内部の物理アドレスアクセスはすべて権限チェックが必要で、ITLB/DTLB チェック後、および Page Table Walker、Hypervisor Page Table Walker、Last Level Page Table Walker がメモリアクセスする前に行う。ITLB、DTLB、PTW、LL PTW、Hypervisor PTW がそれぞれどの分散 PMP/PMA とチェッカを使用するかは表[@tbl:PMP-PMA-modules] のとおりである。すなわち Frontend、Memblock、L2 TLB はそれぞれ PMP/PMA レジスタのコピーを保持し（5.2.5 節参照）、各自のチェッカを駆動する。

Table: PMP と PMA チェックモジュールの対応関係 {#tbl:PMP-PMA-modules}

| モジュール | チャネル                          | 分散 PMP&PMA      | PMP&PMA チェッカ |
| ---------- | --------------------------------- | ----------------- | ---------------- |
| ITLB       |                                   |                   |                  |
|            | requestor(0)                      | pmp（Frontend）   | PMPChecker       |
|            | requestor(1)                      | pmp（Frontend）   | PMPChecker_1     |
|            | requestor(2)                      | pmp（Frontend）   | PMPChecker_2     |
|            | requestor(3)                      | pmp（Frontend）   | PMPChecker_3     |
| DTLB_LD    |                                   |                   |                  |
|            | requestor(0)                      | pmp（Memblock）   | PMPChecker       |
|            | requestor(1)                      | pmp（Memblock）   | PMPChecker_1     |
|            | requestor(2)                      | pmp（Memblock）   | PMPChecker_2     |
| DTLB_ST    |                                   |                   |                  |
|            | requestor(0)                      | pmp（Memblock）   | PMPChecker_3     |
|            | requestor(1)                      | pmp（Memblock）   | PMPChecker_4     |
| DTLB_PF    |                                   |                   |                  |
|            | requestor(0)                      | pmp（Memblock）   | PMPChecker_5     |
| L2 TLB     |                                   |                   |                  |
|            | Page Table Walker                 | pmp（L2 TLB）     | PMPChecker       |
|            | Last Level Page Table Walker      | pmp（L2 TLB）     | PMPChecker_1     |
|            | Hypervisor Page Table Walker      | pmp（L2 TLB）     | PMPChecker_2     |

RISC-V 仕様では Page Fault の優先度が Access Fault より高い。ただし Page Table Walker や Last Level Page Table Walker が PMP や PMA チェックで Access Fault を起こした場合、ページテーブルエントリが不正となり Page Fault と Access Fault が同時に発生する。この場合、香山では Access Fault を報告する。仕様に明記はなく挙動が異なる可能性があるが、それ以外のケースでは Page Fault の優先度が Access Fault より高くなるよう制御している。

### 動的チェックと静的チェック

仕様上、PMP と PMA は動的チェック、すなわち TLB 変換後の物理アドレスで権限検査を行う必要がある。Frontend、L2 TLB、Memblock の 5 つの PMPChecker（表[@tbl:PMP-PMA-modules] 参照）は動的チェックである。タイミングを考慮し、DTLB の PMP/PMA チェック結果を前倒しで求め、TLB へ回填する際に格納する静的チェックも可能である。具体的には、L2 TLB がページテーブルエントリを DTLB に回填する際、そのエントリを PMP/PMA に渡して権限チェックを行い、得られた属性ビット（R, W, X, C, Atomic。詳細は 5.4 節）を DTLB に保存する。これにより再チェックなしに Memblock へ結果を返せる。静的チェックを実現するには PMP/PMA の粒度を 4KB に引き上げる必要がある。

注意点として、現状 PMP/PMA チェックは昆明湖のタイミングボトルネックにはなっていないため、静的チェックは採用しておらずすべて動的チェックである。昆明湖 V1 のコードには静的チェックの実装はなく、動的チェックのみである。ただし互換性のため、PMP/PMA の粒度は 4KB に保っている。

動的チェックと静的チェックで得られる情報は以下のとおり。

* 動的チェック：命令アクセス例外、ロードアクセス例外、ストアアクセス例外の有無／アクセス先が MMIO 空間かどうか。
* 静的チェック：対象物理アドレスの属性ビット（R、W、X、C、Atomic）。昆明湖 V1 では静的チェックを既定では用いない。

### 分散配置された PMP と PMA

PMP/PMA の実装は CSR Unit、Frontend、Memblock、L2 TLB の 4 部分で構成する。CSR Unit が CSR 命令に応答し、PMP/PMA レジスタの読み書きを担当する。CSR Unit と ITLB/DTLB/L2 TLB は距離があるため、これらのモジュール内にも PMP/PMA レジスタのコピーを保持し物理アドレスと属性チェックに利用する。よって、ITLB、DTLB、L2 TLB 付近にコピーを持たせる分散 PMP/PMA が必要となる。

Frontend、Memblock、L2 TLB は PMP/PMA レジスタのコピーを保持し、CSRRW の書き込み信号を取り込むことで内容を同期させる。L1 TLB は面積制約があるため、PMP/PMA レジスタのコピーは Frontend や Memblock に置き、ITLB/DTLB のチェックを提供する。L2 TLB は面積に余裕があるため、PMP/PMA レジスタのコピーを L2 TLB 内に保持する。

### PMP と PMA のチェックフロー

ITLB/DTLB で物理アドレスを得たあと、L2 TLB の Page Table Walker、Last Level Page Table Walker、Hypervisor Page Table Walker がメモリアクセスする前に物理アドレスチェックを行う。PMPChecker に提供する情報は、PMP/PMA の設定レジスタ、アドレスレジスタ（連続した 1 のビット数。最小 12）、チェック対象の物理アドレス、要求する権限（ITLB：命令実行、Memblock：読み書き、原子読み書き）などである。

PMP/PMA チェック要求に必要な情報は表[@tbl:PMP-PMA-req-info] のとおり。

Table: PMP と PMA チェック要求に必要な情報 {#tbl:PMP-PMA-req-info}

| PMPChecker モジュール | 必要な情報                                                                                       | 供給元                                                                                |
| ---------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| Frontend               |                                                                                                  |                                                                                       |
|                        | PMP/PMA 設定レジスタ                                                                             | Frontend pmp                                                                          |
|                        | PMP/PMA アドレスレジスタ                                                                         | Frontend pmp                                                                          |
|                        | PMP/PMA の mask（アドレスレジスタの下位連続 1 の個数。最小 12）                                 | Frontend pmp                                                                          |
|                        | 照会対象の物理アドレス（paddr）                                                                  | ICache、IFU                                                                           |
|                        | 照会コマンド。ITLB は常に 2（実行権限）                                                          | ICache、IFU                                                                           |
| Memblock               |                                                                                                  |                                                                                       |
|                        | PMP/PMA 設定レジスタ                                                                             | Memblock pmp                                                                          |
|                        | PMP/PMA アドレスレジスタ                                                                         | Memblock pmp                                                                          |
|                        | PMP/PMA の mask（下位連続 1 の個数、最小 12）                                                    | Memblock pmp                                                                          |
|                        | 照会対象の paddr                                                                                | LoadUnits、L1 Load Stream & Stride Prefetch、StoreUnits、AtomicsUnit、SMSprefetcher |
|                        | 照会コマンド。DTLB は 0/1/4/5（read/write/atom_read/atom_write）                               | LoadUnits、L1 Load Stream & Stride Prefetch、StoreUnits、AtomicsUnit、SMSprefetcher |
| Memblock 静的チェック |                                                                                                  |                                                                                       |
|                        | PMP/PMA 設定レジスタ                                                                             | Memblock pmp                                                                          |
|                        | PMP/PMA アドレスレジスタ                                                                         | Memblock pmp                                                                          |
|                        | PMP/PMA の mask（低 i ビットが 1 で、高位が 0。i は一致領域の log2 サイズ。）                    | Memblock pmp                                                                          |
|                        | 照会対象の paddr                                                                                | L2 TLB から返る PTW                                                                   |
| L2 TLB                 |                                                                                                  |                                                                                       |
|                        | PMP/PMA 設定レジスタ                                                                             | L2 TLB pmp                                                                            |
|                        | PMP/PMA アドレスレジスタ                                                                         | L2 TLB pmp                                                                            |
|                        | PMP/PMA の mask（低 i ビットが 1 で、高位が 0。i は一致領域の log2 サイズ。）                    | L2 TLB pmp                                                                            |
|                        | 照会対象の paddr                                                                                | Page Table Walker、Last Level Page Table Walker、Hypervisor Page Table Walker        |
|                        | 照会コマンド。L2 TLB は常に 0（読み取り権限）                                                   | Page Table Walker、Last Level Page Table Walker、Hypervisor Page Table Walker        |

PMPChecker は ITLB、DTLB、L2 TLB に対して、命令アクセス例外（ITLB）、ロードアクセス例外（LoadUnits、L2 TLB）、ストアアクセス例外（StoreUnits、AtomicsUnit）、アクセス先が MMIO 空間かの情報を返す。静的チェックではさらに cacheable、atomic、x、w、r の属性ビットを DTLB に格納する。

ITLB と L2 TLB からのリクエストは同サイクルで結果を返し、DTLB からのリクエストは次サイクルで結果を返す。チェック結果で返す情報は表[@tbl:PMP-PMA-resp-info] のとおり。

Table: PMP と PMA チェックで返す情報 {#tbl:PMP-PMA-resp-info}

| PMPChecker モジュール | 返却する情報                    | 宛先                                                                                |
| ---------------------- | ------------------------------- | ----------------------------------------------------------------------------------- |
| Frontend               |                               |                                                                                     |
|                        | 命令アクセス例外の有無          | ICache、IFU                                                                         |
|                        | MMIO 空間かどうか              | ICache、IFU                                                                         |
| Memblock 動的チェック  |                               |                                                                                     |
|                        | ロードアクセス例外の有無        | LoadUnits                                                                           |
|                        | ストアアクセス例外の有無        | StoreUnits、AtomicsUnit                                                             |
|                        | MMIO 空間かどうか              | LoadUnits、StoreUnits、AtomicsUnit                                                  |
| Memblock 静的チェック  |                               |                                                                                     |
|                        | キャッシュ可能か               | DTLB                                                                                |
|                        | 原子操作可否                   | DTLB                                                                                |
|                        | 実行可否                       | DTLB                                                                                |
|                        | 書き込み可否                   | DTLB                                                                                |
|                        | 読み出し可否                   | DTLB                                                                                |
| L2 TLB                 |                               |                                                                                     |
|                        | ロードアクセス例外の有無        | Page Table Walker、Last Level Page Table Walker、Hypervisor Page Table Walker       |
|                        | MMIO 空間かどうか              | Page Table Walker、Last Level Page Table Walker、Hypervisor Page Table Walker       |

### 例外処理

PMP/PMA チェックで発生し得る例外は、命令アクセス例外（ITLB）、ロードアクセス例外（LoadUnits、L2 TLB）、ストアアクセス例外（StoreUnits、AtomicsUnit）である。ITLB や DTLB が例外を検出した場合は、リクエスト元に応じて処理モジュールへ渡す。ITLB の例外は ICache あるいは IFU に、DTLB の例外は LoadUnits、StoreUnits、AtomicsUnit に渡す。

Page Table Walker、Last Level Page Table Walker、Hypervisor Page Table Walker はメモリアクセス前に PMP/PMA チェックを行うため、L2 TLB で access fault が発生する可能性がある。L2 TLB は例外を直接処理せず、L1 TLB に通知する。L1 TLB はアクセス fault を検出すると要求されたコマンドに応じて inst access fault、load access fault、store access fault を生成し、リクエスト発行元に渡す。

想定例外と MMU の処理フローは表[@tbl:PMP-PMA-exceptions] のとおり。

Table: PMP と PMA チェックで生じ得る例外と処理フロー {#tbl:PMP-PMA-exceptions}

| **モジュール** | **発生し得る例外**           | **処理フロー**                                                   |
| :------------- | :--------------------------- | :--------------------------------------------------------------- |
| ITLB           |                              |                                                                 |
|                | 命令アクセス例外             | リクエスト元に応じ ICache または IFU で処理                     |
| DTLB           |                              |                                                                 |
|                | ロードアクセス例外           | LoadUnits で処理                                                 |
|                | ストアアクセス例外           | リクエスト元に応じ StoreUnits または AtomicsUnit で処理         |
| L2 TLB         |                              |                                                                 |
|                | Access fault                 | L1 TLB へ通知し、L1 TLB がリクエスト元に応じて処理を振り分ける |

### チェックルール

香山・昆明湖アーキテクチャの PMP/PMA チェックルールは RISC-V 仕様に準拠し、ここではマッチング方式のみ説明する。PMP/PMA の設定レジスタ A ビットとアドレスレジスタにより、1 エントリが管理するアドレス範囲が決まる。DTLB の静的チェック（5.4.2.4 節参照）に対応するため粒度を 4KB とし、最小範囲も 4KB とする。

A ビットのモードは以下のとおり。A=0,1,2,3 は順に OFF、TOR、NA4、NAPOT を示す。

* A=0（OFF）：エントリ無効、マッチしない。
* A=1（TOR：Top of Range）：前エントリのアドレスレジスタから当該エントリのアドレスレジスタまでをマッチ。
* A=2（NA4）：昆明湖ではサポートしない。
* A=3（NAPOT）：アドレスレジスタの下位連続 1 の数を調べ、`ADDR = yyy…111`（1 が x 個）の場合、`yyy…000`（`ADDR >> 2`）から始まる $2^{x+3}$ バイトをマッチする。昆明湖では最小粒度 4KB と定めるため、最小範囲も 4KB となる。

分散 PMP/PMA からチェッカへはマスク信号を送る。マスクは下位 i ビットが 1、上位が 0 の形で、i はエントリがカバーするアドレス空間の log2 値である。エントリ更新時にマスク値も更新する。最小粒度 4KB のため、マスク信号の下位 12 ビットは必ず 1 になる。

例：ある PMP エントリの `pmpaddr = 16'b1111_0000_0000_0000` とすると、最小粒度 4KB より napot モードのマッチ範囲は $2^{12}$（4KB）。マスクは `18'hfff` となる。

別例：`pmpaddr = 16'b1011_1111_1111_1111` の場合、napot モードのマッチ範囲は $2^{17}$（128KB）で、マスクは `18'h1ffff` となる。

## 全体ブロック図

PMP モジュールと PMA モジュールの全体ブロック図を図[@fig:PMP-overall] と図[@fig:PMA-overall] に示す。CSR Unit が CSRRW 等の CSR 命令に応答し、Frontend、Memblock、L2 TLB がレジスタのコピーを保持してアドレスチェックを担当する。CSR 書き込み信号を取り込んで内容の一貫性を保つ。

![PMP モジュール全体図](./figure/image45.png){#fig:PMP-overall}

![PMA モジュール全体図](./figure/image46.png){#fig:PMA-overall}

## インターフェイス一覧

別途のインターフェイス一覧文書を参照。

## インターフェイス時系列

ITLB と L2 TLB では PMP/PMA チェックの結果を同サイクルで返し、DTLB では次サイクルで返す。ITLB および L2 TLB の PMP モジュールのタイミングは図[@fig:PMP-time-ITLB] に示す。

![ITLB と L2 TLB PMP モジュールのタイミング](./figure/image48.svg){#fig:PMP-time-ITLB}

DTLB の PMP モジュールのタイミングは図[@fig:PMP-time-DTLB] のとおりで、静的チェック・動的チェックとも同じインターフェイスを共有する。

![DTLB PMP モジュールのタイミング](./figure/image50.svg){#fig:PMP-time-DTLB}
