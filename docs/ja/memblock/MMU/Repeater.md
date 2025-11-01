# 二段モジュール Repeater

Repeater は次のモジュールで構成される。

* PTWFilter itlbRepeater1
* PTWRepeaterNB itlbRepeater2
* PTWRepeaterNB itlbRepeater3
* PTWNewFilter dtlbRepeater

## 設計仕様

1. L1 TLB と L2 TLB 間で PTW 要求と応答を転送できること
2. 重複する要求をフィルタリングできること
3. TLB ヒント機構をサポートすること

## 機能

### L1 TLB の PTW 要求を L2 TLB に転送

L1 TLB と L2 TLB の間には物理距離があり、長い配線遅延が発生する。このため Repeater モジュールで中間に拍を挿入する。ITLB と DTLB は複数の outstanding 要求を扱えるため、Repeater は MSHR に似た役割を担い、重複要求を Filter で抑制する。Filter の項数は L2 TLB の並列度を左右する（5.1.1.2 節参照）。

昆明湖アーキテクチャでは、L2 TLB は memblock モジュール内にあるが ITLB・DTLB の双方から距離がある。香山の MMU には 3 つの itlbRepeater と 1 つの dtlbRepeater があり、L1 TLB と L2 TLB の間に拍を挿入する。各段は valid-ready 信号で握手する。ITLB は PTW 要求と仮想ページ番号を itlbRepeater1 に送り、仲裁後に itlbRepeater2、itlbRepeater3 を経由して L2 TLB に伝える。L2 TLB は対応する仮想ページ番号に対して物理ページ番号、ページテーブルの権限ビット、階層、例外の有無などを返し、itlbRepeater3、itlbRepeater2、itlbRepeater1 を通じて ITLB に戻す。DTLB と dtlbRepeater のやり取りも同様で、dtlbRepeater と itlbRepeater1 は Filter モジュールとして L1 TLB の重複要求を統合する。昆明湖アーキテクチャでは ITLB・DTLB がいずれもノンブロッキングアクセスであるため、各 repeater はブロッキング Repeater として動作する。

### 重複する要求のフィルタリング

ITLB・DTLB は複数チャネルを備えており、チャネル間やチャネル内でミス要求が重複する場合がある。通常のアービタのみで 1 件ずつ処理すると、他の要求が再送されて再び miss となり L2 TLB に流れ込み、L2 TLB の利用率が下がるうえプロセッサ資源を占有する。このため多入力単出力のキューである Filter モジュールを用いて重複要求を除去する。

昆明湖アーキテクチャの dtlbRepeater は load entry、store entry、prefetch entry の 3 部構成で、load dtlb・store dtlb・prefetch dtlb からの要求をそれぞれ対応する entry に送って処理する。3 種類の entry はラウンドロビン仲裁で L2 TLB へ要求を流す。itlbrepeater は ITLB から届く全要求を確認して重複を排除するが、dtlbRepeater がチェックする粒度は entry 単位であり、同じ dtlb（load、store、prefetch）内での重複のみを排除する。異なる dtlb 間（例えば load dtlb と store dtlb）が L2 TLB に送る要求は重複する可能性が残る。

### TLB ヒント機構のサポート

![TLB ヒントの概略図](./figure/image28.png)

TLB がヒットしたときは load 命令のライフサイクルに影響しない（loadunit が 0 拍目に TLB を参照し、1 拍目に結果が返る）。TLB ミス時は L2 TLB やメモリ上のページテーブルを順に検索して結果を得るが、load 命令は TLB ミス後に load replay queue へ移り、再送されて TLB で物理アドレスが得られてから後段処理に進む。

よって load 命令をいつ再送するかが遅延短縮の鍵である。再送が遅れると TLB リフィル周期を短縮しても性能向上が得られない。昆明湖アーキテクチャでは TLB ヒント機構を実装し、TLB miss が発生した load を狙ってウェイクアップする。具体的には load_s0 段で vaddr を送って miss すると、load_s1 段で miss 情報が返ると同時に dtlbRepeater へ通知され、dtlbRepeater が処理する。

dtlbRepeater の処理結果は MSHRid または full 信号である。load entry では新要求が既存項と重複するかを確認し、重複する場合はその項の MSHRid を返す。重複しなければ空き項の有無を確認し、空きがあれば MSHRid、なければ full を返す。2 つの load チャネルが同じ仮想アドレスで同時に要求した場合は loadunit(0) の MSHRid を優先する。

TLB miss で load replay queue に入った命令はヒントによる再送を待つ。ウェイクアップが来なければデッドロックするため、DTLB が dtlbRepeater に要求を送った際に空き項がなければ full 信号を返し、該当 load の PTW 要求は受け付けられないことを示す。load replay queue はヒントがなくても再送できるようにし、デッドロックを防ぐ必要がある。また、リフィル項が dtlb または dtlbRepeater に到達してまだ dtlb へ書き込まれていない場合も loadunit に full を返し、再送を促す。

load_s2 段で dtlbRepeater は MSHRid を loadunit に返し、load_s3 段で load replay queue に書き込む。MSHRid が有効なら、PTW リフィル情報が dtlbRepeater に保持されている同じ MSHRid にヒットするのを待ち、ヒットした時点でヒントを送って再送を指示する。その際に dtlb にヒットできる。1 件の PTW リフィル要求が複数の MSHR entry に対応する場合（例えば 2 つの VPN が同じ 2M 空間にあり、PTW リフィルのページサイズが 2MB のとき）は、dtlbRepeater が replay_all 信号を送って dtlb miss で停止している全 load を再送させる。このケースは稀であり性能低下はほぼない。

## 全体ブロック図

Repeater の全体図を [@fig:MMU-repeater-overall] に示す。3 つの itlbRepeater と 1 つの dtlbRepeater が L1 TLB と L2 TLB の間に拍を挿入し、各段は valid-ready 信号で握手する。Repeater は上流から ITLB・DTLB の PTW 要求を受け取り、下流へ L2 TLB に送る。dtlbRepeater と itlbRepeater1 は Filter モジュールとして重複要求を統合する。

itlbRepeater1 を除く 2 段は単に拍を挿入する役割で、必要な段数は物理距離で決まる。昆明湖アーキテクチャでは L2 TLB が Memblock にあり Frontend の ITLB とは距離があるため Frontend に 2 段、Memblock に 1 段の repeater を配置する。一方 DTLB は Memblock 内にあり L2 TLB との距離が短いため 1 段でタイミング要件を満たせる。

![Repeater モジュール全体図](./figure/image29.png){#fig:MMU-repeater-overall}

## インターフェイス一覧

詳細はインターフェイス一覧ドキュメントを参照。

## インターフェイス時系列

### Repeater1 と L1 TLB のインターフェイス時系列

[@sec:L1TLB-tlbRepeater-time] [TLB と tlbRepeater のインターフェイス時系列](./L1TLB.md#sec:L1TLB-tlbRepeater-time) を参照。

### itlbRepeater3 および dtlbRepeater1 と L2 TLB のインターフェイス時系列

itlbRepeater3 と dtlbRepeater1 が L2 TLB とやり取りする時系列を [@fig:MMU-tlbrepeater-time-L2TLB] に示す。両者は valid-ready 信号でハンドシェイクし、Repeater が L1 TLB からの PTW 要求と仮想アドレスを L2 TLB に送り、L2 TLB は物理アドレスとページテーブル情報を返す。

![itlbRepeater3 および dtlbRepeater1 と L2 TLB のインターフェイス時系列](./figure/image31.svg){#fig:MMU-tlbrepeater-time-L2TLB}

### 多段 itlbRepeater 間のインターフェイス時系列

多段 itlbRepeater 間の時系列を [@fig:MMU-multi-itlbrepeater-time] に示す。各段は valid-ready 信号で握手する。

![多段 itlbRepeater 間のインターフェイス時系列](./figure/image33.svg){#fig:MMU-multi-itlbrepeater-time}
