# CSR

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット: [xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 用語説明

表: 用語説明

| 略語 | 正式名称 | 説明 |
|---|---|---|
| CSR | Control and Status Register | 制御およびステータスレジスタ |
| Trap | Trap | トラップ、割り込み、例外の総称 |
| ROB | Reorder Buffer | リオーダーバッファ |
| PRVM | Privilege Mode | 特権モード、M、S、Uを含む |
| VM/V | Virtual Mode | 仮想化モード、仮想化モードではVSとVUの2つの特権レベルを持つ |
| EX_II | Illegal Instruction Exception | 不正命令例外 |
| EX_VI | Virtual Instruction Exception | 仮想命令例外 |
| TVEC | Trap Vector | Trapハンドラの入口設定レジスタ、m/hs/vsの3つのモードで独立 |
| IMSIC | Incoming MSI Controller | 割り込みメッセージコントローラ、The RISC-V Advanced Interrupt Architectureで定義 |

## 設計仕様

CSR命令の実行をサポート

CSR読み取り専用命令の実行をサポート

CSR読み取り専用命令のアウトオブオーダー実行をサポート

mret、sret、ecall、ebreak、wfiなどのシステムレベル命令の実行をサポート

割り込みを受信し、最も優先度の高い割り込みを選択してROBに送信して処理することをサポート

EX_IIおよびEX_VIの2種類の例外の生成をサポート

ROB Trap（割り込み+例外）からの受信と処理をサポート

riscv-privileged-spec仕様に準拠したCSR実装をサポート

割り込みと例外のデリゲートをサポート

SmaiaおよびSsaia拡張をサポート

SdtrigおよびSdext拡張をサポート

H拡張をサポート

仮想化割り込みをサポート

外部割り込みの受信と処理をサポート

## 機能

CSRは機能ユニット（FU）として、fenceおよびdivと同じExeUnit内のintExuBlockに位置しています。CSR内には主に4つのサブモジュール、すなわちcsrMod、trapInstMod、trapTvalMod、およびimsicが含まれています。csrModはCSRの主要な機能部品です。

trapTvalModモジュールは、主にトラップ関連のターゲット値tvalの管理と更新を担当します。flush、targetPc、clearなどの入力信号に基づいてtvalを更新またはクリアし、クリア時にtvalが有効であることを保証します。モジュールには、特定の条件下でtvalが正しく更新されることを保証するための状態ロジックも含まれています。このモジュールは、csrModから発行されたtargetPcとflushからのfullTargetからソースを選択し、robIdxの順序を比較して更新またはクリアを決定し、最終的にtval情報を出力する必要があります。

trapInstModモジュールは、主にトラップの命令エンコーディング情報の管理と更新を担当します。flush、faultCsrUop、readClearなどの入力信号に基づいてトラップ命令情報を更新またはクリアし、特定の条件下でトラップ命令情報が正しく更新されることを保証します。モジュールには、特定の条件下でトラップ命令情報が正しく更新されることを保証するための状態ロジックも含まれています。このモジュールは、decodeからの命令情報（命令エンコーディング、FtqPtr、FtqOffsetを含む）と、CSR自体が組み合わせで生成したCSR命令の命令情報からソースを選択し、FtqPtrとFtqOffsetの順序を比較して更新またはクリア、および更新のソースを決定します。flushまたはreadClearが必要な場合は無効に設定されます。最終的に、トラップ関連の命令エンコーディングと、対応するFtqPtrおよびFtqOffsetを出力します。

imsic（Incoming MSI Controller）モジュールは、主にcsrModが間接エイリアスCSR（mireg/sireg/vsireg）を介してIMSICのコンテンツにアクセスする際に相互作用し、アクセスされるCSRアドレス、特権レベルモード、書き込みデータなどの必要な情報をimsicに入力し、imsicの出力が返されるのを待ちます。csrMod自体の権限チェックで例外が発生すべきであるとすでに判断されている場合、imsicにはリクエストを送信しません。

CSRは、CSRタイプの命令およびmret、sret、ecall、ebreak、wfiなどのシステムタイプの命令の実行を担当します。Backendから命令uopとデータ情報を受け取り、実行完了後にデータとジャンプアドレスを出力します。例外が発生した場合、ルールに従ってEX_IIまたはEX_VIを設定します。

CSRは、外部割り込みコントローラCLINTおよびIMSICからMSIP、MTIP、MEIP、SEIP、VSTIP、VSEIPなどの割り込みペンディングを受信し、現在の特権レベルとそのグローバル割り込み有効化ビットに基づいて応答するかどうかを決定し、対応する割り込みを優先度順にソートし、最も優先度の高い割り込みをROBに渡して処理します。

CSRは、ROBからのTrap情報を受信し、デリゲート状況（m[e|i]delegおよびh[e|i]deleg）に基づいて特権モード（PRVM）と仮想化モード（V）をTrapを処理する特権レベルに設定し、関連するCSRの状態を変更し、実行フローをTVECに対応するTrap Handlerの開始アドレスに変更します。

CSRは、浮動小数点およびベクトルの実行を制御する設定情報（Frm、Vstart、Vl、Vtype、Vxrmなど）を保存し、浮動小数点およびベクトル命令の実行によって生成される追加の結果（Fflags、Vxsatなど）を格納します。

CSRは、カスタムデータラインを介してIMSICと相互作用し、IMSICに設定されているmireg、sireg、およびvsiregの**一部**のレジスタ（external interrupts部分）を読み書きします。

CSRは、TLBが仮想アドレスから物理アドレスへの変換を正しく実行できるように、TLBの関連信号を設定および更新します。これには、ASIDおよびVMIDの変更の検出、satp/vsatp/hgatpなどのレジスタ値の転送、mstatus/vsstatusのmxr/sum、menvcfg/henvcfgのpmmなどの権限および制御ビットの転送、仮想メモリモードの選択、および物理メモリ保護拡張の設定が含まれます。これらの設定により、TLBはさまざまな仮想メモリモードで正しくアドレス変換を実行できます。

CSRは、現在の特権モードとレジスタの状態に基づいて、命令デコードに関連する不正命令および仮想命令のフラグを設定および転送します。これらのフラグは、特定の特権モードで特定の命令が不正または仮想であるかどうかを示すために使用されます。これらのフラグにより、ハードウェアは命令デコード段階でこれらの命令を正しく処理できます。

## カスタムCSR

RISC-Vマニュアルで定義されているCSRに加えて、7つのカスタムCSRも実装しました：sbpctl、spfctl、slvpredctl、smblockctl、srnctl、mcorepwr、およびmflushpwr。

そのうち、sbpctl、spfctl、slvpredctl、smblockctl、およびsrnctlの5つのカスタムCSRはHSモードで定義され、mcorepwrおよびmflushpwrの2つのカスタムCSRはMモードで定義されています。

これらのカスタムCSRへのアクセスは、特権レベル（低特権は高特権にアクセスできない）の制約に従うだけでなく、Smstateen/Ssstateen拡張のCフィールドによるカスタムコンテンツへのアクセスの制御も受けます。

以下は、各カスタムCSRの定義です。

### sbpctl

sbpctl（Speculative Branch Prediction Control register）のアドレスは0x5C0で、HSモードで定義された読み書き可能なレジスタです。

表: sbpctlの定義

| フィールド名 | フィールド位置 | 初期値 | 説明 |
|---|---|---|---|
| UBTB_ENABLE | 0 | 1 | UBTB_ENABLEを1に設定するとuftbが有効になります |
| BTB_ENABLE | 1 | 1 | BTB_ENABLEを1に設定すると主ftbが有効になります |
| BIM_ENABLE | 2 | 1 | BIM_ENABLEを1に設定するとbim予測器が有効になります |
| TAGE_ENABLE | 3 | 1 | TAGE_ENABLEを1に設定するとTAGE予測器が有効になります |
| SC_ENABLE | 4 | 1 | SC_ENABLEを1に設定するとSC予測器が有効になります |
