# Debug Module

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット: [xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 用語説明

表: 用語説明

| 略称 | 正式名称 | 説明 |
| ---- | -------- | ---- |
| DM   | Debug Module           | デバッグモジュール |
| DTM  | Debug Transport Module | デバッグトランスポートモジュール |
| DMI  | Debug Module Interface | デバッグモジュールインターフェース |

## パラメータ設計

表: パラメータ設計

| パラメータ             | 既定値     | 説明 |
| ---------------------- | ---------- | ---- |
| baseAddress            | 0x38020800 | Debug Module の MMIO ベースアドレス |
| nDMIAddrSize           | 7          | DMI アドレス幅 |
| nProgramBufferWords    | 16         | Program Buffer のワード数 |
| nAbstractDataWords     | 4          | Abstract Commands のワード数 |
| hasBusMaster           | true       | system bus master を持つか |
| maxSupportedSBAccess   | 64         | sysbus の最大アクセス幅 |
| supportQuickAccess     | false      | QuickAccess をサポートするか |
| supportHartArray       | true       | hart array をサポートするか |
| nHaltGroups            | 1          | halt group の数 |
| nExtTriggers           | 0          | external trigger の数 |
| hasHartResets          | true       | 選択した hart をリセットするか |
| hasImplicitEbreak      | false      | 暗黙の ebreak をサポートするか |

## 全体設計

### 全体ブロック図

[@fig:DM] に示すように：

![DebugModule の概要](./figure/DM-Overview.svg){#fig:DM}

### マルチクロックドメイン

[@fig:multiclock] に示すように：

![DebugModule のマルチクロックドメイン](./figure/MultiClock.svg){#fig:multiclock}

### Debug MMIO

[@tbl:debug-mmio] に示すように：

Table: Debug MMIO アドレス空間 {#tbl:debug-mmio}

| アドレス (ベース 0x3802_0000) | 名称        | 説明 | このアドレスに格納される内容 |
| ------------------------------ | ----------- | ---- | ------------------------------ |
| 0x800                          | debugEntry  | Debug 入口アドレス / debug ROM のベースアドレス | |
| 0x808                          | debugException | dmode 実行時の例外入口アドレス | |
| 0x100                          | HALTED      |                                    | dmode に入った hart の hartid (debug module が取得) |
| 0x104                          | GOING       |                                    | `whereto`。最終的に ABSTRACT へ分岐して実行 |
| 0x108                          | RESUMING    |                                    | `dret` を実行 |
| 0x10c                          | EXCEPTION   |                                    | |
| 0x300                          | WHERETO     | このアドレスに命令を格納           | dm が生成する ABSTRACT へのジャンプ命令 |
| 0x380                          | DATA        | DATA のベースアドレス（ld/st 用）   | データ交換 |
| DATA-4*nProgBuf                | PROGBUF     | progbuf0 のアドレス                | dm が生成する命令（go 前に準備） |
| DATA-4                         | IMPEBREAK   | 暗黙の ebreak 命令                 | |
| PROGBUF - 4 * nAbstractInst    | ABSTRACT    | AbstractInstructions               | dm が生成する命令（go 前に準備） |
| 0x400                          | FLAGS       | hartid に対応する flag のベースアドレス。各 flag は 8bit、0x400 は hartid=0 の flag アドレス | 下位 2bit のみ有効。下位から 2 番目が resume、最下位が go。アドレス空間は 1k（0x400 → 0x4FF） |

## モジュール設計

### Debug Module

昆明湖における現行の debug 実装は次のとおり。

* CPU リセット直後から debug mode に入り、最初の命令からのデバッグをサポートする。
* 単一コアと選択した複数コアに対し、halt・resume・reset の実行制御をサポートする。
* シングルステップデバッグをサポートする。
* `stopcount` と `stoptime` をサポートする。
* ソフトウェアブレークポイント（`ebreak` 命令）、ハードウェアブレークポイント（trigger）、メモリブレークポイント（trigger）をサポートする。
* GPR・CSR・メモリアクセスをサポートし、progbuf と sysbus の 2 系統のアクセス手段を提供する。
* debug interrupt（`haltreq`、`haltgroup`、`halt-on-reset`）、trigger fire、`ebreak`、`singlestep`、クリティカルエラーなどの経路で debug mode へ遷移できる。

### Trigger Module

昆明湖における現行の trigger module 実装は次のとおり。

* 昆明湖 trigger module が実装する debug 関連 CSR は下表のとおり。
* trigger の既定構成数は 4（ユーザーが任意に変更可能）。
* mcontrol6 タイプの命令およびメモリアクセスに対する trigger をサポートする。
* `match` タイプは等しい・以上・未満の 3 種類をサポート（一部のベクトルメモリアクセスでは等しいのみ）。
* address マッチのみサポートし、data マッチは未対応。
* `timing = before` のみサポート。
* trigger のチェインは 1 組のみサポート。
* trigger による重複 breakpoint 例外を防ぐため、`xSTATUS.xIE` による制御をサポート。
* H 拡張におけるソフト／ハードブレークポイントおよびウォッチポイントをサポート。
* 原子命令に対するメモリアクセストリガーをサポート。

以下の表は、昆明湖がサポートするメモリアクセス命令のマイクロアーキテクチャ上のアクセス粒度と trigger のマッチ粒度を示す。スカラ命令および要素粒度でアクセスするベクトル命令は `>=`、`=`、`<` をサポートし、それ以外のベクトル命令は `=` のみをサポートする。ベクトル命令では、より若い要素インデックスで trigger fire が発生した場合（action が breakpoint でも debug でも）を対象とする。

表: メモリアクセス粒度と trigger マッチ粒度

| 命令タイプ                    | メモリアクセス粒度          | trigger マッチ粒度 |
| ----------------------------- | --------------------------- | ------------------ |
| スカラメモリアクセス命令      | 命令（要素）                | 要素のリトルエンディアンアドレスをチェック、`>=` `=` `<` をサポート |
| 原子命令（lr/sc）             | 命令（要素）                | 同上。`lr` は load、`sc` は成否に関わらず store とみなす |
| 原子命令（amo）               | 命令（要素）                | 同上。`vaddr` 取得時に load と store を同時にチェック |
| ベクトル命令（unit-stride）   | ベクトルレジスタ幅 (128bit) | 8bit 粒度で範囲内をチェック、`=` のみ |
| ベクトル命令（whole）         | ベクトルレジスタ幅 (128bit) | 8bit 粒度で範囲内をチェック、`=` のみ |
| ベクトル命令（fof unit-stride）| ベクトルレジスタ幅 (128bit) | 8bit 粒度で範囲内をチェック、要素 0 に対して `=` のみ |
| ベクトル命令（segment）       | 要素                         | 各要素のリトルエンディアンアドレスをチェック、`=` のみ |
| その他のベクトル命令          | 要素                         | 各要素のリトルエンディアンアドレスをチェック、`>=` `=` `<` をサポート |

表: 昆明湖が実装する debug 関連 CSR

| 名称              | アドレス | R/W | 説明                         | リセット値 |
| ----------------- | -------- | --- | ---------------------------- | ---------- |
| Tselect           | 0x7A0    | RW  | trigger 選択レジスタ         | 0x0        |
| Tdata1 (Mcontrol6)| 0x7A1    | RW  | trigger data1                | 0xF0000000000000000 |
| Tdata2            | 0x7A2    | RW  | trigger data2                | 0x0        |
| Tinfo             | 0x7A4    | RO  | trigger info                 | 0x40       |
| Dcsr              | 0x7B0    | RW  | Debug Control and Status     | 0x40000003 |
| Dpc               | 0x7B1    | RW  | Debug PC                     | 0x0        |
| Dscratch0         | 0x7B2    | RW  | Debug Scratch Register 0     | -          |
| Dscratch1         | 0x7B3    | RW  | Debug Scratch Register 1     |            |
| mcontext          | 0x7A8    | RW  | Machine Context              | -          |
| hcontext          | 0x6A8    | RW  | Hypervisor Context           | -          |
| scontext          | 0x5A8    | RW  | Supervisor Context           | -          |

### デバッグフロー例

#### CSR アクセス

Debug Module での CSR アクセスは abstract command と progbuf を組み合わせて行う。abstract command に基づいて ABSTRACT と PROGBUF（いずれも連続領域）に命令を生成し、CPU に実行させることで CSR にアクセスする。ABSTRACT では `lw` / `st` を生成し、MMIO アドレスと GPR `s0` / `s1` 間のデータ交換を担当する。PROGBUF では CSR の読み書き命令を生成する。`mstatus` レジスタアクセスを例に説明する。

1. ソフトウェアが `mstatus` 書き込み命令を発行すると、JtagProbe → JtagDTM → DMI を経て DMI 操作に変換される。
2. DMI 操作が dmi2tl を通って Debug Module 内部の制御信号を更新し、`DMI_COMMAND` を `mstatus` 書き込みコマンドに設定する。
3. OpenOCD は `s0` / `fp` を読み出して保存し、progbuffer に CSR 書き込み命令を準備する。
4. ABSTRACT（`ld`）を実行して `DATA` の値を `s0` に読み込む。
5. PROGBUF（CSR 書き込み命令）を実行する。末尾の `ebreak` により parking loop に復帰する。

   読み出し時は以下の手順となる。
6. PROGBUF（CSR 読み出し命令）で CSR の値を `s0` に読み込む。
7. ABSTRACT（`st`）で `s0` を `DATA` へ書き戻す。

#### ハードウェアブレークポイント

ブレークポイント設定時のソフト／ハード協調フローを以下に示す。

1. halt コマンドが JtagProbe → JtagDTM → DMI を経て DMI 操作となる。
2. DMI 操作が dmi2tl を通って Debug Module 制御信号を更新し、hart へ外部 debug 割り込みを送信する。割り込みは hart 内の CSR モジュールへ到達する。
3. CSR モジュールは外部 debug 割り込みを処理し、hart は Debug Module 入口へトラップして DMode に入る（Debug Module MMIO 参照）。
4. DMode に入った hart は debug ROM を実行し、自身の hartid を HALTED に書き込んで Debug Module に通知する。Debugger は DMode 下で hart を制御できる。
5. ハードウェアブレークポイント設定コマンドが発行されると、hart は WHERETO にジャンプし、ABSTRACT と PROGBUF を協調させて CSR 命令を実行し trigger CSR を設定する。末尾の `ebreak` により再び Debug Module 入口へ戻る。
6. resume コマンドにより hart は `_resume` を実行して `dret` で DMode から復帰し、halt 前の実行に戻る（resume 前に step を挟み単一命令を commit させた後、single step 例外で debug mode に戻る手順は OpenOCD の実装を参照）。
7. hart がブレークポイントに到達すると PC が trigger CSR のアドレスと一致し trigger が発火、hart は再度 DMode に入り debug ROM を実行してデバッガの操作を待つ。
