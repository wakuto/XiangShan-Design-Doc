# XiangShan Decode 設計ドキュメント

- バージョン：V2R2
- ステータス：OK
- 日付：2025/02/28
- コミット：[xxx](https://github.com/OpenXiangShan/XiangShan/tree/xxx)

## 用語説明

表：用語説明

| 略語 | 正式名称 | 説明 |
| --- | --- | --- |
| - | Decode Unit | デコードユニット |
| uop | Micro Operation | マイクロオペレーション |
| - | numOfUop | 1つの命令から分割されたuopの数 |
| - | numOfWB | 1つの命令から分割されたuopのうち、書き戻しが必要な命令の数 |
| - | vtypeArch | 最新にコミットされたベクトル命令のvtype設定 |
| - | vtypeSpec | 現在のベクトル命令のvtype設定 |
| - | walkVType | リダイレクト発生時にロールバックして復元されるvtype |

## サブモジュールリスト

表：サブモジュールリスト

| サブモジュール | 説明 |
| --- | --- |
| DecodeUnit | デコードユニット |
| DecodeUnitComp | ベクトル命令分割処理モジュール |
| FPDecoder | 浮動小数点命令デコードモジュール |
| UopInfoGen | 命令分割タイプ・数量生成ユニット |
| VecDecoder | ベクトル命令デコードモジュール |
| VecExceptionGen | ベクトル例外チェックモジュール |
| VTypeGen | ベクトル命令vtype設定生成モジュール |

## 設計仕様

- ベクトル設定生成モジュール、ベクトルデコードモジュール、ベクトル命令分割モジュール、ベクトル例外チェックモジュールを新規追加。すべてのベクトル命令は命令分割を行い、decoderCompに入る
- 同一サイクル内で6つのスカラー命令を同時にデコードすることをサポート
- 同一サイクル内で最大1つのベクトル命令をデコードすることをサポート
- 一部の命令は変換処理を行う
  - zimop命令は、srcがx0、immが0のaddi命令に変換
  - vlenb読み取り命令は、srcがx0、immがVLEN/8のaddi命令に変換
  - vl読み取り命令は、vlレジスタを読み取りスカラーレジスタに書き込むvset命令に変換
- 読み取り専用権限のcsrを読み取る際、waitForwardおよびblockBackward信号をセットせず、アウトオブオーダー実行をサポート
- その他の機能は南湖と同じ

## 機能

命令をデコードし、命令の32ビットエンコーディングを命令の制御信号に変換します。命令がベクトル命令またはAMO_CAS命令の場合、命令分割が必要です。命令分割のプロセスは、命令を1つ以上のuopに分割し、分割タイプに基づいてソースレジスタ番号、ソースレジスタタイプ、デスティネーションレジスタ番号、デスティネーションレジスタタイプ、使用する機能ユニット、操作タイプに新しい値を割り当てることです。デコード完了後、制御情報を持つ命令をrenameモジュールに渡し、renameモジュールはソースレジスタ番号とソースレジスタタイプに基づいて物理レジスタをリネーム割り当てします。デコード段階で例外命令、例外仮想化命令をチェックし、対応するexceptionVec内の信号をハイにします。

## 全体設計

デコードは6つのDecodeUnitモジュールをインスタンス化して入力命令をデコードします。DecodeUnitは命令がベクトル命令であるかどうかの信号を出力し、ベクトル命令であれば、複雑なデコーダdecoderCompに渡して命令分割を行う必要があります。
ベクトル命令はDecodeUnitとUopInfoGenでデコードされてから複雑なデコーダに入るため、クリティカルパスが長くなります。命令が複雑なデコーダに入ると、まず1サイクル保持され、次のサイクルでベクトル例外チェックと命令分割が行われ、1つ以上のuopに変換されます。uopが6つを超える場合、デコードを完了するのに複数サイクルが必要になります。残りのuopが
そのサイクルでデコードを完了できる場合、デコードが必要なベクトル命令はそのサイクルでdecoderCompに渡されます。
renameがreadyであると仮定すると、入力される命令の順序によって、以下のようないくつかのケースに分けられます。

1. スカラー命令：直接デコード
2. ベクトル命令：decoderCompがreadyのとき、ベクトル命令をdecoderCompに渡して命令分割を行う。一度に1つのベクトル命令しか処理できない
3. ベクトル命令+スカラー命令：decoderCompがreadyのとき、ベクトル命令をdecoderCompに渡して分割する。一度に1つのベクトル命令しか処理できず、同時にスカラー命令を処理することはできない
4. スカラー命令+ベクトル命令：ベクトル命令より前のスカラー命令は直接デコードする。decoderCompがreadyのとき、ベクトル命令をdecoderCompに渡して命令分割を行う。一度に1つのベクトル命令しか処理できない
5. 命令分割後のuop+スカラー命令：そのサイクルでrenameが必要な分割後のuopがn個、renameが必要なスカラー命令がm個あると仮定する。n+m<=6の場合、直接デコードする。そうでない場合は、6-n個のスカラー命令のみをデコードする
6. 命令分割後のuop+ベクトル命令：ベクトル命令分割後のuopの処理はベクトル命令の場合と同じ
7. 命令分割後のuop+ベクトル命令+スカラー命令：スカラー命令+ベクトル命令の場合と同じ
8. 命令分割後のuop+スカラー命令+ベクトル命令：スカラー命令の処理は命令分割後のuop+スカラー命令の場合と同じ、ベクトル命令の処理はベクトル命令の場合と同じ

## 全体ブロック図

![decode](./figure/decode.svg)

## インターフェースリスト

インターフェースドキュメントを参照

## 二次モジュール VTypeGen

VTypeGenモジュールは、主に現在デコード中のベクトル命令が使用するvtype設定を維持するために使用されます。vset命令が実行されるたび、またはリダイレクトが発生してロールバックが必要になるたびに、VTYpeGenに保存されているvtype情報が更新されます。

### 入力

- フロントエンドからの命令ストリーム内の32ビット命令情報
- rob内のvtypeバッファからのvtypeロールバック情報
- rob内のvtypeバッファからのvtypeコミット情報
- バックエンドからのvsetvl命令のvtype情報。vsetvl命令のvtype情報はデコードではなくレジスタ読み取りによって取得する必要があるため、vsetvl命令が書き戻される際に、vtype情報がvtypeGenに渡されます。

### 出力

Decode Unitへのvtype情報（現在デコード段階にあるベクトル命令が使用するvtype設定）

### 設計仕様

vtypeSpecの更新には4つのケースがあります。

1. vsetvl命令がコミットされるとき、vtypeSpecはvsetvl命令のvtypeに更新されます。vsetvl命令のvtype値はその書き戻し時に取得されます。vsetvl命令はパイプラインをフラッシュするため、他のケースと競合することはありません。
2. リダイレクトのロールバック中、vtypeSpecはvtypeバッファから渡されたwalkVTypeに更新されます。
3. リダイレクト開始時、vtypeSpecはArch vtypeに更新されます。
4. デコードされた命令にvsetivliまたはvsetvli命令が存在し、かつ例外が発生していない場合、vsetivli命令とvsetvli命令のvtype情報は即値フィールドから取得できます。VTypeGenには、入力命令にこれらの2つの命令が含まれているかどうかを判断するための簡単なデコーダがあります。これらのvset命令が存在する場合、PriorityMuxを介して最初のvset命令を選択し、`VsetModule`モジュールを介してvtype情報を解析します。

```scala
  when(io.commitVType.hasVsetvl) {
    vtypeSpecNext := io.vsetvlVType
  }.elsewhen(io.walkVType.valid) {
    vtypeSpecNext := io.walkVType.bits
  }.elsewhen(io.walkToArchVType) { 
    vtypeSpecNext := vtypeArch
  }.elsewhen(inHasVset && io.canUpdateVType) {
    vtypeSpecNext := vtypeNew
  }
```

vtypeArchの更新には2つのケースがあります。
1. vsetvl命令がコミットされるとき、vtypeArchはvsetvl命令が書き戻したvtypeに更新されます。
2. vsetivli命令またはvsetvli命令がコミットされるとき、vtypeArchはvtypeバッファから渡されたvtypeコミット情報に更新されます。

## 二次モジュール DecodeUnit

### 入力と出力

- **入力**
     - DecodeUnitEnqIO：フロントエンドから渡される命令ストリーム情報、ベクトル命令が使用するvtype、vstart情報
     - CustomCSRCtrlIO：csr制御信号
     - CSRToDecode：csr制御信号
- **出力**
     - DecodeUnitDeqIO：デコード後の命令情報、ベクトル命令かどうか、命令分割数

### 機能

このモジュールは香山バックエンドのデコードユニットであり、このモジュールは制御フローをより情報豊富なマイクロオペレーションに変換します。これには、ソースレジスタ番号、ソースレジスタタイプ、デスティネーションレジスタ番号、デスティネーションレジスタタイプ、即値タイプ、使用する機能ユニットタイプ、操作タイプなどの情報が含まれます。

### 設計仕様

1. **デコード情報**
   - **XSDecode**
     DecodeConstantsで定義されているdecodeArrayは、命令の32ビットエンコーディングをXSDecodeに変換します。これには以下の情報が含まれます。

      - srcType0: ソースレジスタ0のタイプ
      - srcType1: ソースレジスタ1のタイプ
      - srcType2: ソースレジスタ2のタイプ（fma命令用）
      - fuType: 機能ユニットタイプ
      - fuOpType: 操作タイプ
      - rfWen: スカラーレジスタに書き戻すかどうか
      - fpWen: 浮動小数点レジスタに書き戻すかどうか
      - vfWen: ベクトルレジスタに書き戻すかどうか
      - isXSTrap：XSTrap命令かどうか
      - noSpecExec：アウトオブオーダー実行が可能かどうか、つまり前の命令のコミット完了を待たずに実行できるかどうか
      - blockBackward：後続の命令をブロックするかどうか、つまり現在の命令のコミット完了を待ってから後続の命令がrobに入れるかどうか
      - flushPipe：パイプラインをフラッシュする必要があるかどうか、つまり現在の命令がコミット完了後にパイプラインをフラッシュする必要があるかどうか
      - canRobCompress：命令がrob圧縮をサポートしているかどうか（例外をトリガーしない命令で、FTQの境界にない場合、Rob圧縮が可能と見なされます）
      - uopSplitType：命令分割タイプ。スカラー命令の分割タイプはすべてUopSplitType.SCA_SIMで分割不要、ベクトル命令とAMO_CAS命令は分割が必要。ベクトル命令が1つのuopに分割するだけで、命令制御信号の変更が不要な場合、分割タイプはUopSplitType.dummyとなり、ベクトル複雑デコーダでベクトル命令の例外チェックが行われます。

   - **VPUCtrlSignals**
     ベクトル命令と浮動小数点命令はVPUCtrlSignalsを設定する必要があります。VPUCtrlSignalsには、ベクトル設定用のsew、lmulなどの情報が含まれます。
     - ベクトル命令：ベクトル設定情報はDecodeStageのVtypeGenのvtype情報から取得します。
     - 浮動小数点命令：浮動小数点モジュールとベクトルモジュールは独立していますが、ベクトルと同じ演算ユニットを再利用しており、演算ユニットはsew情報によって要素のビット幅を指定するため、浮動小数点命令専用のデコードサブモジュールFPToVecDecoderを介して浮動小数点命令のVPUCtrlSignals制御信号を生成します。

   - **FPUCtrlSignals**
     デコードサブモジュールFPDecoderで生成されます。rm信号は浮動小数点丸めを制御し、wflagsはi2fモジュールとfflagの更新を制御し、残りの信号はi2fモジュールを制御します。
      ```scala
        class FPUCtrlSignals(implicit p: Parameters) extends XSBundle {
          val typeTagOut = UInt(2.W) // H S D
          val wflags = Bool()
          val typ = UInt(2.W)
          val fmt = UInt(2.W)
          val rm = UInt(3.W)
        }
    
      ```
    - **uopnum**
    `UopInfoGen`は命令分割の数を生成します。スカラー命令の命令分割数は1、AMO_CAS命令はタイプに応じて2または4、ベクトル命令の命令分割数はlmulに基づいて計算する必要があり、そのうちベクトルメモリアクセス命令はlmul、sew、eewに基づいて命令分割数を計算する必要があります。

2. **変換処理**
    - **move命令**
      move命令は特殊なaddi命令であるため、命令フィールドによってmove命令を識別し、後続のリネーム段階でmove削除を行います。
    - **zimop命令**
      zimop命令はvdを0に書き込むだけなので、srcがx0、immが0のaddi命令に変換されます。
    - **csrr vlenb命令**
      vlenbの値は固定なので、srcがx0、immがVLEN/8のaddi命令に変換されます。
    - **csrr vl命令**
      vlは独立したレジスタファイルを使用するため、リネームとアウトオブオーダー実行をサポートします。vl読み取り命令は、vlを読み取り対応するrdに書き込むvset命令に変換されます。
    - **ソフトプリフェッチ命令**
      fuTypeをFuType.ldu.Uに変更し、対応する機能ユニットに渡して処理します。

3. **例外処理**
    DecodeUnitでは`illegalInstr`（例外値2）と`virtualInstr`（例外値22）の2種類の例外を処理します。
    - **illegalInstr**
      - 即値選択が無効かどうかをチェック
      - 特定のCSR設定下で命令を実行した場合の例外
      - ベクトル関連の例外はこのモジュールではチェックせず、複雑なデコーダで行います。
    - **virtualInstr**
      - 特定のCSR設定下で命令を実行した場合の例外

### 二次モジュール DecodeUnitComp

### 入力と出力
  命令分割は命令内のオペランドレジスタ番号、オペランドタイプなどの情報を変更するだけなので、入力と出力のタイプは両方ともDecodeUnitCompInputです。vset命令のvtype情報はデコードによって取得する必要があり、vtypegenによって取得するわけではないため、vtypebypass信号を介して、vset命令が使用するvtypeをそのvset命令のvtype情報に更新します。
  - **DecodeUnitCompIO**
  ```scala
      class DecodeUnitCompIO(implicit p: Parameters) extends XSBundle {
        val redirect = Input(Bool())
        val csrCtrl = Input(new CustomCSRCtrlIO)
        val vtypeBypass = Input(new VType)
        // When the first inst in decode vector is complex inst, pass it in
        val in = Flipped(DecoupledIO(new DecodeUnitCompInput))
        val out = new DecodeUnitCompOutput
        val complexNum = Output(UInt(3.W))
      }
  
  ```

### 機能

1つのベクトル命令を、分割タイプとlmul情報に基づいて複数のマイクロオペレーションに生成し、マイクロオペレーション内のオペランドレジスタ番号、オペランドタイプなどの情報を変更します。同時に、ベクトル命令の例外チェックもこのモジュールで行われます。このモジュールはステートマシンを使用し、処理する命令がないか、分割された命令の処理が完了したサイクルでのみready信号がハイになり、次の命令を処理します。

### 設計仕様

現在、命令分割の種類は多いですが、将来的には簡素化・最適化される予定です。

| 分割タイプ | 対応する命令タイプ |
| --- | --- |
| AMO_CAS_W/AMO_CAS_D/AMO_CAS_Q | AMO_CAS命令 |
| VSET | vset命令 |
| VEC_VVV | 2つのソースレジスタとデスティネーションレジスタが両方ともベクトルレジスタである命令 |
| VEC_VFV | 1つのソースレジスタが浮動小数点レジスタで、1つのソースレジスタとデスティネーションレジスタが両方ともベクトルレジスタである命令 |
| VEC_EXT2/VEC_EXT4/VEC_EXT8 | ベクトル符号拡張命令 |
| VEC_0XV | スカラーからベクトルへのmove命令 |
| VEC_VXV | 1つのソースレジスタがスカラーレジスタで、1つのソースレジスタとデスティネーションレジスタが両方ともベクトルレジスタである命令 |
| VEC_VVW/VEC_VFW/VEC_WVW/VEC_VXW/VEC_WXW/VEC_WVV/VEC_WFW/VEC_WXV | widening/narrowベクトル命令 |
| VEC_VVM/VEC_VFM/VEC_VXM | デスティネーションレジスタがマスクレジスタであるベクトル命令 |
| VEC_SLIDE1UP | vslide1up命令 |
| VEC_FSLIDE1UP | vfslide1up命令 |
| VEC_SLIDE1DOWN | vslide1down命令 |
| VEC_FSLIDE1DOWN | vfslide1down命令 |
| VEC_VRED | スカラーreduction命令 |
| VEC_VFRED | アウトオブオーダー浮動小数点reduction命令 |
| VEC_VFREDOSUM | 順序付き浮動小数点reduction命令 |
| VEC_SLIDEUP | vslideup命令 |
| VEC_SLIDEDOWN | vslidedown命令 |
| VEC_M0X | vcpop命令 |
| VEC_MVV | vid/viota命令 |
| VEC_VWW | スカラーwidening reduction命令 |
| VEC_RGATHER | vrgather命令 |
| VEC_RGATHER_VX | オペランドの1つがスカラーレジスタからのvrgather命令 |
| VEC_RGATHEREI16 | vrgatherei16命令 |
| VEC_COMPRESS | vcompress命令 |
| VEC_MVNR | vmvnr命令 |
| VEC_US_LDST | unit-stride load/store命令 |
| VEC_S_LDST | strided load/store命令 |
| VEC_I_LDST | indexed load/store命令 |

## 二次モジュール VecExceptionGen

- **入力:**
  - `inst`：32ビット命令
  - `decodedInst`：デコード後の情報
  - `vtype`：vtype情報
  - `vstart`：vstart情報

- **出力:**
  - `illegalInst`：命令が不正かどうか

### 機能

ベクトル命令が例外を発生させるかどうかをチェックします。ベクトルメモリアクセス命令のメモリアクセス関連の例外を除き、すべてデコード段階でチェックされます。

### 設計仕様

ベクトル命令関連の例外は、以下の8種類に分類されます。

| 例外名 | 説明 |
| --- | --- |
| inst Illegal | 予約命令で例外が発生 |
| vill Illegal | vtypeのvillフィールドが1の場合、vset以外のベクトル命令を実行すると例外が発生 |
| EEW Illegal | ベクトル浮動小数点命令、符号拡張命令、widening命令、narrow命令のeew例外 |
| EMUL Illegal | ベクトルメモリアクセス命令、符号拡張命令、widening命令、narrow命令、vrgatherei16命令のelmul例外 |
| Reg Number Align | vs1、vs2、vdがlmulにアラインされていない |
| v0 Overlap | 一部の命令がv0レジスタを読み取りながら同時にv0を変更すると例外が発生 |
| Src Reg Overlap | 一部の命令でvs1、vs2、vdが重複すると例外が発生 |
| vstart Illegal | vstartが0でない場合、vsetとベクトルメモリアクセス命令以外のベクトル命令を実行すると例外が発生 |

これらのいずれかが例外をトリガーすると、例外信号がハイになります。
