# RXDAT

## 機能説明
RXDATチャネルからデータ付きの応答メッセージを受け入れ、データをRefillBufferに保存し、同時にメッセージ内のtxnIDを使用してmshrIDを識別し、応答をMSHRCtlに送信します。CHI.IssueBが処理する必要がある応答にはCompDataが含まれます。CHI.IssueCが処理する必要がある応答にはDataSepRespが含まれます。

## 全体ブロック図
![RXDAT](./figure/RXDAT.svg)

## インターフェースタイミング
リクエストを受信した同じサイクルでMSHRに通知します。最初のビートの場合はラッチし、2番目のビートの場合は最初のビートのデータと組み合わせて同じサイクルでRefillBufに書き込みます。
