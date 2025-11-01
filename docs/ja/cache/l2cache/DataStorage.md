# データSRAM DataStorage
DataStorage モジュールは CoupledL2 のデータ SRAM の読み書きを担当し、単一ポート SRAM で構成される。要求は MainPipe の s3 ステージでのみ DataStorage とやり取りし、各サイクルで処理できる読み出しまたは書き込み要求は 1 件のみである。
