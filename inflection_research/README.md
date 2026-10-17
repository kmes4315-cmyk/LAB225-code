# 成長拐點研究 v1（第一階段）

依《成長拐點研究 V1：研究邏輯》（2026-10-16 確認版）實作的季度拐點篩選。
只做研究紀錄：不產生買賣訊號、不讀持倉。

## 檔案

| 檔案 | 用途 |
|---|---|
| `config/inflection_research_v1.yaml` | 門檻、時間、資料來源，以及這次執行採用的解讀（第一期後凍結） |
| `src/pit_rotation/inflection.py` | 時點過濾、單季推導（含 Q4 = 年度 − 前三季）、TTM、六道門檻、拐點來源分類 |
| `src/pit_rotation/universe.py` | 主要代號、申報類型、封面股數、股價與分割 |
| `src/pit_rotation/records.py` | 只能追加的紀錄（SHA-256 雜湊鏈），舊紀錄被改動就停 |
| `src/pit_rotation/fetch.py` | 限速下載與快取，每個回應的 SHA-256 記在 `fetch_log.jsonl` |
| `scripts/fetch_sec_v1.py` | 抓 SEC 代號清單、submissions、XBRL companyfacts |
| `scripts/fetch_prices_v1.py` | 抓 Yahoo 日線（收盤、成交量、分割） |
| `scripts/run_inflection_snapshot_v1.py` | 產生季度快照並寫入 `data/prospective/inflection_v1/` |
| `scripts/extract_competition_v1.py` | 競爭地圖卡素材：10-K Competition 段落與反查點名 |
| `scripts/peer_metrics_v1.py` | 競爭地圖卡的規模對照（任何 SEC 上市公司） |
| `src/pit_rotation/fsds.py` | XBRL API 缺的申報，用 SEC 季度財報資料集補 |
| `tests/test_inflection_research.py` | 驗收測試 |

## 執行

```bash
export SEC_USER_AGENT="inflection-research <你的 email>"
python scripts/fetch_sec_v1.py --cache CACHE_DIR
python scripts/fetch_prices_v1.py --cache CACHE_DIR
python scripts/run_inflection_snapshot_v1.py --cache CACHE_DIR
python -m pytest -q tests
```

同一份快取重跑，輸出檔逐位元相同（manifest 只記決策時間、設定／程式／資料的雜湊，不記執行時間）。

## 第一期結果

- 報告：`docs/first_period_2026-10-16.md`
- 正式紀錄：`data/prospective/inflection_v1/2026-10-16-r1/`（修正並取代 `2026-10-16`，兩者都保留）
- 競爭地圖卡：`data/inflection/competitor_cards_v1/2026-10-16/cards.md`
- 產業地圖（對手、市佔推估、商業模式對比，含卡片勘誤）：`data/inflection/industry_maps_v1/2026-10-16/`
- 原始資料下載紀錄（SHA-256）：`data/provenance/`
