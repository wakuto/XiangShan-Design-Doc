# CSR

- バージョン：V2R2
- ステータス：OK
- 日付：2025/01/20
- コミット：[xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 用語説明

Table: 用語説明

| 略語 | 正式名称 | 説明 |
| --- | --- | --- |
| CSR | Control and Status Register | 制御およびステータスレジスタ |
| Trap | Trap | トラップ、割り込みと例外の総称 |
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

CSRは機能ユニットFUとして、fenceとdivと同じintExuBlock内のExeUnitに配置されています。CSR内には主に4つのサブモジュール、すなわちcsrMod、trapInstMod、trapTvalMod、imsicが含まれています。csrModはCSRの主要な機能部品です。

trapTvalModモジュールは、主にトラップ関連のターゲット値tvalの管理と更新を担当します。入力信号flush、targetPc、clearなどに基づいてtvalを更新またはクリアし、クリア時にtvalが有効であることを保証します。モジュールには、特定の条件下でtvalが正しく更新されることを保証するための状態ロジックも含まれています。このモジュールは、csrModから発行されたtargetPcとflushからのfullTargetからソースを選択し、robIdxの順序を比較して更新またはクリアを選択し、最終的にtval情報を出力する必要があります。

trapInstModモジュールは、主にトラップの命令エンコーディング情報の管理と更新を担当します。入力信号（flush、faultCsrUop、readClearなど）に基づいてトラップ命令情報を更新またはクリアし、特定の条件下でトラップ命令情報が正しく更新されることを保証します。モジュールには、特定の条件下でトラップ命令情報が正しく更新されることを保証するための状態ロジックも含まれています。このモジュールは、decodeからの命令情報（命令エンコーディング、FtqPtr、FtqOffsetを含む）と、CSR自体が組み合わせで生成したCSR命令の命令情報からソースを選択し、FtqPtrとFtqOffsetの順序を比較して更新またはクリア、および更新のソースを決定します。flushまたはreadClearが必要な場合は無効に設定されます。最終的に、トラップ関連の命令エンコーディングと、対応するFtqPtrおよびFtqOffsetを出力します。

imsic（Incoming MSI Controller）モジュールは、主にcsrModが間接エイリアスCSR（mireg/sireg/vsireg）を介してIMSICのコンテンツにアクセスする際に相互作用し、アクセスされるCSRアドレス、特権レベルモード、書き込みデータなどの必要な情報をimsicに入力し、imsicの出力が返されるのを待ちます。csrMod自体の権限チェックで例外が発生すべきであるとすでに判断されている場合、imsicにはリクエストを送信しません。

CSRは、CSRタイプの命令およびmret、sret、ecall、ebreak、wfiなどのシステムタイプの命令の実行を担当します。Backendから命令uopとデータ情報を受け取り、実行完了後にデータとジャンプアドレスを出力します。例外が発生した場合、ルールに従ってEX_IIまたはEX_VIを設定します。

CSRは、外部割り込みコントローラCLINTおよびIMSICからMSIP、MTIP、MEIP、SEIP、VSTIP、VSEIPなどの割り込みペンディングを受信し、現在の特権レベルとそのグローバル割り込み有効化ビットに基づいて応答するかどうかを決定し、対応する割り込みを優先度順にソートし、最も優先度の高い割り込みをROBに渡して処理します。

CSRは、ROBからのTrap情報を受信し、デリゲート状況（m[e|i]delegおよびh[e|i]deleg）に基づいて特権モード（PRVM）と仮想化モード（V）をTrapを処理する特権レベルに設定し、関連するCSRの状態を変更し、実行フローをTVECに対応するTrap Handlerの開始アドレスに変更します。

CSRは、浮動小数点およびベクトルの実行を制御する設定情報（Frm、Vstart、Vl、Vtype、Vxrmなど）を保存し、浮動小数点およびベクトル命令の実行によって生成される追加の結果（Fflags、Vxsatなど）を格納します。

CSRは、カスタムデータラインを介してIMSICと相互作用し、IMSICに設定されているmireg、sireg、およびvsiregの**部分**のレジスタ（external interrupts部分）を読み書きします。

CSRは、TLBが仮想アドレスから物理アドレスへの変換を正しく実行できるように、TLBの関連信号を設定および更新します。これには、ASIDおよびVMIDの変更の検出、satp/vsatp/hgatpなどのレジスタ値の転送、mstatus/vsstatusのmxr/sum、menvcfg/henvcfgのpmmなどの権限および制御ビットの転送、仮想メモリモードの選択、および物理メモリ保護拡張の設定が含まれます。これらの設定により、TLBはさまざまな仮想メモリモードで正しくアドレス変換を実行できます。

CSRは、現在の特権モードとレジスタの状態に基づいて、命令デコードに関連する不正命令および仮想命令のフラグを設定および転送します。これらのフラグは、特定の特権モードで特定の命令が不正または仮想であるかどうかを示すために使用されます。これらのフラグにより、ハードウェアは命令デコード段階でこれらの命令を正しく処理できます。

## カスタムCSR

RISC-Vマニュアルで定義されているCSRに加えて、7つのカスタムCSRも実装しました：sbpctl、spfctl、slvpredctl、smblockctl、srnctl、mcorepwr、およびmflushpwr。

そのうち、sbpctl、spfctl、slvpredctl、smblockctl、およびsrnctlの5つのカスタムCSRはHSモードで定義され、mcorepwrおよびmflushpwrの2つのカスタムCSRはMモードで定義されています。

これらのカスタムCSRへのアクセスは、特権レベル（低特権は高特権にアクセスできない）の制約に従うだけでなく、Smstateen/Ssstateen拡張のCフィールドによるカスタムコンテンツへのアクセスの制御も受けます。

以下は、各カスタムCSRの定義です。

### sbpctl

sbpctl（Speculative Branch Prediction Control register）のアドレスは0x5C0で、HSモードで定義された読み書き可能なレジスタです。

Table: sbpctlの定義

| フィールド名 | フィールド位置 | 初期値 | 説明 |
| --- | --- | --- | --- |
| UBTB_ENABLE | 0 | 1 | UBTB_ENABLEを1に設定するとuftbが有効になります |
| BTB_ENABLE | 1 | 1 | BTB_ENABLEを1に設定すると主ftbが有効になります |
| BIM_ENABLE | 2 | 1 | BIM_ENABLEを1に設定するとbim予測器が有効になります |
| TAGE_ENABLE | 3 | 1 | TAGE_ENABLEを1に設定するとTAGE予測器が有効になります |
| SC_ENABLE | 4 | 1 | SC_ENABLEを1に設定するとSC予測器が有効になります |
| RAS_ENABLE | 5 | 1 | RAS_ENABLEを1に設定するとRAS予測器が有効になります |
| LOOP_ENABLE | 6 | 1 | LOOP_ENABLEを1に設定するとloop予測器が有効になります |
| | [63:7] | 0 | 予約済み |

### spfctl

spfctl（Speculative Prefetch Control register）のアドレスは0x5C1で、HSモードで定義された読み書き可能なレジスタです。

Table: spfctlの定義

| フィールド名 | フィールド位置 | 初期値 | 説明 |
| --- | --- | --- | --- |
| L1I_PF_ENABLE | 0 | 1 | L1命令プリフェッチャを制御し、1に設定するとプリフェッチが有効になります |
| L2_PF_ENABLE | 1 | 1 | L2プリフェッチャを制御し、1に設定するとプリフェッチが有効になります |
| L1D_PF_ENABLE | 2 | 1 | SMSプリフェッチャを制御し、1に設定するとプリフェッチが有効になります |
| L1D_PF_TRAIN_ON_HIT | 3 | 0 | SMSプリフェッチャがヒット時にトレーニングを受け入れるかどうかを制御し、1に設定するとヒット時もトレーニングを受け入れます。0に設定するとミス時のみトレーニングします |
| L1D_PF_ENABLE_AGT | 4 | 1 | SMSプリフェッチャのagtテーブルを制御し、1に設定するとagtテーブルが有効になります |
| L1D_PF_ENABLE_PHT | 5 | 1 | SMSプリフェッチャのphtテーブルを制御し、1に設定するとphtテーブルが有効になります |
| L1D_PF_ACTIVE_THRESHOLD | [9:6] | 12 | SMSプリフェッチャのアクティブページしきい値を制御します |
| L1D_PF_ACTIVE_STRIDE | [15:10] | 30 | SMSプリフェッチャのアクティブページストライドを制御します |
| L1D_PF_ENABLE_STRIDE | 16 | 1 | SMSプリフェッチャがストライドを有効にするかどうかを制御します |
| L2_PF_STORE_ONLY | 17 | 0 | L2プリフェッチャがストアのみをプリフェッチするかどうかを制御します |
| L2_PF_RECV_ENABLE | 18 | 1 | L2プリフェッチャがSMSのプリフェッチ要求を受信するかどうかを制御します |
| L2_PF_PBOP_ENABLE | 19 | 1 | L2プリフェッチャのPBOPの有効化を制御します |
| L2_PF_VBOP_ENABLE | 20 | 1 | L2プリフェッチャのVBOPの有効化を制御します |
| L2_PF_TP_ENABLE | 21 | 1 | L2プリフェッチャのTPの有効化を制御します |
| | [63:22] | 0 | 予約済み |

### slvpredctl

slvpredctl（Speculative Load Violation Predictor Control register）のアドレスは0x5C2で、HSモードで定義された読み書き可能なレジスタです。

Table: slvpredctlの定義

| フィールド名 | フィールド位置 | 初期値 | 説明 |
| --- | --- | --- | --- |
| LVPRED_DISABLE | 0 | 0 | メモリアクセス違反予測器を無効にするかどうかを制御し、1に設定すると無効になります |
| NO_SPEC_LOAD | 1 | 0 | メモリアクセス違反予測器がload命令の投機的実行を禁止するかどうかを制御し、1に設定すると禁止します |
| STORESET_WAIT_STORE | 2 | 0 | メモリアクセス違反予測器がstore命令をブロックするかどうかを制御し、1に設定するとブロックします |
| STORESET_NO_FAST_WAKEUP | 3 | 0 | メモリアクセス違反予測器が高速ウェイクアップをサポートするかどうかを制御し、1に設定すると高速ウェイクアップしません |
| LVPRED_TIMEOUT | [8:4] | 3 | メモリアクセス違反予測器のリセット間隔。このビットフィールドの値をxに設定すると、間隔は2^(10+x)になります |
| | [63:9] | 0 | 予約済み |

### smblockctl

smblockctl（Speculative Memory Block Control register）のアドレスは0x5C3で、HSモードで定義された読み書き可能なレジスタです。

Table: smblockctlの定義

| フィールド名 | フィールド位置 | 初期値 | 説明 |
| --- | --- | --- | --- |
| SBUFFER_THRESHOLD | [3:0] | 7 | sbufferのフラッシュしきい値を制御します |
| LDLD_VIO_CHECK_ENABLE | 4 | 1 | ld-ld違反チェックを有効にするかどうかを制御し、1に設定すると有効になります |
| SOFT_PREFETCH_ENABLE | 5 | 1 | ソフトプリフェッチを有効にするかどうかを制御し、1に設定すると有効になります |
| CACHE_ERROR_ENABLE | 6 | 1 | キャッシュで発生したeccエラーを報告するかどうかを制御し、1に設定すると有効になります |
| UNCACHE_WRITE_OUTSTANDING_ENABLE | 7 | 0 | uncacheのoutstandingアクセスをサポートするかどうかを制御し、1に設定すると有効になります |
| HD_MISALIGN_ST_ENABLE | 8 | 1 | ハードウェア非整列ストアを有効にするかどうかを制御します |
| HD_MISALIGN_LD_ENABLE | 9 | 1 | ハードウェア非整列ロードを有効にするかどうかを制御します |
| | [63:10] | 0 | 予約済み |

### srnctl

srnctl（Speculative Runtime Control register）のアドレスは0x5C4で、HSモードで定義された読み書き可能なレジスタです。

Table: srnctlの定義

| フィールド名 | フィールド位置 | 初期値 | 説明 |
| --- | --- | --- | --- |
| FUSION_ENABLE | 0 | 1 | fusionデコーダを有効にするかどうか、1で有効 |
| | 1 | 0 | 予約済み |
| WFI_ENABLE | 2 | 1 | wfi命令を有効にするかどうか、1で有効 |
| | [63:3] | 0 | 予約済み |

### mcorepwr

mcorepwr（Core Power Down Status Enable）のアドレスは0xBC0で、Mモードで定義された読み書き可能なレジスタです。

Table: mcorepwrの定義

| フィールド名 | フィールド位置 | 初期値 | 説明 |
| --- | --- | --- | --- |
| POWER_DOWN_ENABLE | 0 | 0 | 1は、コアがWFI（割り込み待ち）状態のときに、コアが低消費電力モードに入ることを希望することを示します |
| | [63:1] | 0 | 予約済み |

### mflushpwr

mflushpwr（Flush L2 Cache Enable）のアドレスは0xBC1で、Mモードで定義された読み書き可能なレジスタです。

Table: mflushpwrの定義

| フィールド名 | フィールド位置 | 初期値 | 説明 |
| --- | --- | --- | --- |
| FLUSH_L2_ENABLE | 0 | 0 | 1は、コアがL2キャッシュをフラッシュして一貫性状態を終了することを希望することを示します |
| L2_FLUSH_DONE | 1 | 0 | 読み取り専用ビット。1は、L2キャッシュのフラッシュが完了し、一貫性状態を終了したことを示します |
| | [63:2] | 0 | 予約済み |

## CSR例外チェック

現在のCSRの権限チェックモジュールpermitModは、権限チェックを複数のサブモジュールに分割しています：xRetPermitMod、mLevelPermitMod、sLevelPermitMod、privilegePermitMod、virtualLevelPermitMod、およびindirectCSRPermitMod。permitModはEX_IIとEX_VIの2種類の例外を生成します。また、xRetPermitModは他のサブモジュールとは異なり、xret命令実行時に発生する例外に対応し、他のサブモジュールはCSRアクセス命令に対応します。この2つの部分は相互に排他的であり、つまりxret命令実行の例外とCSRアクセス命令実行の例外が同時に発生することはありません。

そのうち、xRetPermitModはmnret/mret/sret/dret命令実行時に発生する可能性のある例外、EX_IIとEX_VIを生成します。

mLevelPermitModではEX_IIのみが発生し、いくつかのタイプの権限チェックが行われます：読み取り専用CSRへの書き込み、fs/vsが無効な場合の浮動小数点/ベクトルCSRへのアクセス、およびMモードCSR（mstateen0やmenvcfgなど）によって制御される他の低特権レベルCSRへのアクセス。

sLevelPermitModでも同様にEX_IIのみが発生し、HSモードCSR（sstateen0やscounterenなど）によって制御される他の低特権レベルCSRへのアクセスの一連のチェックが行われます。

privilegePermitModでは、低特権モードが高特権モードのCSRにアクセスできないことを保証し、現在の特権レベルとアクセス対象のCSR特権レベルに基づいてEX_IIとEX_VIの2種類の例外を生成します。

Table: 異なる特権レベルでのCSRアクセス権限チェック

| | MレベルCSR | H/VSレベルCSR | SレベルCSR | UレベルCSR |
| --- | --- | --- | --- | --- |
| MODE_M | OK | OK | OK | OK |
| MODE_VS | EX_II | EX_VI | OK | OK |
| MODE_VU | EX_II | EX_VI | EX_VI | OK |
| MODE_HS | EX_II | OK | OK | OK |
| MODE_HU | EX_II | EX_II | EX_II | OK |

virtualLevelPermitModではEX_IIとEX_VIの2種類の例外が発生し、HモードCSR（hstateen0やhenvcfgなど）によって制御される他のCSRへのアクセスの一連のチェックが行われます。

indirectCSRPermitModでも同様にEX_IIとEX_VIの2種類の例外が発生し、AlisaのエイリアスCSR（mireg、sireg、vsireg）へのアクセスの一連の権限チェックが行われます。

また、CSRアクセス時に発生する例外については、mLevelPermitMod、sLevelPermitMod、privilegePermitMod、virtualLevelPermitModの結果、つまり直接アクセスで発生した例外結果を優先し、次に間接アクセスで発生した例外結果indirectCSRPermitModを考慮します。

直接アクセスで発生した例外結果の中では、mLevelPermitModの結果を最優先し、sLevelPermitModを次に、privilegePermitModをその次に、最後にvirtualLevelPermitModを優先することを保証する必要があります。この制約は同時に、EX_IIがEX_VIよりも優先されることも保証します。

## CSR読み取り専用命令のアウトオブオーダー実行

CSR読み取り専用命令のアウトオブオーダー実行もサポートしています。ほとんどのCSRについて、CSRR命令は前の命令を待つ必要がないことに注意してください。すべてのCSRについて、CSRR命令は後の命令をブロックする必要もありません。isCsrrはCSRR命令の場合だけでなく、CSRに書き込む必要のない他のCSR命令も含むことに注意してください。

現在、以下のCSRに対して実行されるCSRR命令は、前の命令を待って順次実行する必要があります：fflags, fcsr, vxsat, vcsr, vstart, mstatus, sstatus, hstatus, vsstatus, mnstatus, dcsr。これらのCSRは、ユーザーレベルの命令によってfenceなしで変更される可能性があるため、アウトオブオーダーで実行すると誤った結果になる可能性があるため、これらのCSRに対するCSRR命令は順次実行する必要があります。

また、PMC CSRを読み取る前には必ずfence命令を実行する必要があるため、PMC CSRに対する命令を順次実行する必要はありません。

CSR命令はこれまでパイプラインなしで実行されていたため、CSRモジュール内部にステートマシンは必要ありませんでした。一部のCSR読み取り専用命令のパイプライン高速化最適化を追加した後、整数レジスタファイルのアービタがCSRR命令が正常に実行される前に書き込み要求を許可する必要があるため、ステートマシンが必要になります。

この有限ステートマシンには、アイドル（s_idle）、IMSIC待ち（s_waitIMSIC）、完了（s_finish）の3つの状態があります。

現在の状態がs_idleの場合、有効な入力validがあり、かつflush信号がある場合、次の状態はs_idleのままです。有効な入力validがあり、かつAIAへの非同期アクセスが必要な場合、次の状態はs_waitIMSICになります。有効な入力validがある場合、次の状態はs_finishになります。その他の場合はs_idleを維持します。

現在の状態がs_waitIMSICの場合、flush信号がある場合、次の状態はs_idleに戻ります。AIAから読み取り有効信号が返され、かつ出力がreadyの場合、次の状態はs_idleに戻ります。そうでない場合、出力がreadyでない場合、次の状態はs_finishになり、出力を待ちます。その他の場合はs_waitIMSICを維持します。

現在の状態がs_finishの場合、flush信号または出力ready信号がある場合、次の状態は両方ともs_idleに戻ります。そうでない場合はs_finishを維持します。
