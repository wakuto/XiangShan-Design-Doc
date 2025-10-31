# CtrlUnitサブモジュール ドキュメント

現在、CtrlUnitは主にECCチェック有効化/エラー注入機能を処理します。

## mmioマップCSR

CtrlUnitは、tilelinkバスに接続された一連のmmioマップCSRを実装しており、アドレスはパラメータ`cacheCtrlAddressOpt`で設定可能で、デフォルトは`0x38022080`です。合計サイズは128Bです。

パラメータ`cacheCtrlAddressOpt`が`None`の場合、CtrlUnitは**インスタンス化されません**。この場合、ECCチェック有効化は**デフォルトで有効**になり、ソフトウェアはそれを無効にできません。ソフトウェアはエラー注入を制御できません。

現在実装されているCSRは次のとおりです。

```plain
              64     10        7         4         2        1        0
0x00 eccctrl   | WARL | ierror | istatus | itarget | inject | enable |

              64 PAddrBits-1               0
0x08 ecciaddr  | WARL |       paddr        |
```

| CSR      | フィールド   | 説明                                                                                     |
| -------- | ------- | ---------------------------------------------------------------------------------------- |
| eccctrl  | enable  | ECCエラーチェック有効化、元は`sfetchctl(0)`                                        |
| eccctrl  | inject  | ECCエラー注入有効化、1を書き込むと注入開始、読み取りは常に0                   |
| eccctrl  | itarget | ECCエラー注入ターゲット、以下の表を参照                                              |
| eccctrl  | istatus | ECCエラー注入ステータス（読み取り専用）、以下の表を参照                                  |
| eccctrl  | ierror  | ECCエラー理由（読み取り専用）、`eccctrl.istatus===error`の場合のみ有効、以下の表を参照 |
| ecciaddr | paddr   | ECCエラー注入物理アドレス                                                     |

`eccctrl.itarget`:

| 値 | ターゲット    |
| ----- | --------- |
| 0     | metaArray |
| 2     | dataArray |
| 1/3   | rsvd      |

`eccctrl.istatus`:

| 値 | ステータス   |
| ----- | -------- |
| 0     | Idle     |
| 1     | working  |
| 2     | injected |
| 7     | error    |
| 3-6   | rsvd     |

`eccctrl.ierror`:

| 値 | エラー                                                                         |
| ----- | ----------------------------------------------------------------------------- |
| 0     | ECCが有効でない（つまり`!eccctrl.enable`）                                     |
| 1     | 注入ターゲットSRAMが無効（つまり`eccctrl.itarget==rsvd`）                     |
| 2     | 注入対象アドレス（つまり`ecciaddr.paddr`）がICacheにない |
| 3-7   | rsvd                                                                          |

## エラーチェック有効化

CtrlUnitの`eccctrl.enable`ビットはMainPipeに直接接続されており、ECCチェックの有効化を制御します。このビットが0の場合、ICacheはECCチェックを実行しません。ただし、リフィル中にチェックコードを計算して保存するため、わずかな追加の電力消費が発生する可能性があります。計算しない場合、無効から有効に切り替えるときにICacheをフラッシュする必要があります（そうしないと、読み取りパリティコードが正しくない可能性があります）。

## エラー注入有効化

CtrlUnitは内部でステートマシンを使用してエラー注入プロセスを制御し、そのステータス（注意：`eccctrl.istatus`とは異なります）は次のとおりです。

- idle: 注入コントローラアイドル
- readMetaReq: metaArrayに読み取り要求を送信
- readMetaResp: metaArrayの読み取り応答を受信
- writeMeta: metaArrayに書き込み
- writeData: dataArrayに書き込み

ソフトウェアが`eccctrl.inject`に1を書き込むと、以下の簡単なチェックが実行されます。合格した場合、ステートマシンは`readMetaReq`状態に遷移します。

- `eccctrl.enable`が0の場合、エラー`eccctrl.ierror=0`を報告
- `eccctrl.itarget`がrsvd(1/3)の場合、エラー`eccctrl.ierror=1`を報告

`readMetaReq`状態では、CtrlUnitはアドレス`ecciaddr.paddr`に対応するセットのMetaArrayに読み取り要求を送信し、ハンドシェイクを待ちます。ハンドシェイク後、`readMetaResp`状態に遷移します。

`readMetaResp`状態では、CtrlUnitはMetaArrayからの応答を受信し、`ecciaddr.paddr`アドレスに対応するptagがヒットするかどうかをチェックします。ヒットしない場合、エラー`eccctrl.ierror=2`を報告します。それ以外の場合、`eccctrl.itarget`に基づいて、`writeMeta`または`writeData`状態に遷移します。

`writeMeta`または`writeData`状態では、CtrlUnitは`poison`ビットをアサートしながら、MetaArray/DataArrayに任意のデータを書き込みます。書き込み後、ステートマシンは`idle`状態に遷移します。

ICacheのトップレベルはMuxを実装しています。CtrlUnitのステートマシンが`idle`でない場合、MetaArray/DataArrayの読み取り/書き込みポートをMainPipe/IPrefetchPipe/MissUnitではなくCtrlUnitに接続します。ステートマシンが`idle`の場合、その逆が行われます。
