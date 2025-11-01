# P-Credit管理メカニズム

## 機能説明
CHIプロトコル2.3.2のRetryの説明によると、P-Credit管理は以下のルールに従います。
1. RXRSPチャネルがPCrdGrantを受信すると、CAMはこの操作のPCrdTypeとSrcIDを記録します。
2. この時点で、特定のスライスに同じタイプ{PCrdType, SrcID}のPCreditを待っているMSHRがある場合、このPCreditはそのスライスに割り当てられます。
   - 複数のスライスが同時にヒットした場合、このPCreditはRoundRobin方式で割り当てられ、CAM内の対応するレコードは削除されます。
   - どのスライスもヒットしない場合、CAMは将来の使用のためにPCrdTypeとSrcIDを保存します（プロトコルでは、PCrdGrantはRetryAckの前に発行されることが許可されています）。
3. ヒットしたスライスについて、複数のMSHRが{PCrdType, SrcID}にヒットした場合、RoundRobin方式で1つのMSHRに割り当てられます。
4. 各MSHRについて：
   - RetryAckを受信すると、PTypeとSrcIDを保存し、pValid信号をアサートして、PCreditを待っていることをCAMに通知します。
   - CAMで一致するPCreditが見つかった場合、MSHRはpValidをデアサートし、CAMから一致するエントリを削除して操作を完了します。
   - CAMで一致するPCreditが見つからない場合、対応するPCreditが受信されるまでpValidはアサートされたままになります。
