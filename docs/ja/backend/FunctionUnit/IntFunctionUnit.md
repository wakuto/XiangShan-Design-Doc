# IntFunctionUnit

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット：[xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

整数機能ユニットには、jmp、brh、i2f、i2v、f2v、csr、alu、mul、div、fence、bkuが含まれます。各機能ユニットがサポートする命令は次の表に示されています。

## jmp

表: jmp fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| jmp | AUIPC | I | スカラー |
| jmp | JAL | I | スカラー |
| jmp | JALR | I | スカラー |

## brh

表: BRH FUがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| brh | BEQ | I | スカラー |
| brh | BNE | I | スカラー |
| brh | BGE | I | スカラー |
| brh | BGEU | I | スカラー |
| brh | BLT | I | スカラー |
| brh | BLTU | I | スカラー |

## i2f

表: i2f fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| i2f | FCVT.S.W | F | スカラー |
| i2f | FCVT.S.WU | F | スカラー |
| i2f | FCVT.S.L | F | スカラー |
| i2f | FCVT.S.LU | F | スカラー |
| i2f | FCVT.D.W | D | スカラー |
| i2f | FCVT.D.WU | D | スカラー |
| i2f | FCVT.D.L | D | スカラー |
| i2f | FCVT.D.LU | D | スカラー |
| i2f | FCVT.H.W | Zfh | スカラー |
| i2f | FCVT.H.WU | Zfh | スカラー |
| i2f | FCVT.H.L | Zfh | スカラー |
| i2f | FCVT.H.LU | Zfh | スカラー |

## i2v

表: i2v fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| i2v | FMV.D.X | D | スカラー |
| i2v | FMV.W.X | F | スカラー |
| i2v | FMV.H.X | Zfh | スカラー |

さらに、ベクトル命令から分割されたuopとして（具体的な分割方法についてはdecodeを参照）、サポートされるUopSplitTypeにはVSET、VEC_0XV、VEC_VXV、VEC_VXW、VEC_WXW、VEC_WXV、VEC_VXM、VEC_SLIDE1UP、VEC_SLIDE1DOWN、VEC_SLIDEUP、VEC_SLIDEDOWN、VEC_RGATHER_VX、VEC_US_LDST、VEC_US_FF_LD、VEC_S_LDST、VEC_I_LDSTが含まれます。サポート内容：

* 整数からベクトルへのmove

## f2v

表: f2v fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| f2v | FLI.H | I | zfa |
| f2v | FLI.S | I | zfa |
| f2v | FLI.D | I | zfa |

さらに、ベクトル命令から分割されたuopとして（具体的な分割方法についてはdecodeを参照）、サポートされるUopSplitTypeはVEC_VFV、VEC_0XV、VEC_VFW、VEC_WFW、VEC_VFM、VEC_FSLIDE1UP、VEC_FSLIDE1DOWNです。サポート内容：

* 浮動小数点からベクトルへのmove

## csr

表: csr fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| csr | csrrw | I | スカラー |
| csr | csrrs | I | スカラー |
| csr | csrrc | I | スカラー |
| csr | csrrwi | I | スカラー |
| csr | csrrsi | I | スカラー |
| csr | csrrci | I | スカラー |
| csr | ebreak | I | スカラー |
| csr | ecall | I | スカラー |
| csr | sret | I | スカラー |
| csr | mret | I | スカラー |
| csr | mnret | smdt | スカラー |
| csr | dret | debug | スカラー |
| csr | wfi | | スカラー |
| csr | wrs.nto | zawrs | スカラー |
| csr | wrs.sto | zawrs | スカラー |

## ALU

表: ALU FUがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| ALU | LUI | I | スカラー |
| ALU | ADDI | I | スカラー |
| ALU | ANDI | I | スカラー |
| ALU | ORI | I | スカラー |
| ALU | XORI | I | スカラー |
| ALU | SLTI | I | スカラー |
| ALU | SLTIU | I | スカラー |
| ALU | SLL | I | スカラー |
| ALU | SUB | I | スカラー |
| ALU | SLT | I | スカラー |
| ALU | SLTU | I | スカラー |
| ALU | AND | I | スカラー |
| ALU | OR | I | スカラー |
| ALU | XOR | I | スカラー |
| ALU | SRA | I | スカラー |
| ALU | SRL | I | スカラー |
| ALU | SLLI | I | スカラー |
| ALU | SRLI | I | スカラー |
| ALU | SRAI | I | スカラー |
| ALU | ADDIW | I | スカラー |
| ALU | SLLIW | I | スカラー |
| ALU | SRAIW | I | スカラー |
| ALU | SRLIW | I | スカラー |
| ALU | ADDW | I | スカラー |
| ALU | SUBW | I | スカラー |
| ALU | SLLW | I | スカラー |
| ALU | SRAW | I | スカラー |
| ALU | SRLW | I | スカラー |
| ALU | ADD.UW | Zba | スカラー |
| ALU | SH1ADD | Zba | スカラー |
| ALU | SH1ADD.UW | Zba | スカラー |
| ALU | SH2ADD | Zba | スカラー |
| ALU | SH2ADD.UW | Zba | スカラー |
| ALU | SH3ADD | Zba | スカラー |
| ALU | SH3ADD.UW | Zba | スカラー |
| ALU | SLLI.UW | Zba | スカラー |
| ALU | ANDN | Zbb | スカラー |
| ALU | ORN | Zbb | スカラー |
| ALU | XORN | Zbb | スカラー |
| ALU | MAX | Zbb | スカラー |
| ALU | MAXU | Zbb | スカラー |
| ALU | MIN | Zbb | スカラー |
| ALU | MINU | Zbb | スカラー |
| ALU | SEXT.B | Zbb | スカラー |
| ALU | SEXT.H | Zbb | スカラー |
| ALU | ROL | Zbb | スカラー |
| ALU | ROLW | Zbb | スカラー |
| ALU | ROR | Zbb | スカラー |
| ALU | RORI | Zbb | スカラー |
| ALU | RORIW | Zbb | スカラー |
| ALU | RORW | Zbb | スカラー |
| ALU | ORC.B | Zbb | スカラー |
| ALU | REV8 | Zbb | スカラー |
| ALU | BCLR | Zbs | スカラー |
| ALU | BCLRI | Zbs | スカラー |
| ALU | BEXT | Zbs | スカラー |
| ALU | BEXTI | Zbs | スカラー |
| ALU | BINV | Zbs | スカラー |
| ALU | BINVI | Zbs | スカラー |
| ALU | BSET | Zbs | スカラー |
| ALU | BSETI | Zbs | スカラー |
| ALU | PACk | Zbkb | スカラー |
| ALU | PACKH | Zbkb | スカラー |
| ALU | PACKW | Zbkb | スカラー |
| ALU | BREV8 | Zbkb | スカラー |
| ALU | CZERO.EQZ | Zicond | スカラー |
| ALU | CZERO.NEZ | Zicond | スカラー |
| ALU | MOP.R | Zimop | スカラー |
| ALU | MOP.RR | Zimop | スカラー |
| ALU | TRAP | I | スカラー |

## mul

表: mul fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| mul | MUL | M | スカラー |
| mul | MULH | M | スカラー |
| mul | MULHU | M | スカラー |
| mul | MULHSU | M | スカラー |
| mul | MULW | M | スカラー |

## div

表: div fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| div | DIV | M | スカラー |
| div | DIVU | M | スカラー |
| div | REM | M | スカラー |
| div | REMU | M | スカラー |
| div | DIVW | M | スカラー |
| div | DIVUW | M | スカラー |
| div | REMW | M | スカラー |
| div | REMUW | M | スカラー |

## fence

表: fence fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| fence | SFENCE.VMA | | スカラー |
| fence | SFENCE.I | | スカラー |
| fence | FENCE | | スカラー |
| fence | PAUSE | | スカラー |
| fence | SINVAL.VMA | Svinval | スカラー |
| fence | SFENCE.W.INVAL | Svinval | スカラー |
| fence | SFENCE.INVAL.IR | Svinval | スカラー |
| fence | HFENCE.GVMA | | スカラー |
| fence | HFENCE.VVMA | | スカラー |
| fence | HINVAL.GVMA | | スカラー |
| fence | HINVAL.VVMA | | スカラー |

## bku

表: bku fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| bku | CLZ | Zbb | スカラー |
| bku | CLZW | Zbb | スカラー |
| bku | CTZ | Zbb | スカラー |
| bku | CTZW | Zbb | スカラー |
| bku | CPOP | Zbb | スカラー |
| bku | CPOPW | Zbb | スカラー |
| bku | CLMUL | Zbc | スカラー |
| bku | CLMULH | Zbc | スカラー |
| bku | CLMULH | Zbc | スカラー |
| bku | XPERM4 | Zbkx | スカラー |
| bku | XPERM8 | Zbkx | スカラー |
| bku | AES64DS | Zknd | スカラー |
| bku | AES64DSM | Zknd | スカラー |
| bku | AES64IM | Zknd | スカラー |
| bku | AES64KS1I | Zknd | スカラー |
| bku | AES64KS2 | Zknd | スカラー |
| bku | AES64ES | Zkne | スカラー |
| bku | AES64ESM | Zkne | スカラー |
| bku | SHA256SIG0 | Zknh | スカラー |
| bku | SHA256SIG1 | Zknh | スカラー |
| bku | SHA256SUM0 | Zknh | スカラー |
| bku | SHA256SUM1 | Zknh | スカラー |
| bku | SHA512SIG0 | Zknh | スカラー |
| bku | SHA512SIG1 | Zknh | スカラー |
| bku | SHA512SUM0 | Zknh | スカラー |
| bku | SHA512SUM1 | Zknh | スカラー |
| bku | SM4ED0 | Zksed | スカラー |
| bku | SM4ED1 | Zksed | スカラー |
| bku | SM4ED2 | Zksed | スカラー |
| bku | SM4ED3 | Zksed | スカラー |
| bku | SM4KS0 | Zksed | スカラー |
| bku | SM4KS1 | Zksed | スカラー |
| bku | SM4KS2 | Zksed | スカラー |
