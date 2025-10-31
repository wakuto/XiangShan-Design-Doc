# MainPipeサブモジュール ドキュメント

MainPipeはICacheのメインパイプラインであり、2ステージパイプラインとして設計されています。DataArrayからのデータ読み取り、PMPチェック、ECCチェック、ミス処理、およびIFUへの結果返却を担当します。

![MainPipe構造](../figure/ICache/MainPipe/mainpipe_structure.png)

## S0パイプラインステージ

S0パイプラインステージでは、WayLookupからウェイヒット情報やITLBクエリ結果などのメタデータを取得し、DataArrayの単一ウェイにアクセスします。DataArrayが書き込み中であるか、WayLookupに有効なエントリがない場合、パイプラインはストールします。各リダイレクト後、FTQからの同じリクエストがMainPipeとIPrefetchPipeに同時に送信されます。MainPipeは常にIPrefetchPipeがクエリ情報をWayLookupに書き込むのを待ってから続行するため、1サイクルのリダイレクトレイテンシが発生します。このレイテンシは、プリフェッチが命令フェッチを上回る場合に隠蔽されます。

## S1パイプラインステージ

1. リプレーサにタッチリクエストを送信して更新します。
2. PMPチェック：PMPリクエストを送信し、同じサイクルで応答を受信し、次のパイプラインステージで処理するために結果を登録します。
   - IPrefetchPipe s1パイプラインステージもPMPチェックを実行しますが、これはここで行われるものと同一です。タイミングを最適化するために個別のチェックが実施されます（過度に長い組み合わせロジックパスを回避するため：`ITLB(reg) -&gt; ITLB.resp -&gt; PMP.req -&gt; PMP.resp -&gt; WayLookup.write -&gt; bypass -&gt; WayLookup.read -&gt; MainPipe s1(reg)`）。
3. DataArrayから返されたデータとコードを受信して登録し、MSHR応答を監視します。DataArrayとMSHRの両方の応答が有効な場合、後者が優先されます。

## S2パイプラインステージ

1. DataArray ECC検証：S1パイプラインステージで登録されたコードをチェックします。検証に失敗した場合、BEUにエラーを報告します。
2. MetaArray ECC検証：IPrefetchPipeがMetaArrayからデータを読み取った後、直接検証を実行し、検証結果とヒット情報をWayLookupにエンキューします。これはMainPipeを介してS2ステージに流れ、DataArrayからのECC検証結果とともにBEUに報告されます。
3. Tilelinkエラー処理：corrupt信号がハイのMissUnit応答を監視する場合（L2キャッシュ応答データエラーを示す）、BEUにエラーを報告します。
4. ミス処理：ミス時にMissUnitにリクエストを送信し、MSHR応答を監視します。ヒット時には、MSHR応答データを登録し、タイミング最適化のために次のサイクルでIFUに送信します。
