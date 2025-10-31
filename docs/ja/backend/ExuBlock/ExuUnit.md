# ExuUnit

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット：[xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 用語解説

表: FUの用語解説

| FU | 説明 |
| --- | --- |
| alu | 算術論理ユニット |
| mul | 乗算ユニット |
| bku | B拡張ビット操作および暗号化ユニット |
| brh | 条件分岐ユニット |
| jmp | 直接ジャンプユニット |
| i2f | 整数から浮動小数点への変換ユニット |
| i2v | 整数をベクターに移動するユニット |
| VSetRiWi | 整数を読み書きするVSetユニット |
| VSetRiWvf | 整数を読み込み、ベクターを書き込むvsetユニット |
| csr | 制御およびステータスレジスタユニット |
| fence | メモリ同期命令ユニット |
| div | 除算ユニット |
| falu | 浮動小数点算術論理ユニット |
| fcvt | 浮動小数点変換ユニット |
| f2v | 浮動小数点をベクターに移動するユニット |
| fmac | 浮動小数点融合積和 |
| fdiv | 浮動小数点除算ユニット |
| vfma | ベクター浮動小数点融合積和ユニット |
| vialu | ベクター整数算術論理ユニット |
| vimac | ベクター整数積和ユニット |
| vppu | ベクター順列処理ユニット |
| vfalu | ベクター浮動小数点算術論理ユニット |
| vfcvt | ベクター浮動小数点変換ユニット |
| vipu | ベクター整数処理ユニット |
| VSetRvfWvf | ベクターを読み書きするvsetユニット |
| vfdiv | ベクター浮動小数点除算ユニット |
| vidiv | ベクター整数除算ユニット |

## 入出力

`flush` は、valid信号を持つリダイレクト入力です。

`in` は、特定のExeUnitパラメータ設定に従って生成されるExuInputです。

`out` は、特定のExeUnitパラメータ設定に基づいて生成されるExuOutputです。

`csrio`、`csrin`、および`csrToDecode`は、ExeUnitに`CSR`が存在する場合にのみ存在します。

同様に、`fenceio`は、ExeUnitに`fence`が存在する場合にのみ存在します。`frm`は、ExeUnitで`frm`がsrcとして必要な場合にのみ存在します。`vxrm`は、ExeUnitで`vxrm`がsrcとして必要な場合にのみ存在します。

`vtype`、`vlIsZero`、および`vlIsVlmax`は、このExeUnitでVconfigを書き込む必要がある場合にのみ存在します。

さらに、ExeUnitにJmpFuまたはBrhFuが存在する場合、命令アドレス変換タイプ`instrAddrTransType`も入力する必要があります。

## 機能

各ExuUnitは、その設定パラメータに基づいて一連の対応するFUモジュールを生成します。

`busy`は、現在のExeUnitがビジー状態であるかどうかを示します。決定論的なレイテンシを持つExeUnitの場合、レイテンシが固定されており、すべてのタスクが順序通りに完了するため、機能ユニットがビジーとしてマークされることはありません。この場合、`busy`は直接falseに設定され、機能ユニットが常にアイドルであることを示します。非決定論的なレイテンシを持つExeUnitの場合、入力が発行されると`busy`が高くなり、出力が発行されると低くなります。さらに、入力中のuopまたは計算中のuopがリダイレクトフラッシュされる必要がある場合も、`busy`は低くなります。

さらに、ExeUnitは混合レイテンシタイプをチェックします。つまり、同じポートに異なるレイテンシタイプ（決定的および非決定的）の機能ユニットが存在するかどうかをチェックします。このような混合ケースが存在する場合、非決定論的レイテンシを持つ機能ユニットについては、その優先度が最大であることが保証されます。この設計ロジックにより、異なるレイテンシタイプの機能ユニットを処理する際に、書き込みポートの優先度が適切に設定され、優先度の競合や不整合が回避されます。

各ExuUnitには、さまざまなFUに加えて、in1ToNというサブモジュールも含まれています。これはディスパッチャとして機能し、ExeUnitに入るExuInputをさらに異なるFUにディスパッチする役割を果たします。同じExuInputが正確に1つのFUに入り、複数のFUに入らないようにする必要があります。

さらに、inPipeと呼ばれるレジスタのセットがあります。これは、サイズがlatencyMax + 1の（valid、input）ペアで構成されています。これらは、入力と、入力が存在する計算サイクルを記録します。パイプライン制御が必要なFUの場合、inPipeを介して元のデータを取得できます。

最後に、異なるFUからの出力結果を集約し、1つのFUの出力結果をExeUnitの出力として選択する必要があります。

![ExuUnit 概要](./figure/ExuUnit-Overview.svg)

## 設計仕様

バックエンドには、intExuBlock、fpExuBlock、vfExuBlockの合計3つのExuBlockがあり、それぞれ整数、浮動小数点、ベクトルの実行モジュールです。各ExuBlockには、いくつかのExeUnitユニットが含まれています。

intExuBlockには8つのExeUnitが含まれており、それぞれ次の機能を持ちます。

表: intExuBlock内の各ExeUnitに含まれるFU

| ExeUnit | 機能 |
| --- | --- |
| exus0 | alu、mul、bku |
| exus1 | brh、jmp |
| exus2 | alu、mul、bku |
| exus3 | brh、jmp |
| exus4 | alu |
| exus5 | brh、jmp、i2f、i2v、VSetRiWi、VSetRiWvf |
| exus6 | alu |
| exus7 | csr、fence、div |

fpExuBlockには5つのExeUnitが含まれており、各ExeUnitは次の機能に対応しています。

表: fpExuBlockの各ExeUnitに含まれるFU

| ExeUnit | 機能 |
| --- | --- |
| exus0 | falu、fcvt、f2v、fmac |
| exus1 | fdiv |
