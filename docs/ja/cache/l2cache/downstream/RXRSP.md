# RXRSP

## 機能説明
RXRSPチャネルからデータなしの応答メッセージを受信し、メッセージ内のtxnIDを使用してmshrIDを識別し、MSHRCtlに直接転送します。CHI.IssueBが処理する必要がある応答には、Comp、CompDBIDResp、Retry、PCrdGrantが含まれます。CHI.IssueCが必要とする応答はRespSepDataです。

## 全体ブロック図
![RXRSP](./figure/RXRSP.svg)
