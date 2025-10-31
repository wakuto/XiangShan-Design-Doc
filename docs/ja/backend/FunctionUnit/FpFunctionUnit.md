# FpFunctionUnit

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット：[xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

浮動小数点演算機能ユニットには、falu、fmac、fcvt、fDivSqrtが含まれます。各機能ユニットがサポートする命令は次の表に示されています。

## falu

表: FALUがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| falu | FMINM.H | Zfa | スカラー |
| falu | FMINM.S | Zfa | スカラー |
| falu | FMINM.D | Zfa | スカラー |
| falu | FMAXM.H | Zfa | スカラー |
| falu | FMAXM.S | Zfa | スカラー |
| falu | FMAXM.D | Zfa | スカラー |
| falu | FLEQ.H | Zfa | スカラー |
| falu | FLEQ.S | Zfa | スカラー |
| falu | FLEQ.D | Zfa | スカラー |
| falu | FLTQ.H | Zfa | スカラー |
| falu | FLTQ.S | Zfa | スカラー |
| falu | FLTQ.D | Zfa | スカラー |
| falu | FADD.H | Zfh | スカラー |
| falu | FADD.S | F | スカラー |
| falu | FADD.D | D | スカラー |
| falu | FSUB.H | Zfh | スカラー |
| falu | FSUB.S | F | スカラー |
| falu | FSUB.D | D | スカラー |
| falu | FEQ.H | Zfh | スカラー |
| falu | FEQ.S | F | スカラー |
| falu | FEQ.D | D | スカラー |
| falu | FLT.H | Zfh | スカラー |
| falu | FLT.S | F | スカラー |
| falu | FLT.D | D | スカラー |
| falu | FLE.H | Zfh | スカラー |
| falu | FLE.S | F | スカラー |
| falu | FLE.D | D | スカラー |
| falu | FMIN.H | Zfh | スカラー |
| falu | FMIN.S | F | スカラー |
| falu | FMIN.D | D | スカラー |
| falu | FCLASS.H | Zfh | スカラー |
| falu | FCLASS.S | F | スカラー |
| falu | FCLASS.D | D | スカラー |
| falu | FSGNJ.H | Zfh | スカラー |
| falu | FSGNJ.S | F | スカラー |
| falu | FSGNJ.D | D | スカラー |
| falu | FSGNJX.H | Zfh | スカラー |
| falu | FSGNJX.S | F | スカラー |
| falu | FSGNJX.D | D | スカラー |
| falu | FSGNJN.H | Zfh | スカラー |
| falu | FSGNJN.S | F | スカラー |
| falu | FSGNJN.D | D | スカラー |

## fmac

表: fmacがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| fmac | FMUL.H | Zfh | スカラー |
| fmac | FMUL.S | F | スカラー |
| fmac | FMUL.D | D | スカラー |
| fmac | FMADD.H | Zfh | スカラー |
| fmac | FMADD.S | F | スカラー |
| fmac | FMADD.D | D | スカラー |
| fmac | FMSUB.H | Zfh | スカラー |
| fmac | FMSUB.S | F | スカラー |
| fmac | FMSUB.D | D | スカラー |
| fmac | FNMADD.H | Zfh | スカラー |
| fmac | FNMADD.S | F | スカラー |
| fmac | FNMADD.D | D | スカラー |
| fmac | FNMSUB.H | Zfh | スカラー |
| fmac | FNMSUB.S | F | スカラー |
| fmac | FNMSUB.D | D | スカラー |

## fcvt

表: fcvtがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| fcvt | FROUND.H | zfa | スカラー |
| fcvt | FROUND.S | zfa | スカラー |
| fcvt | FROUND.D | zfa | スカラー |
| fcvt | FROUNDX.H | zfa | スカラー |
| fcvt | FROUNDX.S | zfa | スカラー |
| fcvt | FROUNDX.D | zfa | スカラー |
| fcvt | FCVTMOD.W.D | zfa | スカラー |
| fcvt | FCVT.W.S | F | スカラー |
| fcvt | FCVT.WU.S | F | スカラー |
| fcvt | FCVT.L.S | F | スカラー |
| fcvt | FCVT.LU.S | F | スカラー |
| fcvt | FCVT.D.S | D | スカラー |
| fcvt | FCVT.W.D | D | スカラー |
| fcvt | FCVT.WU.D | D | スカラー |
| fcvt | FCVT.L.D | D | スカラー |
| fcvt | FCVT.LU.D | D | スカラー |
| fcvt | FCVT.S.D | D | スカラー |
| fcvt | FCVT.D.S | D | スカラー |
| fcvt | FCVT.H.S | Zfh | スカラー |
| fcvt | FCVT.S.H | Zfh | スカラー |
| fcvt | FCVT.H.D | Zfh | スカラー |
| fcvt | FCVT.D.H | Zfh | スカラー |
| fcvt | FCVT.W.H | Zfh | スカラー |
| fcvt | FCVT.WU.H | Zfh | スカラー |
| fcvt | FCVT.L.H | Zfh | スカラー |
| fcvt | FCVT.LU.H | Zfh | スカラー |
| fcvt | FMV.X.D | D | スカラー |
| fcvt | FMV.X.W | F | スカラー |
| fcvt | FMV.X.H | Zfh | スカラー |

## fDivSqrt

表: fDivSqrtがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| fDivSqrt | FDIV.H | Zfh | スカラー |
| fDivSqrt | FDIV.S | F | スカラー |
| fDivSqrt | FDIV.D | D | スカラー |
| fDivSqrt | FSQRT.H | Zfh | スカラー |
| fDivSqrt | FSQRT.S | F | スカラー |
| fDivSqrt | FSQRT.D | D | スカラー |
