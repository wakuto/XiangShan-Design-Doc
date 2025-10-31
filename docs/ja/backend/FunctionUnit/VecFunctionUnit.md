# VecFunctionUnit

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット：[xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

ベクトル機能ユニットには、vsetiwi、vsetiwf、vsetfwf、vipu、vialuF、vfpu、vldu、vstu、vppu、vimac、vidiv、vfalu、vfma、vfdiv、vfcvtが含まれます。各機能ユニットがサポートする命令は次の表に示されています。

## vsetiwi vsetiwf vsetfwf

vsetiwi、vsetiwf、vsetfwfの3つの機能ユニットは、vset命令（VSETVLI、VSETIVLI、VSETVL）のuop分割をサポートするために使用されます。具体的な分割方法については、decodeを参照してください。

## vipu

表: vipu fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| vipu | vwredsumu.vs | V | ベクトル |
| vipu | vwredsum.vs | V | ベクトル |
| vipu | vcpop.m | V | ベクトル |
| vipu | vfirst.m | V | ベクトル |
| vipu | vid.v | V | ベクトル |
| vipu | viota.m | V | ベクトル |
| vipu | vmsbf.vv | V | ベクトル |
| vipu | vmsif.vv | V | ベクトル |
| vipu | vmsof.vv | V | ベクトル |
| vipu | vmv.x.s | V | ベクトル |
| vipu | vredand.vs | V | ベクトル |
| vipu | vredmax.vs | V | ベクトル |
| vipu | vredmaxu.vs | V | ベクトル |
| vipu | vredmin.vs | V | ベクトル |
| vipu | vredminu.vs | V | ベクトル |
| vipu | vredor.vs | V | ベクトル |
| vipu | vredsum.vs | V | ベクトル |
| vipu | vredxor.vs | V | ベクトル |

## vialuF

表: vialuF FUがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| vialuF | vadd.vv | V | ベクトル |
| vialuF | vsub.vv | V | ベクトル |
| vialuF | vminu.vv | V | ベクトル |
| vialuF | vmin.vv | V | ベクトル |
| vialuF | vmaxu.vv | V | ベクトル |
| vialuF | vmax.vv | V | ベクトル |
| vialuF | vand.vv | V | ベクトル |
| vialuF | vor.vv | V | ベクトル |
| vialuF | vxor.vv | V | ベクトル |
| vialuF | vadc.vvm | V | ベクトル |
| vialuF | vmadc.vvm | V | ベクトル |
| vialuF | vmadc.vv | V | ベクトル |
| vialuF | vsbc.vvm | V | ベクトル |
| vialuF | vmsbc.vv | V | ベクトル |
| vialuF | vmsbc.vvm | V | ベクトル |
| vialuF | vmerge.vvm | V | ベクトル |
| vialuF | vmv.v.v | V | ベクトル |
| vialuF | vmseq.vv | V | ベクトル |
| vialuF | vmsne.vv | V | ベクトル |
| vialuF | vmsltu.vv | V | ベクトル |
| vialuF | vmslt.vv | V | ベクトル |
| vialuF | vmsleu.vv | V | ベクトル |
| vialuF | vmsle.vv | V | ベクトル |
| vialuF | vsll.vv | V | ベクトル |
| vialuF | vsrl.vv | V | ベクトル |
| vialuF | vsra.vv | V | ベクトル |
| vialuF | vnsrl.wv | V | ベクトル |
| vialuF | vnsra.wv | V | ベクトル |
| vialuF | vsaddu.vv | V | ベクトル |
| vialuF | vsadd.vv | V | ベクトル |
| vialuF | vssubu.vv | V | ベクトル |
| vialuF | vssub.vv | V | ベクトル |
| vialuF | vssrl.vv | V | ベクトル |
| vialuF | vssra.vv | V | ベクトル |
| vialuF | vnclipu.wv | V | ベクトル |
| vialuF | vnclip.wv | V | ベクトル |
| vialuF | vwredsumu.vs | V | ベクトル |
| vialuF | vwredsum.vs | V | ベクトル |
| vialuF | vandn.vv | V | ベクトル |
| vialuF | vrol.vv | V | ベクトル |
| vialuF | vror.vv | V | ベクトル |
| vialuF | vwsll.vv | V | ベクトル |
| vialuF | vadd.vx | V | ベクトル |
| vialuF | vsub.vx | V | ベクトル |
| vialuF | vrsub.vx | V | ベクトル |
| vialuF | vminu.vx | V | ベクトル |
| vialuF | vmin.vx | V | ベクトル |
| vialuF | vmaxu.vx | V | ベクトル |
| vialuF | vmax.vx | V | ベクトル |
| vialuF | vand.vx | V | ベクトル |
| vialuF | vor.vx | V | ベクトル |
| vialuF | vxor.vx | V | ベクトル |
| vialuF | vadc.vxm | V | ベクトル |
| vialuF | vmadc.vxm | V | ベクトル |
| vialuF | vmadc.vx | V | ベクトル |
| vialuF | vsbc.vxm | V | ベクトル |
| vialuF | vmsbc.vx | V | ベクトル |
| vialuF | vmsbc.vxm | V | ベクトル |
| vialuF | vmerge.vxm | V | ベクトル |
| vialuF | vmv.v.x | V | ベクトル |
| vialuF | vmseq.vx | V | ベクトル |
| vialuF | vmsne.vx | V | ベクトル |
| vialuF | vmsltu.vx | V | ベクトル |
| vialuF | vmslt.vx | V | ベクトル |
| vialuF | vmsleu.vx | V | ベクトル |
| vialuF | vmsle.vx | V | ベクトル |
| vialuF | vmsgtu.vx | V | ベクトル |
| vialuF | vmsgt.vx | V | ベクトル |
| vialuF | vsll.vx | V | ベクトル |
| vialuF | vsrl.vx | V | ベクトル |
| vialuF | vsra.vx | V | ベクトル |
| vialuF | vnsrl.wx | V | ベクトル |
| vialuF | vnsra.wx | V | ベクトル |
| vialuF | vsaddu.vx | V | ベクトル |
| vialuF | vsadd.vx | V | ベクトル |
| vialuF | vssubu.vx | V | ベクトル |
| vialuF | vssub.vx | V | ベクトル |
| vialuF | vssrl.vx | V | ベクトル |
| vialuF | vssra.vx | V | ベクトル |
| vialuF | vnclipu.wx | V | ベクトル |
| vialuF | vnclip.wx | V | ベクトル |
| vialuF | vandn.vx | V | ベクトル |
| vialuF | vrol.vx | V | ベクトル |
| vialuF | vror.vx | V | ベクトル |
| vialuF | vwsll.vx | V | ベクトル |
| vialuF | vadd.vi | V | ベクトル |
| vialuF | vrsub.vi | V | ベクトル |
| vialuF | vand.vi | V | ベクトル |
| vialuF | vor.vi | V | ベクトル |
| vialuF | vxor.vi | V | ベクトル |
| vialuF | vadc.vim | V | ベクトル |
| vialuF | vmadc.vim | V | ベクトル |
| vialuF | vmadc.vi | V | ベクトル |
| vialuF | vmerge.vim | V | ベクトル |
| vialuF | vmv.v.i | V | ベクトル |
| vialuF | vmseq.vi | V | ベクトル |
| vialuF | vmsne.vi | V | ベクトル |
| vialuF | vmsleu.vi | V | ベクトル |
| vialuF | vmsle.vi | V | ベクトル |
| vialuF | vmsgtu.vi | V | ベクトル |
| vialuF | vmsgt.vi | V | ベクトル |
| vialuF | vsll.vi | V | ベクトル |
| vialuF | vsrl.vi | V | ベクトル |
| vialuF | vsra.vi | V | ベクトル |
| vialuF | vnsrl.wi | V | ベクトル |
| vialuF | vnsra.wi | V | ベクトル |
| vialuF | vsaddu.vi | V | ベクトル |
| vialuF | vsadd.vi | V | ベクトル |
| vialuF | vssrl.vi | V | ベクトル |
| vialuF | vssra.vi | V | ベクトル |
| vialuF | vnclipu.wi | V | ベクトル |
| vialuF | vnclip.wi | V | ベクトル |
| vialuF | vror.vi | V | ベクトル |
| vialuF | vwsll.vi | V | ベクトル |
| vialuF | vaadd.vv | V | ベクトル |
| vialuF | vaaddu.vv | V | ベクトル |
| vialuF | vasub.vv | V | ベクトル |
| vialuF | vasubu.vv | V | ベクトル |
| vialuF | vmand.mm | V | ベクトル |
| vialuF | vmandn.mm | V | ベクトル |
| vialuF | vmnand.mm | V | ベクトル |
| vialuF | vmnor.mm | V | ベクトル |
| vialuF | vmor.mm | V | ベクトル |
| vialuF | vmorn.mm | V | ベクトル |
| vialuF | vmxnor.mm | V | ベクトル |
| vialuF | vmxor.mm | V | ベクトル |
| vialuF | vsext.vf2 | V | ベクトル |
| vialuF | vsext.vf4 | V | ベクトル |
| vialuF | vsext.vf8 | V | ベクトル |
| vialuF | vzext.vf2 | V | ベクトル |
| vialuF | vzext.vf4 | V | ベクトル |
| vialuF | vzext.vf8 | V | ベクトル |
| vialuF | vwadd.vv | V | ベクトル |
| vialuF | vwadd.wv | V | ベクトル |
| vialuF | vwaddu.vv | V | ベクトル |
| vialuF | vwaddu.wv | V | ベクトル |
| vialuF | vwsub.vv | V | ベクトル |
| vialuF | vwsub.wv | V | ベクトル |
| vialuF | vwsubu.vv | V | ベクトル |
| vialuF | vwsubu.wv | V | ベクトル |
| vialuF | vbrev.v | V | ベクトル |
| vialuF | vbrev8.v | V | ベクトル |
| vialuF | vrev8.v | V | ベクトル |
| vialuF | vclz.v | V | ベクトル |
| vialuF | vctz.v | V | ベクトル |
| vialuF | vcpop.v | V | ベクトル |
| vialuF | vaadd.vx | V | ベクトル |
| vialuF | vaaddu.vx | V | ベクトル |
| vialuF | vasub.vx | V | ベクトル |
| vialuF | vasubu.vx | V | ベクトル |
| vialuF | vmv.s.x | V | ベクトル |
| vialuF | vwadd.vx | V | ベクトル |
| vialuF | vwadd.wx | V | ベクトル |
| vialuF | vwaddu.vx | V | ベクトル |
| vialuF | vwaddu.wx | V | ベクトル |
| vialuF | vwsub.vx | V | ベクトル |
| vialuF | vwsub.wx | V | ベクトル |
| vialuF | vwsubu.vx | V | ベクトル |
| vialuF | vwsubu.wx | V | ベクトル |

## vldu

## vstu

## vppu

表: vppu fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| vppu | vrgather.vv | V | ベクトル |
| vppu | vrgatherei16.vx | V | ベクトル |
| vppu | vrgather.vx | V | ベクトル |
| vppu | vslideup.vx | V | ベクトル |
| vppu | vslidedown.vx | V | ベクトル |
| vppu | vrgather.vi | V | ベクトル |
| vppu | vslideup.vi | V | ベクトル |
| vppu | vslidedown.vi | V | ベクトル |
| vppu | vmv1r.v | V | ベクトル |
| vppu | vmv2r.v | V | ベクトル |
| vppu | vmv4r.v | V | ベクトル |
| vppu | vmv8r.v | V | ベクトル |
| vppu | vcompress.vm | V | ベクトル |
| vppu | vslide1up.vx | V | ベクトル |
| vppu | vslide1down.vx | V | ベクトル |
| vppu | vfslide1up.vf | V | ベクトル |
| vppu | vfslide1down.vf | V | ベクトル |

## vimac

表: vimac fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| vimac | vsmul.vv | V | ベクトル |
| vimac | vsmul.vx | V | ベクトル |
| vimac | vmacc.vv | V | ベクトル |
| vimac | vmadd.vv | V | ベクトル |
| vimac | vmul.vv | V | ベクトル |
| vimac | vmulh.vv | V | ベクトル |
| vimac | vmulhsu.vv | V | ベクトル |
| vimac | vmulhu.vv | V | ベクトル |
| vimac | vnmsac.vv | V | ベクトル |
| vimac | vnmsub.vv | V | ベクトル |
| vimac | vwmacc.vv | V | ベクトル |
| vimac | vwmaccsu.vv | V | ベクトル |
| vimac | vwmaccu.vv | V | ベクトル |
| vimac | vwmul.vv | V | ベクトル |
| vimac | vwmulsu.vv | V | ベクトル |
| vimac | vwmulu.vv | V | ベクトル |
| vimac | vmacc.vx | V | ベクトル |
| vimac | vmadd.vx | V | ベクトル |
| vimac | vmul.vx | V | ベクトル |
| vimac | vmulh.vx | V | ベクトル |
| vimac | vmulhsu.vx | V | ベクトル |
| vimac | vmulhu.vx | V | ベクトル |
| vimac | vnmsac.vx | V | ベクトル |
| vimac | vnmsub.vx | V | ベクトル |
| vimac | vwmacc.vx | V | ベクトル |
| vimac | vwmaccsu.vx | V | ベクトル |
| vimac | vwmaccu.vx | V | ベクトル |
| vimac | vwmaccus.vx | V | ベクトル |
| vimac | vwmul.vx | V | ベクトル |
| vimac | vwmulsu.vx | V | ベクトル |
| vimac | vwmulu.wx | V | ベクトル |

## vidiv

表: VIDIV FUがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| vidiv | vdiv.vv | V | ベクトル |
| vidiv | vdivu.vv | V | ベクトル |
| vidiv | vrem.vv | V | ベクトル |
| vidiv | vremu.vv | V | ベクトル |
| vidiv | vdiv.vx | V | ベクトル |
| vidiv | vdivu.vx | V | ベクトル |
| vidiv | vrem.vx | V | ベクトル |
| vidiv | vremu.vx | V | ベクトル |

## vfalu

表: VFALU FUがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| vfalu | vfadd.vv | V | ベクトル |
| vfalu | vfsub.vv | V | ベクトル |
| vfalu | vfwadd.vv | V | ベクトル |
| vfalu | vfwsub.vv | V | ベクトル |
| vfalu | vfwadd.wv | V | ベクトル |
| vfalu | vfwsub.wv | V | ベクトル |
| vfalu | vfmin.vv | V | ベクトル |
| vfalu | vfmax.vv | V | ベクトル |
| vfalu | vfsgnj.vv | V | ベクトル |
| vfalu | vfsgnjn.vv | V | ベクトル |
| vfalu | vfsgnjx.vv | V | ベクトル |
| vfalu | vmfeq.vv | V | ベクトル |
| vfalu | vmfne.vv | V | ベクトル |
| vfalu | vmflt.vv | V | ベクトル |
| vfalu | vmfle.vv | V | ベクトル |
| vfalu | vfclass.v | V | ベクトル |
| vfalu | vfredosum.vs | V | ベクトル |
| vfalu | vfredusum.vs | V | ベクトル |
| vfalu | vfredmax.vs | V | ベクトル |
| vfalu | vfredmin.vs | V | ベクトル |
| vfalu | vfwredosum.vs | V | ベクトル |
| vfalu | vfwredusum.vs | V | ベクトル |
| vfalu | vfadd.vf | V | ベクトル |
| vfalu | vfsub.vf | V | ベクトル |
| vfalu | vfrsub.vf | V | ベクトル |
| vfalu | vfwadd.vf | V | ベクトル |
| vfalu | vfwsub.vf | V | ベクトル |
| vfalu | vfwadd.wf | V | ベクトル |
| vfalu | vfwsub.wf | V | ベクトル |
| vfalu | vfmin.vf | V | ベクトル |
| vfalu | vfmax.vf | V | ベクトル |
| vfalu | vfsgnj.vf | V | ベクトル |
| vfalu | vfsgnjn.vf | V | ベクトル |
| vfalu | vfsgnjx.vf | V | ベクトル |
| vfalu | vmfeq.vf | V | ベクトル |
| vfalu | vmfne.vf | V | ベクトル |
| vfalu | vmflt.vf | V | ベクトル |
| vfalu | vmfle.vf | V | ベクトル |
| vfalu | vmfgt.vf | V | ベクトル |
| vfalu | vmfge.vf | V | ベクトル |
| vfalu | vfmerge.vfm | V | ベクトル |
| vfalu | vfmv.v.f | V | ベクトル |
| vfalu | vfmv.f.s | V | ベクトル |
| vfalu | vfmv.s.f | V | ベクトル |

## vfma

表: vfma fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| vfma | vfmul.vv | V | ベクトル |
| vfma | vfwmul.vv | V | ベクトル |
| vfma | vfmacc.vv | V | ベクトル |
| vfma | vfnmacc.vv | V | ベクトル |
| vfma | vfmsac.vv | V | ベクトル |
| vfma | vfnmsac.vv | V | ベクトル |
| vfma | vfmadd.vv | V | ベクトル |
| vfma | vfnmadd.vv | V | ベクトル |
| vfma | vfmsub.vv | V | ベクトル |
| vfma | vfnmsub.vv | V | ベクトル |
| vfma | vfwmacc.vv | V | ベクトル |
| vfma | vfwnmacc.vv | V | ベクトル |
| vfma | vfwmsac.vv | V | ベクトル |
| vfma | vfwnmsac.vv | V | ベクトル |
| vfma | vfmul.vf | V | ベクトル |
| vfma | vfwmul.vf | V | ベクトル |
| vfma | vfmacc.vf | V | ベクトル |
| vfma | vfnmacc.vf | V | ベクトル |
| vfma | vfmsac.vf | V | ベクトル |
| vfma | vfnmsac.vf | V | ベクトル |
| vfma | vfmadd.vf | V | ベクトル |
| vfma | vfnmadd.vf | V | ベクトル |
| vfma | vfmsub.vf | V | ベクトル |
| vfma | vfnmsub.vf | V | ベクトル |
| vfma | vfwmacc.vf | V | ベクトル |
| vfma | vfwnmacc.vf | V | ベクトル |
| vfma | vfwmsac.vf | V | ベクトル |
| vfma | vfwnmsac.vf | V | ベクトル |

## vfdiv

表: vfdiv FUがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| vfdiv | vfdiv.vv | V | ベクトル |
| vfdiv | vfsqrt.v | V | ベクトル |
| vfdiv | vfdiv.vf | V | ベクトル |
| vfdiv | vfrdiv.vf | V | ベクトル |

## vfcvt

表: vfcvt fuがサポートする命令

| 機能ユニット | サポートする命令 | 拡張 | 説明 |
| --- | --- | --- | --- |
| vfcvt | vfrsqrt7.v | V | ベクトル |
| vfcvt | vfrec7.v | V | ベクトル |
| vfcvt | vfcvt.xu.f.v | V | ベクトル |
| vfcvt | vfcvt.x.f.v | V | ベクトル |
| vfcvt | vfcvt.rtz.xu.f.v | V | ベクトル |
| vfcvt | vfcvt.rtz.x.f.v | V | ベクトル |
| vfcvt | vfcvt.f.xu.v | V | ベクトル |
| vfcvt | vfwcvt.xu.f.v | V | ベクトル |
| vfcvt | vfwcvt.x.f.v | V | ベクトル |
| vfcvt | vfwcvt.rtz.xu.f.v | V | ベクトル |
| vfcvt | vfwcvt.rtz.x.f.v | V | ベクトル |
| vfcvt | vfwcvt.f.xu.v | V | ベクトル |
| vfcvt | vfwcvt.f.x.v | V | ベクトル |
| vfcvt | vfwcvt.f.f.v | V | ベクトル |
| vfcvt | vfncvt.xu.f.w | V | ベクトル |
| vfcvt | vfncvt.x.f.w | V | ベクトル |
| vfcvt | vfncvt.rtz.xu.f.w | V | ベクトル |
| vfcvt | vfncvt.rtz.x.f.w | V | ベクトル |
| vfcvt | vfncvt.f.xu.w | V | ベクトル |
| vfcvt | vfncvt.f.x.w | V | ベクトル |
| vfcvt | vfncvt.f.f.w | V | ベクトル |
| vfcvt | vfncvt.rod.f.f.w | V | ベクトル |
