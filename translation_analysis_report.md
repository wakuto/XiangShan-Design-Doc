# 翻訳整合性チェック - 詳細分析レポート

- 総ファイル数: 104
- 問題なし: 45
- 問題あり: 59


## 🔴 重大（80%以上の翻訳不足） (9件)

| ファイル | 中国語版行数 | 日本語版行数 | 差異率 | 見出し数(zh/ja) | 画像数(zh/ja) | コードブロック(zh/ja) |
|---------|------------|------------|--------|----------------|--------------|--------------------|
| `frontend/BPU/index.md` | 325 | 13 | 96.0% | 51/1 | 4/0 | 0/0 |
| `frontend/IFU/index.md` | 170 | 8 | 95.3% | 23/1 | 6/0 | 0/0 |
| `memblock/LSU/index.md` | 216 | 16 | 92.6% | 22/1 | 1/0 | 0/0 |
| `backend/VFPU.md` | 1146 | 94 | 91.8% | 51/8 | 23/1 | 6/0 |
| `memblock/MMU/L2TLB/index.md` | 148 | 15 | 89.9% | 12/1 | 5/0 | 0/0 |
| `frontend/Pruned_Address/index.md` | 34 | 4 | 88.2% | 4/1 | 0/0 | 0/0 |
| `backend/HPM.md` | 789 | 93 | 88.2% | 21/13 | 1/1 | 0/0 |
| `memblock/DCache/index.md` | 107 | 13 | 87.9% | 14/1 | 1/0 | 0/0 |
| `memblock/LSU/LSQ/index.md` | 70 | 14 | 80.0% | 7/1 | 3/0 | 0/0 |

## 🟠 高（50-80%の翻訳不足） (11件)

| ファイル | 中国語版行数 | 日本語版行数 | 差異率 | 見出し数(zh/ja) | 画像数(zh/ja) | コードブロック(zh/ja) |
|---------|------------|------------|--------|----------------|--------------|--------------------|
| `memblock/LSU/VLSU/index.md` | 51 | 13 | 74.5% | 6/1 | 0/0 | 0/0 |
| `backend/CtrlBlock/Rename.md` | 340 | 100 | 70.6% | 55/17 | 22/2 | 0/0 |
| `backend/CtrlBlock/decode.md` | 290 | 98 | 66.2% | 23/12 | 1/1 | 6/0 |
| `memblock/MMU/L2TLB/PageCache.md` | 180 | 62 | 65.6% | 18/4 | 1/0 | 0/0 |
| `frontend/BPU/TAGE-SC.md` | 286 | 101 | 64.7% | 22/6 | 8/2 | 0/2 |
| `backend/DataPath/DataPath.md` | 273 | 99 | 63.7% | 34/16 | 3/1 | 4/0 |
| `backend/CSR.md` | 244 | 101 | 58.6% | 14/6 | 0/0 | 0/0 |
| `frontend/BPU/FTB.md` | 209 | 93 | 55.5% | 19/17 | 7/6 | 0/0 |
| `memblock/LSU/LSQ/LoadQueueUncache.md` | 222 | 101 | 54.5% | 14/8 | 6/2 | 0/0 |
| `memblock/MMU/PMP-PMA.md` | 212 | 100 | 52.8% | 14/9 | 4/0 | 0/0 |
| `index.md` | 27 | 13 | 51.9% | 3/1 | 0/0 | 0/0 |

## 🟡 中（30-50%の翻訳不足または構造的不一致） (19件)

| ファイル | 中国語版行数 | 日本語版行数 | 差異率 | 見出し数(zh/ja) | 画像数(zh/ja) | コードブロック(zh/ja) |
|---------|------------|------------|--------|----------------|--------------|--------------------|
| `memblock/LSU/Uncache.md` | 187 | 97 | 48.1% | 11/6 | 5/1 | 0/0 |
| `backend/DebugModule/DM.md` | 160 | 93 | 41.9% | 13/10 | 2/2 | 0/0 |
| `memblock/MMU/L2TLB/LLPTW.md` | 82 | 49 | 40.2% | 11/9 | 2/0 | 0/0 |
| `memblock/MMU/L2TLB/PTW.md` | 90 | 55 | 38.9% | 10/8 | 1/1 | 0/0 |
| `backend/index.md` | 21 | 13 | 38.1% | 2/1 | 1/0 | 0/0 |
| `frontend/BPU/RAS.md` | 152 | 100 | 34.2% | 21/14 | 10/5 | 0/0 |
| `cache/l2cache/DataStorage.md` | 3 | 4 | 33.3% | 1/1 | 0/0 | 0/0 |
| `memblock/DCache/Error.md` | 191 | 130 | 31.9% | 11/9 | 8/5 | 0/0 |
| `memblock/LSU/LSQ/LoadQueueReplay.md` | 136 | 93 | 31.6% | 10/5 | 8/2 | 0/0 |
| `memblock/LSU/LSQ/StoreQueue.md` | 291 | 206 | 29.2% | 19/9 | 10/3 | 0/0 |
| `backend/CtrlBlock/Rob.md` | 139 | 102 | 26.6% | 13/5 | 4/3 | 2/2 |
| `memblock/LSU/LoadUnit.md` | 204 | 162 | 20.6% | 12/8 | 3/0 | 0/0 |
| `backend/Schedule_And_Issue/IssueQueueEntries.md` | 129 | 105 | 18.6% | 13/13 | 11/6 | 0/0 |
| `memblock/LSU/VLSU/VfofBuffer.md` | 43 | 46 | 7.0% | 7/7 | 0/0 | 0/2 |
| `memblock/LSU/VLSU/VSMergeBuffer.md` | 55 | 58 | 5.5% | 8/8 | 0/0 | 0/2 |
| `memblock/LSU/VLSU/VLMergeBuffer.md` | 59 | 62 | 5.1% | 9/9 | 0/0 | 0/2 |
| `memblock/MMU/Repeater.md` | 74 | 77 | 4.1% | 12/12 | 4/4 | 0/2 |
| `memblock/LSU/VLSU/VSegmentUnit.md` | 133 | 136 | 2.3% | 11/11 | 2/2 | 0/2 |
| `memblock/MMU/L1TLB.md` | 416 | 417 | 0.2% | 31/31 | 11/11 | 0/2 |

## 🟢 低（軽微な不一致） (20件)

| ファイル | 中国語版行数 | 日本語版行数 | 差異率 | 見出し数(zh/ja) | 画像数(zh/ja) | コードブロック(zh/ja) |
|---------|------------|------------|--------|----------------|--------------|--------------------|
| `cache/l2cache/downstream/PCredit.md` | 15 | 11 | 26.7% | 2/2 | 0/0 | 0/0 |
| `memblock/LSU/VLSU/VSSplit.md` | 131 | 97 | 26.0% | 10/8 | 0/0 | 0/0 |
| `memblock/LSU/VLSU/VLSplit.md` | 128 | 99 | 22.7% | 8/6 | 0/0 | 0/0 |
| `cache/l2cache/upstream/SinkC.md` | 18 | 14 | 22.2% | 5/5 | 1/1 | 0/0 |
| `backend/DataPath/BypassNetwork.md` | 127 | 99 | 22.0% | 8/7 | 1/1 | 0/0 |
| `cache/l2cache/Directory.md` | 5 | 6 | 20.0% | 1/1 | 1/1 | 0/0 |
| `backend/ExuBlock/ExuUnit.md` | 126 | 101 | 19.8% | 6/5 | 1/1 | 0/0 |
| `cache/l2cache/ReqBuf.md` | 46 | 37 | 19.6% | 8/8 | 1/1 | 0/0 |
| `cache/l2cache/downstream/LinkMonitor.md` | 29 | 24 | 17.2% | 7/7 | 1/1 | 0/0 |
| `cache/l2cache/downstream/TXRSP.md` | 19 | 16 | 15.8% | 5/5 | 1/1 | 0/0 |
| `cache/l2cache/downstream/RXDAT.md` | 13 | 11 | 15.4% | 4/4 | 1/1 | 0/0 |
| `memblock/LSU/StoreMisalignBuffer.md` | 106 | 91 | 14.2% | 9/9 | 4/4 | 0/0 |
| `cache/l2cache/upstream/GrantBuffer.md` | 44 | 38 | 13.6% | 6/6 | 1/1 | 0/0 |
| `cache/l2cache/downstream/TXDAT.md` | 15 | 13 | 13.3% | 4/4 | 1/1 | 0/0 |
| `frontend/ICache/WayLookup.md` | 23 | 20 | 13.0% | 2/2 | 2/2 | 0/0 |
| `memblock/LSU/AtomicsUnit.md` | 113 | 99 | 12.4% | 6/6 | 4/4 | 0/0 |
| `frontend/ICache/MissUnit.md` | 25 | 22 | 12.0% | 5/5 | 1/1 | 0/0 |
| `backend/CtrlBlock/Dispatch.md` | 110 | 99 | 10.0% | 18/16 | 2/2 | 0/0 |
| `backend/DataPath/WbDataPath.md` | 111 | 101 | 9.0% | 20/19 | 2/2 | 0/0 |
| `memblock/LSU/StoreUnit.md` | 107 | 101 | 5.6% | 8/7 | 3/2 | 0/0 |

## 推奨対応策

### 🔴 重大問題への対応

以下のファイルは翻訳がほとんど完了していません（80%以上の内容が未翻訳）。優先的に対応が必要です：

1. `frontend/BPU/index.md` - 96.0%未翻訳（325行中312行が未翻訳）
1. `frontend/IFU/index.md` - 95.3%未翻訳（170行中162行が未翻訳）
1. `memblock/LSU/index.md` - 92.6%未翻訳（216行中200行が未翻訳）
1. `backend/VFPU.md` - 91.8%未翻訳（1146行中1052行が未翻訳）
1. `memblock/MMU/L2TLB/index.md` - 89.9%未翻訳（148行中133行が未翻訳）
1. `frontend/Pruned_Address/index.md` - 88.2%未翻訳（34行中30行が未翻訳）
1. `backend/HPM.md` - 88.2%未翻訳（789行中696行が未翻訳）
1. `memblock/DCache/index.md` - 87.9%未翻訳（107行中94行が未翻訳）
1. `memblock/LSU/LSQ/index.md` - 80.0%未翻訳（70行中56行が未翻訳）

### 🟠 高優先度問題への対応

以下のファイルは翻訳が半分程度しか完了していません。早急な対応が推奨されます：

- `memblock/LSU/VLSU/index.md` - 74.5%未翻訳
- `backend/CtrlBlock/Rename.md` - 70.6%未翻訳
- `backend/CtrlBlock/decode.md` - 66.2%未翻訳
- `memblock/MMU/L2TLB/PageCache.md` - 65.6%未翻訳
- `frontend/BPU/TAGE-SC.md` - 64.7%未翻訳
- `backend/DataPath/DataPath.md` - 63.7%未翻訳
- `backend/CSR.md` - 58.6%未翻訳
- `frontend/BPU/FTB.md` - 55.5%未翻訳
- `memblock/LSU/LSQ/LoadQueueUncache.md` - 54.5%未翻訳
- `memblock/MMU/PMP-PMA.md` - 52.8%未翻訳
- `index.md` - 51.9%未翻訳

### 🟡 中優先度問題への対応

以下のファイルは部分的に翻訳が不完全、または構造的な不一致があります：

- `backend/CtrlBlock/Rob.md`
- `backend/DebugModule/DM.md`
- `backend/Schedule_And_Issue/IssueQueueEntries.md`
- `backend/index.md`
- `cache/l2cache/DataStorage.md`
- `frontend/BPU/RAS.md`
- `memblock/DCache/Error.md`
- `memblock/LSU/LSQ/LoadQueueReplay.md`
- `memblock/LSU/LSQ/StoreQueue.md`
- `memblock/LSU/LoadUnit.md`
- `memblock/LSU/Uncache.md`
- `memblock/LSU/VLSU/VLMergeBuffer.md`
- `memblock/LSU/VLSU/VSMergeBuffer.md`
- `memblock/LSU/VLSU/VSegmentUnit.md`
- `memblock/LSU/VLSU/VfofBuffer.md`
- `memblock/MMU/L1TLB.md`
- `memblock/MMU/L2TLB/LLPTW.md`
- `memblock/MMU/L2TLB/PTW.md`
- `memblock/MMU/Repeater.md`

## カテゴリ別分析

| カテゴリ | 総ファイル数 | 問題ファイル数 | 完了率 |
|---------|------------|--------------|--------|
| backend | 24 | 14 | 41.7% |
| cache | 19 | 10 | 47.4% |
| frontend | 18 | 8 | 55.6% |
| index.md | 1 | 1 | 0.0% |
| memblock | 42 | 26 | 38.1% |
