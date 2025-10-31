# ExuBlock

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット：[xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 入出力

`flush` は、valid信号を持つリダイレクト入力です。

`in` は、issueBlockと、各issueBlock内に含まれるexuに対応するExuInput入力です。つまり、in(i)(j)は、i番目のissueBlock内のj番目のexuからの入力を表します。

`out` は、issueBlockと、各issueBlock内に含まれるexuに対応するExuOutput出力です。つまり、out(i)(j)は、i番目のissueBlock内のj番目のexuに対応する出力を表します。

`csrio`、`csrin`、および`csrToDecode`は、ExuBlock内に`CSR`が存在する場合にのみ存在します。

同様に、`fenceio`は、ExuBlock内に`fence`が存在する場合にのみ存在します。`frm`は、ExuBlockが`frm`をソースとして必要とする場合にのみ存在します。`vxrm`は、ExuBlockが`vxrm`をソースとして必要とする場合にのみ存在します。

`vtype`、`vlIsZero`、および`vlIsVlmax`は、ExuBlockがVconfigへの書き込みを必要とする場合にのみ存在します。

## 機能

ExuBlockは、主に外部モジュールからの信号を設定要件に従って各exuに接続し、exuの出力をExuBlockの出力として整理する役割を担います。

![ExuBlock 概要](./figure/ExuBlock-Overview.svg)

## 設計仕様

バックエンドには、intExuBlock、fpExuBlock、vfExuBlockの合計3つのExuBlockがあり、それぞれ整数、浮動小数点、ベクトルの実行モジュールです。各ExuBlockには、いくつかのExeUnitユニットが含まれています。

intExuBlockには8つのExeUnitが含まれています。そのI/Oには、flush、in、out、csrio、csrin、csrToDecode、fenceio、frm、vtype、vlIsZero、vlIsVlmaxが含まれますが、vxrmは含まれません。

fpExuBlockには5つのExeUnitが含まれています。そのI/Oには、flush、in、out、frmが含まれますが、csrio、csrin、csrToDecode、fenceio、vxrm、vtype、vlIsZero、vlIsVlmaxは含まれません。

vfExuBlockには5つのExeUnitが含まれています。そのI/Oには、flush、in、out、frm、vxrm、vtype、vlIsZero、vlIsVlmaxが含まれますが、csrio、csrin、csrToDecode、fenceioは含まれません。
