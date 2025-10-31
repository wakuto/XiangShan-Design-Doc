# デバッグモジュール

- バージョン: V2R2
- ステータス: OK
- 日付: 2025/01/20
- コミット：[xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 用語集

表: 用語解説

| 略語 | 正式名称 | 説明 |
| --- | --- | --- |
| DM | Debug Module | デバッグモジュール |
| DTM | Debug Transport Module | デバッグ転送モジュール |
| DMI | Debug Module Interface | デバッグモジュールインターフェース |

## パラメータ設計

表: パラメータ設計

| パラメータ | デフォルト値 | 説明 |
| --- | --- | --- |
| baseAddress | 0x38020800 | デバッグモジュールのMMIOベースアドレス |
| nDMIAddrSize | 7 | DMIアドレス幅 |
| nProgramBufferWords | 16 | プログラムバッファのワード数 |
| nAbstractDataWords | 4 | 抽象コマンドのワード数 |
| hasBusMaster | true | システムバスマスターを持つか |
| maxSupportedSBAccess | 64 | システムバスの最大メモリアクセス幅 |
| supportQuickAccess | false | QuickAccessをサポートするか |
| supportHartArray | true | ハートアレイをサポートするか |
| nHaltGroups | 1 | ハルトグループの数 |
| nExtTriggers | 0 | 外部トリガーの数 |
| hasHartResets | true | 選択したハートをリセットするか |
| hasImplicitEbreak | false | 暗黙のebreakをサポートするか |

## 全体設計

### 全体ブロック図

[@fig:DM]に示すように:

![デバッグモジュールの概要](./figure/DM-Overview.svg){#fig:DM}

### 複数クロックドメイン

[@fig:multiclock]に示すように:

![デバッグモジュールの複数クロックドメイン](./figure/MultiClock.svg){#fig:multiclock}

### デバッグMMIO

[@tbl:debug-mmio]に示すように:

表: デバッグMMIOアドレス空間 {#tbl:debug-mmio}

| アドレス (ベースアドレス 0x3802_0000) | 名称 | 説明 | このアドレスに格納される内容 |
| --- | --- | --- | --- |
| 0x800 | debugEntry | デバッグエントリアドレス / デバッグROMのベースアドレス | |
| 0x808 | debugException | dmodeでの実行中に例外が発生した場合の例外エントリアドレス | |
| 0x100 | HALTED | | dmodeに入ったハートに対応するhartidがデバッグモジュールによって取得される |
| 0x104 | GOING | | whereto、最終的にABSTRACTにジャンプして実行 |
| 0x108 | RESUMING | | dretを実行 |
| 0x10c | EXCEPTION | | |
| 0x300 | WHERETO | このアドレスに格納される命令 | dmが生成したABSTRACTへのジャンプ命令 |
| 0x380 | DATA | DATAのベースアドレス (ld/st用) | データ交換 |
| DATA-4*nProgBuf | PROGBUF | progbuf0のアドレス | dmが生成した命令 (goの前に準備) |
| DATA-4 | IMPEBREAK | 暗黙のebreak命令 | |
| PROGBUF - 4* nAbstractInst | ABSTRACT | AbstractInstructions | dmが生成した命令 (goの前に準備) |
| 0x400 | FLAGS | hartidフラグに対応するベースアドレス。各フラグは8ビットで、0x400はhartid=0の時のフラグアドレスを表す | この8ビット値の下位2ビットのみが有効。下から2番目のビットはresumeを、最下位ビットはgoを指す。アドレス空間は1k、つまり0x400->(0x500-0x1) |

## モジュール設計

### デバッグモジュール

現在、昆明湖のデバッグ機能の実装状況は以下の通りです:

* 最初の命令からのデバッグをサポートし、CPUリセット後にデバッグモードに入ります。
* シングルコアおよびマルチコア（選択されたコア）のデバッグにおける実行制御（停止、再開、リセット）をサポートします。
* シングルステップデバッグをサポートします。
* stopcountとstoptimeをサポートします。
* ソフトウェアブレークポイント（ebreak命令）、ハードウェアブレークポイント（トリガー）、およびメモリブレークポイント（トリガー）をサポートします。
* GPR、CSR、およびメモリアクセスをサポートし、progbufとsysbusの両方のアクセス方法を提供します。
* デバッグ割り込み（haltreq、haltgroup、halt-on-reset）、トリガー発火、ebreak、singlestep、クリティカルエラーなどを介してデバッグモードに入ることをサポートします。

### トリガーモジュール

現在、昆明湖のトリガーモジュールの実装状況は以下の通りです:

* 昆明湖のトリガーモジュールで現在実装されているデバッグ関連のCSRは下表の通りです。
* トリガーのデフォルト設定数は4です（ユーザーによるカスタマイズをサポート）。
* mcontrol6タイプの命令およびメモリアクセストリガーをサポートします。
