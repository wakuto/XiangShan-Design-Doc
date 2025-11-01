# BypassNetwork

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/02/27
- コミット: [xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 用語説明

表: 用語説明

| 正式名称 | 説明 |
|---|---|
| BypassNetWork | バイパスネットワーク |

## サブモジュールリスト

表: サブモジュールリスト

| サブモジュール | 説明 |
|---|---|
| ImmExtracter | 即値生成モジュール |
| UIntExtracter | UIntデコードモジュール |

## 機能

BypassNetWorkはDataPath、Exuパイプラインステージ間に位置し、主に機能ユニットにソースオペランドを提供するために使用されます。現在、27の機能ユニットがあり、合計71のソースオペランドがあります。

まず、フォワーディング/バイパス/2段バイパスが可能なソースオペランドについて：

Datapathから入力されるExuSource情報に基づき、UintExtractがワンホットコードを抽出し、機能ユニットからのバイパスデータ候補を選択します。現在のウェイクアップ設定は以下の表の通りです。

表: 現在のウェイクアップ設定1

| ソース | シンク |
|---|---|
| ALU0 | ALU0, BJU0, ALU1, BJU1, ALU2, BJU2, ALU3, BJU3, LDU0, LDU1, LDU2, STA0, STA1, STD0, STD1 |
| ALU1 | ALU0, BJU0, ALU1, BJU1, ALU2, BJU2, ALU3, BJU3, LDU0, LDU1, LDU2, STA0, STA1, STD0, STD1 |
| ALU2 | ALU0, BJU0, ALU1, BJU1, ALU2, BJU2, ALU3, BJU3, LDU0, LDU1, LDU2, STA0, STA1, STD0, STD1 |
| ALU3 | ALU0, BJU0, ALU1, BJU1, ALU2, BJU2, ALU3, BJU3, LDU0, LDU1, LDU2, STA0, STA1, STD0, STD1 |
| LDU0 | ALU0, BJU0, ALU1, BJU1, ALU2, BJU2, ALU3, BJU3, LDU0, LDU1, LDU2, STA0, STA1, STD0, STD1 |
| LDU1 | ALU0, BJU0, ALU1, BJU1, ALU2, BJU2, ALU3, BJU3, LDU0, LDU1, LDU2, STA0, STA1, STD0, STD1 |
| LDU2 | ALU0, BJU0, ALU1, BJU1, ALU2, BJU2, ALU3, BJU3, LDU0, LDU1, LDU2, STA0, STA1, STD0, STD1 |

表: 現在のウェイクアップ設定2

| ソース | シンク |
|---|---|
| FEX0 | FEX0, FEX1, FEX2, FEX3, FEX4 |
| FEX2 | FEX0, FEX1, FEX2, FEX3, FEX4 |
| FEX4 | FEX0, FEX1, FEX2, FEX3, FEX4 |

> ベクトル浮動小数点およびメモリアクセスユニット間の2段バイパスは、現在一時的にキャンセルされています。

次に、ソースオペランドが即値の部分については、datapathからの即値情報に基づき、ImmExtractorが64ビットの即値を組み立てて生成します。

最後に、datapathのデータソース情報に基づき、すべての可能なデータソース（フォワーディング、バイパス、2段バイパス、v0、レジスタファイル、即値、regcache、0番レジスタ）からソースオペランドを選択し、機能ユニットに渡します。

また、ジャンプ機能ユニットについては、一部のpcoffsetロジックもバイパスネットワーク内に配置され、即値情報も同様にImmExtractorによって組み立て生成されます。

具体的な設計は[@fig:BypassNetwork]を参照してください。

## 全体ブロック図

BypassNetWorkの全体ブロック図は以下の通りです。

![BypassNetwork](./figure/BypassNetwork.svg){#fig:BypassNetwork}

## モジュール設計

### 2次モジュール ImmExtracter

このモジュールは64ビットの即値を生成する責任があります。まず、以下のマッピングに従って即値を32ビット形式にマッピングし、その後、結果を符号拡張して64ビットの即値にします。

表: 即値マッピング

| SelImm | ImmUnion | Immlen | extracter |
|:---:|:---:|:---:|---|
| IMM_I | I | 12 | SignExt(imm(len - 1, 0), 32) |
| IMM_S | S | 12 | SignExt(imm, 32) |
| IMM_SB | B | 12 | SignExt(Cat(imm, 0.U(1.W)), 32) |
| IMM_U | U | 20 | Cat(imm(len - 1, 0), 0.U(12.W)) |
| IMM_UJ | J | 20 | SignExt(Cat(imm, 0.U(1.W)), 32) |
| Z | Z | 22 | imm |
| IMM_B6 | B6 | 6 | ZeroExt(imm, 32) |
| IMM_VSETVLI | VSETVLI | 11 | SignExt(imm, 32) |
| IMM_VSETIVLI | VSETIVLI | 15 | SignExt(imm, 32) |
| IMM_OPIVIS | OPIVIS | 5 | SignExt(imm, 32) |
| IMM_OPIVIU | OPIVIU | 5 | ZeroExt(imm, 32) |
| IMM_LUI32 | LUI32 | 32 | imm(31, 0) |
| IMM_VRORVI | VRORVI | 6 | ZeroExt(imm, 32) |

### 2次モジュール UIntExtracter

このモジュールはtoExuOH機能を提供します。UIntに圧縮されたソースオペランドのバイパスソースのexuidxをワンホット形式にデコードする責任があります。

ソースオペランドのバイパスソースのexusource内の機能ユニット番号は、発行段階で2回の圧縮を経験します。

* まず、27の機能ユニットを示すワンホットコードを、バイパスウェイクアップの可能なソースに基づいて、7/3個の機能ユニットのワンホットコードに圧縮します。
* 次に、7/3個の機能ユニットのワンホットコードをUInt形式に圧縮し、合計3/2ビットのUIntになります。

そのため、バイパスネットワークでは、DataPathからの圧縮後のexusourceに対して2回の解凍が必要です。

* まず、3/2ビットのexusourceをワンホットコードに解凍します。
* 次に、圧縮されたワンホットコードを、現在の機能ユニットの可能なウェイクアップソースに基づいて、27個の機能ユニットを示すワンホットコードに解凍します。

最初の解凍操作については、toExuOHで単純なシフト（ウェイクアップソースとソースオペランドは1対1で対応）によって完了できます。

UIntExtracterは2番目の解凍操作を担当し、以下のマッピングを完了します。

表: ウェイクアップソースのワンホットコードマッピング(1)

| EncodedExuOH | ExtractExuOH |
| :----------: | :----------: |
|   ALU0(0)   |      0      |
|   ALU1(1)   |      2      |
|   ALU2(2)   |      4      |
|   ALU3(3)   |      6      |
|   LDU0(4)   |      20      |
|   LDU1(5)   |      21      |
|   LDU2(6)   |      22      |

Table: ウェイクアップソースワンホットコードマッピング(1)

| EncodedExuOH | ExtractExuOH |
| :----------: | :----------: |
|   FEX0(0)   |      8      |
|   FEX1(1)   |      10      |
|   FEX2(2)   |      12      |
