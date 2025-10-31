# WayLookupサブモジュール ドキュメント

WayLookupは、IPrefetchPipeがMetaArrayとITLBをクエリして得たメタデータをMainPipeが使用するために一時的に保存するFIFO構造です。また、MSHRがSRAMキャッシュラインに書き込むのを監視し、ヒット情報を更新します。更新ロジックはIPrefetchPipeと同じです。IPrefetchPipeサブモジュールドキュメントの「ヒット情報の更新」セクションを参照してください。

![WayLookupキュー構造](../figure/ICache/WayLookup/waylookup_structure_rw.png)

![WayLookupヒット情報更新](../figure/ICache/WayLookup/waylookup_structure_update.png)

バイパスは許可されています（つまり、WayLookupが空の場合、エンキューリクエストを直接デキューします）。更新ロジックのレイテンシがDataArrayのアクセスパスに導入されるのを避けるため、MSHRに新しい書き込みがある場合はデキューがブロックされます。MainPipeのS0ステージもDataArrayにアクセスするため、MSHRに新しい書き込みがある場合はそれ以上進むことができず、この措置は追加の影響を与えません。

## GPaddr領域節約メカニズム

`gpaddr`はゲストページフォールトが発生した場合にのみ関連し、各gpfの後、フロントエンドは誤ったパスで動作するため（バックエンドはgpfの前またはgpf自体の誤予測/例外により、フロントエンドへのリダイレクト（WayLookupフラッシュ）を保証します）、WayLookupはリセット/フラッシュ後の最初の有効なgpfのgpaddrのみを保存する必要があります。デュアルラインリクエストの場合、gpfを持つ最初のラインの`gpaddr`のみを保存する必要があります。

実装では、gpf関連の信号（現在は`gpaddr`のみ）は他の信号（`paddr`など）から2つのバンドルに分離されます。他の信号はnWayLookupSize回インスタンス化されますが、gpf関連の信号は単一のレジスタとしてインスタンス化されます。`gpfPtr`ポインタも使用されます。これにより、レジスタで合計$(\text{nWayLookupSize}*2-1)* \text{GPAddrBits} - \log_2{(\text{nWayLookupSize})} - 1$ビットが節約されます。プリフェッチがWayLookupに書き込むとき、gpfが発生し、WayLookupに既存のgpfが存在しない場合、gpf/gpaddrは`gpf_entry`レジスタに書き込まれ、`gpfPtr`は現在の`writePtr`に設定されます。MainPipeがWayLookupから読み取るとき、バイパスする場合、プリフェッチでエンキューされたデータを直接デキューします。それ以外の場合、`readPtr === gpfPtr`であればgpf_entryを読み取ります。それ以外の場合はすべてゼロを読み取ります。注意：

1. デュアルラインリクエストの場合、1つの`gpaddr`のみを保存する必要があります（最初のラインがgpfをトリガーした場合、2番目のラインはすでに誤ったパス上にあり、保存する必要はありません）。ただし、gpf信号自体は、IFUがクロスライン例外であるかどうかを判断する必要があるため、2回保存する必要があります。
2. `readPtr===gpfPtr`という条件は、フラッシュが遅い場合に`readPtr`がループして再び`gpfPtr`と一致し、誤ってgpfを再読み取りする可能性があります。ただし、前述のように、これは誤ったパスで発生するため、gpfの再読み取りは重要ではありません。
3. 特殊なケースに注意してください：2つのページにまたがるフェッチブロックで、最初の32Bが例外なく前のページにあり、最後の2Bが次のページでgpfをトリガーする場合、最初の32Bがたまたま16個のRVC圧縮命令である場合、IFUは最後の2Bとその対応する例外情報を破棄します。これにより、次のフェッチブロックの`gpaddr`が失われる可能性があります。WayLookupに未請求のgpfと関連情報が既にある場合、エンキューをブロックする必要があります（つまり、IPrefetchPipe s1ステージ）。PR#3719を参照してください。
