# 產業地圖：semis 組（MTSI、LSCC、MCHP、COHU）

決策時間 2026-10-16，資料截至 2026-10-17。

**標記說明**
- 【證實】：來源原文直接寫的數字或事實（我讀過原文）。
- 【推估】：我用來源數字自己算的，算法寫在旁邊。
- 【公司說法】：新聞稿、法說會、公司簡報的自述，未經第三方查核。
- 【摘要】：只透過搜尋引擎摘要或二手轉述取得，沒有讀到原文，信心較低。
- 匯率（只用於換算量級，屬推估）：新台幣 31–32.5／美元；日圓 147–152／美元；人民幣 7.2／美元。
- 本機資料：`competitor_cards_v1/2026-10-16/cards.md`、`peer_metrics.jsonl`（下稱「peer_metrics」，TTM 至 2026 年 6–8 月，GAAP）。

---

### MTSI　MACOM Technology Solutions

- **市場怎麼定義**：MACOM 賣高效能類比、射頻與光電元件，按三個終端市場報營收。FY2025（截至 2025-10-03）營收 9.673 億美元：工業國防（I&D）4.198 億（43.4%）、資料中心 2.928 億（30.3%）、電信 2.546 億（26.3%）【證實，[10-K FY2025](https://www.sec.gov/Archives/edgar/data/1493594/000149359425000054/mtsi-20251003.htm)】。三塊沒有共同的第三方市場規模，以下分開列：
  - **公司自估 SAM**：2027 年約 150 億美元，I&D 60 億、資料中心 60 億、電信 30 億，比 2026 年高約 20–30%【公司說法，[FY26Q3 法說逐字稿](https://www.webull.com/news/15396902106440704)，2026-08-06】。FY22 簡報寫的是 I&D 20 億、資料中心 10 億、電信 20 億【公司說法，[Q3FY22 簡報](https://www.macom.com/files/live/sites/macom/files/Home%20Page/MACOM%20Q3FY22%20Corporate%20Presentation.pdf)】。FY25Q1 法說寫 70–80 億【摘要，[MarketBeat 逐字稿](https://www.marketbeat.com/earnings/reports/2025-2-6-macom-technology-solutions-holdings-inc-stock)】。四年內 SAM 從 50 億變成 150 億，主要是公司擴大產品線與定義，不是市場真的成長三倍。
  - **資料中心（第三方）**：LightCounting 估光通訊 IC 晶片組（DSP、driver、TIA 等）2024 年約 35 億美元，2030 年超過 110 億【證實，[LightCounting 2025-04](https://www.lightcounting.com/newsletter/en/february-2025-pam4-and-coherent-dsps-updated-april-2025-340)】。2025 年 PAM4 晶片組銷售「超過倍增」，相干 DSP 成長 16%，但沒公開 2025 年總額【證實，[LightCounting 2026-02](https://www.lightcounting.com/newsletter/en/february-2026-pam4-and-coherent-dsps-updated-april-2026-381)】。光模組本身 2025 年 238 億美元，年增 55%【證實，[LightCounting 2026-03](https://www.lightcounting.com/newsletter/en/march-2026-quarterly-market-update-380)】。
  - **國防（第三方，局部）**：Yole 估 RF GaN 2025 年約 13 億美元，其中國防 5.92 億美元，2031 年到 10 億【證實，[Compound Semiconductor 轉述 Yole](https://compoundsemiconductor.net/article/123465/RF_GaN_geopolitics_fuel_sustained_growth)、[Electronics Weekly](https://www.electronicsweekly.com/news/business/rf-gan-on-11-cagr-to-hit-2-4bn-in-2031-2026-02/)】。MACOM 的 I&D 還包含 GaAs、二極體、工業、醫療、量測，所以這個 GaN 數字只能當局部參考，不能直接當分母。

- **所有玩家**：

| 公司 | 上市地／代號 | 和這家公司的關係（直接對手／替代品） | 相關營收或規模（口徑、期間） | 推估市佔 | 定位 | 來源 |
|---|---|---|---|---|---|---|
| **MACOM** | Nasdaq: MTSI | 本公司 | 全公司 FY2025 9.673 億；TTM 至 2026-07 11.64 億；FY2026E 13.23 億【推估：Q1–Q3 實際加上 Q4 指引中值】 | 自估 SAM 的 10.6–11.5%【推估】 | 三個市場都是第二梯隊，成長加速中 | 10-K、[Q3 FY26 新聞稿](https://www.sec.gov/Archives/edgar/data/1493594/000149359426000036/ex99_1earningsreleaseq3fy26.htm) |
| Broadcom | Nasdaq: AVGO | 資料中心直接對手（DSP、driver、EML 與 VCSEL 雷射）；10-K 點名 | 光元件營收未揭露；全公司 TTM 891 億 | 未找到 | 資料中心龍頭之一 | peer_metrics |
| Marvell | Nasdaq: MRVL | 資料中心直接對手（PAM4 DSP 加 TIA、driver 綁售）；10-K 點名 | 資料中心終端市場 FY2026（至 2026-01）61.0 億，年增 46.5%，含客製 ASIC；光電部分未單獨揭露 | 未找到 | 資料中心龍頭之一 | [10-K](https://www.sec.gov/Archives/edgar/data/1835632/000183563226000011/mrvl-20260131.htm) |
| Semtech | Nasdaq: SMTC | 資料中心與 PON 直接對手（TIA、driver、CDR）；10-K 點名 | Signal Integrity 部門 FY2026（至 2026-01）3.226 億，年增 23.3%，部門毛利率 65.2% | 規模和 MACOM 資料中心相近 | 挑戰者 | [10-K](https://www.sec.gov/Archives/edgar/data/88941/000008894126000005/smtc-20260125.htm) |
| Credo | Nasdaq: CRDO | 直接對手兼替代品：AEC 主動電纜對上 MACOM 的銅纜線性等化器，另有光 DSP；10-K 點名 | FY2026（至 2026-05）營收 13 億，FY2025 4.368 億；前十大客戶約 90% | 未找到 | 成長最快的挑戰者 | [10-K](https://www.sec.gov/Archives/edgar/data/1807794/000162828026043303/crdo-20260502.htm) |
| MaxLinear | Nasdaq: MXL | 資料中心與電信直接對手（Keystone DSP、TIA、driver）；10-K 點名，也反向點名 MACOM | 基礎建設終端市場 FY2025 1.482 億，年增 30.1%；全公司 TTM GAAP 營益率 −13.6% | 未找到 | 落後（獲利） | [10-K](https://www.sec.gov/Archives/edgar/data/1288469/000128846926000011/mxl-20251231.htm)、peer_metrics |
| Coherent、Lumentum | NYSE: COHR／Nasdaq: LITE | 雷射與光偵測器的直接對手，同時也是 MACOM 的模組客戶 | 未找到同口徑 | 未找到 | 光元件龍頭 | 推定 |
| 三菱電機 | 東證 6503 | EML 雷射、GaN HEMT 直接對手 | 未找到 | 未找到 | 日系主要供應商 | 推定 |
| Sumitomo Electric Device Innovations（住友電工子公司） | 東證 5802（母公司） | 光元件與 GaN 直接對手；10-K 點名 | 未找到 | 未找到 | 日系主要供應商 | 10-K |
| 優迅（廈門） | 中國（上市資訊待查） | 低速 TIA 直接對手，高速產品還在送樣 | 未找到；自媒體稱「10G 以下 TIA 全球第二」 | 未找到 | 中國挑戰者 | 【摘要】[搜狐](https://sohu.com/a/1078486942_122944531) |
| Qorvo（HPA 部門） | Nasdaq: QRVO | I&D 與電信直接對手；10-K 點名，Qorvo 的 HPA 也點名 MACOM | HPA 部門 FY2026（至 2026-03）7.057 億，年增 10.7%，含國防、基地台、電源；與 Skyworks 合併，預計 2027 年初完成 | 未找到 | 國防射頻龍頭之一 | [10-K](https://www.sec.gov/Archives/edgar/data/1604778/000162828026032873/rfmd-20260328.htm) |
| Analog Devices | Nasdaq: ADI | I&D 直接對手（微波、混合訊號）；10-K 點名 | 國防營收未揭露；全公司 TTM 138.8 億 | 未找到 | 規模龍頭 | peer_metrics |
| Microchip（Microsemi） | Nasdaq: MCHP | I&D 直接對手；10-K 點名 | 未揭露 | 未找到 | 利基 | 10-K |
| NXP | Nasdaq: NXPI | 電信基地台 RF 功率直接對手；10-K 點名 | 未揭露 | 未找到 | 電信龍頭之一 | 10-K；Yole 列為電信 RF 領先者【摘要，[everythingRF](https://www.everythingrf.com/news/details/20543-yole-group-launches-its-first-status-of-the-rf-industry-report-forecasting-a-70-billion-market-by-2030)】 |
| Skyworks | Nasdaq: SWKS | 少量重疊（主力在手機）；10-K 點名 | 全公司 TTM 40.1 億，年增 0.1% | 未找到 | 落後（成長） | peer_metrics |
| Mini-Circuits | 未上市 | I&D 直接對手（被 Qorvo 10-K 點名） | 未找到 | 未找到 | 利基 | Qorvo 10-K |
| 三安集成、蘇州能訊（Dynax）、Wuatek | 中國 | 電信 GaN 與 LDMOS 直接對手（中國市場） | 未找到 | 未找到 | 中國挑戰者 | 【摘要】Yole（同上） |
| Wolfspeed RF | 已併入 MACOM | 原為 GaN RF 對手，MACOM 已收購 | — | — | — | Wolfspeed 10-K 提到出售 RF 產品線換得 MACOM 股票（本機 sources/MTSI.json） |
| 客戶自研（國防主承包商的自有晶圓廠、模組廠自研） | — | 替代品：10-K 寫「主要和客戶內部設計資源競爭」 | — | — | — | 10-K |
| DSP 內建 driver、LPO／CPO 架構 | — | 替代品或架構轉移：拿掉 DSP 對 driver、TIA 有利；DSP 廠把 driver 整合進 DSP 對獨立 driver 不利 | — | — | — | 【摘要】搜狐 |

- **市佔怎麼推估**：
  - **方法 A：公司自估 SAM**【推估】
    - 分子是 FY2026E 營收 13.23 億美元：Q1 2.716 億、Q2 2.890 億、Q3 3.422 億，加上 Q4 指引中值 4.20 億。
    - 分母是 2026 年 SAM：2027 年 150 億除以 1.2–1.3，得 115–125 億。
    - 全公司約 10.6–11.5%。
    - 分部門看：
      - 資料中心 FY26E 約 5.09 億（FY2025 2.928 億乘上 CEO 說的「FY26 約 +74%」）÷ 46–50 億，約 10–11%。
      - I&D FY26E 約 5.3 億 ÷ 46–50 億，約 10.6–11.5%。I&D 的 Q1 沒揭露，是用「電信 FY26 雙位數成長」反推上限。
      - 電信約 2.8 億 ÷ 23–25 億，約 11–12%。
  - **方法 B：第三方，只算資料中心**【推估】
    - FY2024 資料中心 1.979 億 ÷ LightCounting 2024 晶片組 35 億，約 5.7%。
    - FY2025 2.928 億 ÷ 假設 2025 晶片組 60–70 億，約 4.2–4.9%。60–70 億是我用「PAM4 超過倍增」推的，不是 LightCounting 公布的數字。
    - 口徑偏差有兩個方向：分母含 MACOM 幾乎不賣的 DSP（份額被低估）；分子含雷射、光偵測器、銅纜等化器，這些不在分母裡（份額被高估）。
  - **方法 C：數量法，信心低，不採用**
    - 自媒體稱 800G 模組裡的類比晶片值 8–10 美元，1.6T 值 16–20 美元。這裡的類比晶片包含 TIA、driver、電源、AFE、EEPROM。
    - 數量：800G 2025 年出貨約 1,500 萬只【摘要，轉述 Cignal AI，未證實】；1.6T 從「不到 100 萬」到「約 300 萬」只，來源互相矛盾。
    - 算出高速模組的類比晶片 2025 年只有 2–4 億美元，比 MACOM 自己的資料中心營收 2.93 億還小。所以這組單價或數量至少有一個偏低，或是 MACOM 資料中心營收有很大一塊來自光元件與非模組應用。這裡只列出矛盾。
  - **交叉驗證結論**：全公司對自估 SAM 約 10–12%。資料中心對整個光通訊 IC 市場約 4–6%，對自估 SAM 約 10–11%，**合理區間 4–11%**（看分母）。driver 加 TIA 子市場的份額應該更高，但查不到可靠分母。I&D 和 Yole 的 RF GaN 口徑不同，不換算。

- **龍頭與落後者**：
  - **資料中心**：規模龍頭是 Broadcom、Marvell。Marvell 資料中心 FY2026 61 億，年增 46.5%。自媒體稱兩家 DSP 合計份額超過九成【摘要】。成長最快的是 Credo，FY2026 約 13 億，年增約 198%【推估自 10-K】。純類比與光電業者中，MACOM 資料中心（FY2025 年增 48%，FY26E 約 +74%）和 Semtech Signal Integrity（FY2026 年增 23%，其中資料中心增加 8,140 萬、電信減少 2,000 萬）規模接近，MACOM 成長較快。MaxLinear 基礎建設年增 30%，但全公司 GAAP 營益率 −13.6%，獲利較落後。
  - **國防**：Qorvo HPA FY2026 7.06 億，年增 10.7%，口徑較寬。MACOM I&D FY2025 4.20 億，年增 19.4%；公司說國防 FY2025 成長 19%，FY2026 約 25%【公司說法】。Qorvo 和 Skyworks 合併後，國防射頻的對手規模會更大。
  - **獲利（TTM GAAP 營益率，peer_metrics）**：Broadcom 48.0%、ADI 35.5%、Credo 31.7%、MACOM 18.1%、Marvell 16.5%、Qorvo 13.1%、Semtech 8.0%、Skyworks 7.6%、MaxLinear −13.6%。MACOM 調整後營益率 FY26Q3 是 31.5%，指引 Q4 約 37%【公司說法】。

- **商業模式與客群差異**：
  - **MACOM**
    - 製造：IDM 加外包混合，自有 GaAs、GaN、InP 晶圓廠，Lowell 廠有美國國防部 Trusted Foundry 認證。
    - 客戶：數千種標準品與客製料號，6,000 多家客戶。FY2025 經銷佔 32.3%，兩家轉售商各佔 12.4%、11.2%，前十大客戶佔 57%【證實，10-K】；但前十大「終端客戶」佔比不到 40%（FY26 年初至今）【公司說法】。
    - 誰決定、誰付錢：資料中心元件賣給各地的模組廠（中國、泰國、台灣等），但料號多半由美國雲端業者指定，所以付錢的是模組廠，決定的是雲端業者【公司說法】。
    - 產品壽命：國防與工業料號可賣 5–10 年，部分超過 20 年。
    - 毛利率：GAAP 58.3%（FY26Q3）。
  - **Marvell、Broadcom**：以 DSP 平台加類比晶片組綁售，客戶是模組廠與雲端；Marvell 另有客製 ASIC。毛利率（TTM GAAP）Marvell 52.2%、Broadcom 68.8%。DSP 單價高，議價能力強。
  - **Semtech**：無廠（fabless）類比混合訊號，Signal Integrity 毛利率 65.2%；資料中心與 PON 並重，另有 LoRa 物聯網，是多元化的中型公司。
  - **Credo**：賣 AEC 成品線纜給雲端，前十大客戶約 90%，客戶極度集中，靠系統級產品賺高毛利（TTM 67.1%）。MACOM 走銅纜線性等化器（ACC），兩條是不同路線。
  - **Qorvo HPA**：直接對美國政府、國防主承包商與盟國，賣 RF 元件，也提供化合物半導體代工與封裝服務；同時做基地台與電源。

- **這家公司在地圖上的位置**：MACOM 是三個市場都在第二梯隊、成長正在加速的類比與化合物半導體專家。資料中心是 driver、TIA、光偵測器的主要獨立供應商之一，國防射頻和 Qorvo、ADI 同屬美國本土主要供應商。全公司約佔自估 SAM 的一成。

- **不確定、待查**：
  - 光通訊類比晶片（driver 加 TIA）沒有公開的市場規模和份額，資料中心子市場份額估不準；方法 C 的單價與數量互相矛盾。
  - Broadcom、Marvell 的光元件營收，以及三菱電機、住友 SEDI 的 GaN 與光元件營收，都未揭露或未找到。
  - I&D 和電信的 FY26 Q1 部門營收沒揭露，FY26E 部門數字是反推的。
  - 公司 SAM 四年擴大三倍，以 SAM 當分母的份額會被稀釋，也無法跨年比較。
  - 架構轉移方向不明：LPO、CPO、NPO 對 driver、TIA 是利多還是利空，看 DSP 是否把 driver 整合進去。
  - 法說會提到中國模組廠的監管風險可能讓客戶結構移轉，MACOM 的看法是「跟著業務走」。

---

### LSCC　Lattice Semiconductor

- **市場怎麼定義**：
  - **主要市場**：FPGA（現場可程式邏輯閘陣列）。Lattice 主攻小型（最高約 200K LUT）與中階（150K 到 600K 以上 SLC）、低功耗 FPGA【證實，[10-K FY2025](https://www.sec.gov/Archives/edgar/data/855658/000143774926004100/lscc20260103_10k.htm)】。
  - **營收結構**：FY2025 營收 5.233 億美元，通訊與運算 2.927 億（55.9%）、工業與車用 1.940 億（37.1%）、消費 0.366 億（7.0%）【證實】。2026 年起改成兩大市場，Q2 2026 運算與通訊佔 63%、工業與嵌入式佔 37%【證實，[Q2 2026 新聞稿](https://www.sec.gov/Archives/edgar/data/855658/000143774926025650/ex_971139.htm)】。
  - **重要變化**：2026-07-27 完成收購 AMI，價格 16.5 億美元（約 10 億現金加 6.5 億股票）。AMI 做伺服器韌體與 BMC 管理軟體，CY2026 營收預估超過 2 億【公司說法】。所以 Q3 2026 起 Lattice 不再是純 FPGA 公司，Q3 指引 2.55 億，其中 FPGA 約 2.20 億。
  - **市場規模**：
    - 研究機構估 2025 年 FPGA 市場 84–138 億美元，差距 1.6 倍：MarketsandMarkets 117.3 億、Global Market Insights 138 億、Mordor 99.3 億、Dataintelo 118 億、Trend X 84.3 億【摘要，[MarketsandMarkets](https://www.marketsandmarkets.com/Market-Reports/fpga-market-194123367.html)、[GMI](https://www.gminsights.com/industry-analysis/field-programmable-gate-array-fpga-market-size)、[Mordor](https://www.mordorintelligence.com/industry-reports/field-programmable-gate-array-fpga-market)、[Trend X](https://trendxinsights.com/syndicated-market-research-reports/fpga-market/)】。
    - 主要玩家營收加總只有 53–67 億【推估，見下】。

- **所有玩家**：

| 公司 | 上市地／代號 | 和這家公司的關係（直接對手／替代品） | 相關營收或規模（口徑、期間） | 推估市佔（2025，玩家加總口徑） | 定位 | 來源 |
|---|---|---|---|---|---|---|
| AMD（Xilinx） | Nasdaq: AMD | 直接對手（高階到低階都有，Versal、Spartan、Artix） | Embedded 部門 2025 年 34.54 億，年減 3%，含 x86 嵌入式 CPU；FPGA 推估 24.2–29.4 億（假設佔部門 70–85%）。2026Q2 Embedded 9.77 億，年增 19% | 36–55% | 龍頭 | [AMD 10-K](https://www.sec.gov/Archives/edgar/data/2488/000000248826000018/amd-20251227.htm)、[10-Q Q2 2026](https://www.sec.gov/Archives/edgar/data/2488/000000248826000123/amd-20260627.htm)；Xilinx 被併前 FY2021 營收 31.48 億（[SEC XBRL](https://data.sec.gov/api/xbrl/companyfacts/CIK0000743988.json)） |
| Altera | 未上市（Silver Lake 51%，Intel 2025 年底持股 48%） | 直接對手（Agilex、Cyclone、MAX 10） | 2023 年約 28 億，2024 年 15 億；2025 上半年 8.16 億，毛利率 55%；2025E 16–19 億（推估） | 24–36% | 第二 | [Intel 10-K](https://www.sec.gov/Archives/edgar/data/50863/000005086326000011/intc-20251227.htm)；上半年數字【摘要，[Intel 10-Q Q2 2025](https://www.sec.gov/Archives/edgar/data/50863/000005086325000109/intc-20250628.htm)】 |
| **Lattice** | Nasdaq: LSCC | 本公司 | 2025 年 5.233 億；TTM 至 2026-07 6.511 億，年增 33% | 7.8–9.8% | 小型與低功耗區段的主要玩家，全市場第三 | 10-K、新聞稿 |
| Microchip（PolarFire 等 Flash 型 FPGA） | Nasdaq: MCHP | 直接對手（中低階、國防航太、抗輻射） | 未揭露；放在「其他」產品線（FY2026 10.29 億，含授權、記憶體、代工等）。公司稱 2024 年 FPGA 市佔約 10%，目標 15%，並降價 30% | 5–11%（推估營收 3.5–6 億） | 利基與挑戰者 | 【公司說法】[eeNews Europe 2025-05-20](https://www.eenewseurope.com/en/microchip-slashes-polarfire-fpa-pricing-by-30) |
| 復旦微電 | 上交所 688385／港交所 1385 | 中國直接對手（以高可靠與軍工為主） | FPGA 產品線 2025 年約人民幣 13.16 億（約 1.8 億美元），其中高可靠約 12 億 | 約 3% | 中國利基 | 【摘要】[機構調研紀要](https://www.fxbaogao.com/detail/5332636) |
| 安路科技 | 上交所 688107 | 中國直接對手（中低階） | 2025 年營收約人民幣 5.2 億（約 0.7 億美元），年減 20%；2026Q1 人民幣 1.66 億，年增 77%，資料中心帶動 | 約 1% | 中國挑戰者 | 【摘要】[財聯社](https://www.cls.cn/detail/2360941)、[東方財富](https://finance.eastmoney.com/a/202602283657341595.html) |
| 高雲半導體（Gowin） | 未上市 | 中國直接對手（低階） | 未找到 | 未找到 | 中國挑戰者 | — |
| 紫光同創（Pango） | 未上市（紫光國微 002049 子公司） | 中國直接對手 | 未找到 | 未找到 | 中國挑戰者 | — |
| Efinix | 未上市 | 直接對手（中低階） | 未找到 | 未找到 | 挑戰者 | — |
| QuickLogic | Nasdaq: QUIK | 少量重疊（eFPGA IP） | 未查 | 不到 1%（推定） | 利基 | — |
| ASIC、ASSP、MCU | — | 替代品：10-K 寫依應用可能和 ASIC、ASSP、MCU 競爭 | — | — | — | 10-K |

- **市佔怎麼推估**：
  - **分子**：Lattice 2025 年營收 5.233 億，幾乎全是 FPGA，加少量 IP 授權。
  - **分母 A：玩家加總**【推估】
    - AMD FPGA 24.2–29.4 億。Embedded 部門 34.54 億乘 70–85%；比例是我的假設，依據是 Xilinx 被併前一年營收 31.48 億，以及 Embedded 也含 x86 嵌入式 CPU。
    - Altera 16–19 億：上半年 8.16 億乘 2 是下限，下半年通常較強。
    - Microchip FPGA 3.5–6 億。
    - 復旦微 1.8 億、安路 0.7 億。
    - 高雲、紫光同創、Efinix 等查不到，假設合計 2–5 億。
    - 合計 53–67 億，Lattice 約 **7.8–9.8%**。
  - **分母 B：研究機構**：84–138 億，Lattice 約 **3.8–6.2%**。
  - **交叉驗證**：研究機構的數字比可查證的玩家加總高 25–100%，可能把 FPGA 加速卡、板卡算進去，或口徑不同。差距照列，不挑一個當真。
  - **合理區間 4–10%**，以玩家加總法的 8–10% 為主估，因為它的每一項都對得到財報。

- **龍頭與落後者**：
  - **規模**：AMD 最大，Embedded 2025 年 34.5 億，部門營益率 36.0%（2023 年是 49.4%）。Altera 第二，2023 到 2024 年營收減少 45%，2025 年賣出 51% 給 Silver Lake，整體估值約 87.5 億【摘要，Reuters 轉述】。
  - **週期跌幅**（2023→2024）：Altera −45%、AMD Embedded −33%、Lattice −31%。
  - **2025 年**：Lattice +2.7%、AMD Embedded −2.9%、安路 −20%。
  - **2026 復甦速度**：Lattice Q2 年增 62%，Q3 FPGA 指引約 +65%；AMD Embedded Q2 +19%；安路 Q1 +77%（基期低）。這一波 Lattice 成長最快。
  - **獲利**：Lattice GAAP 毛利率 70.3%，但 GAAP 營益率只有 11%（Q2 2026，含併購與股票報酬費用），非 GAAP 營益率 38%【證實，新聞稿】。
  - **市佔變化**：Microchip 公開說要從 10% 拿到 15%，並降價 30%，是低中階價格競爭的來源。

- **商業模式與客群差異**：
  - **AMD（Xilinx）**：高階 FPGA 與自適應 SoC，先進製程，晶片單價高。客戶是通訊設備、國防航太、量測、ASIC 原型驗證；直銷加經銷。Embedded 部門獲利率高（36%），是 AMD 的穩定現金來源。
  - **Altera**：高階 Agilex 加低階 MAX 10、Cyclone、Agilex 3。私募控股後獨立經營，主攻工業、通訊、國防；Intel 時代的週期下修最深。
  - **Lattice**：小型、低功耗、成熟製程（28nm FD-SOI、16nm）。95% 走經銷，兩大經銷商佔 69%（FY2025），亞洲出貨佔 79%（多半是代工與 ODM 所在地）。策略是「伴隨晶片」：放在 CPU、GPU、BMC 旁邊做控制、開機管理、硬體安全（含後量子密碼）、介面橋接，例如和 ASPEED BMC、TI 雷達合作。AI 伺服器板上這類控制 FPGA 數量增加，是這波主要驅動力；新產品已佔營收超過 25%【公司說法】。
  - **Microchip**：Flash 型 FPGA、抗輻射，國防航太起家；交叉賣給自家 MCU 的 10 萬家客戶，最近用降價搶市佔。
  - **中國廠（安路、高雲、紫光同創、復旦微）**：國產替代，以低中階為主；復旦微以高可靠與軍工為主。

- **這家公司在地圖上的位置**：Lattice 是 FPGA 市場第三大（玩家加總口徑約 8–10%），在小型與低功耗區段是主要玩家。這波 AI 伺服器的控制與安全需求讓它成長領先 AMD、Altera。收購 AMI 後，它會變成「FPGA 加伺服器管理韌體」的組合，地圖要重畫。

- **不確定、待查**：
  - AMD Embedded 裡 FPGA 的比例未揭露，70–85% 是假設。
  - Altera 2025 全年營收未揭露；Microchip 的 FPGA 營收也未揭露。
  - 中國廠商數字都是二手；高雲、紫光同創、Efinix 未找到。
  - 研究機構的市場規模差 1.6 倍，又都高於玩家加總。
  - 小型 FPGA 子市場沒有第三方份額，「低功耗領導者」是公司自述。
  - AMI 的競爭者（其他 BIOS 與 BMC 韌體廠）這次沒研究。

---

### MCHP　Microchip Technology

- **市場怎麼定義**：
  - **營收結構**：Microchip 最大營收來源是 MCU，「mixed-signal microcontrollers」產品線 FY2026（截至 2026-03-31）23.554 億美元，佔 50.0%。類比 13.290 億（28.2%）；其他 10.287 億（21.8%），含 FPGA、授權、記憶體、時脈、代工服務【證實，[10-K FY2026](https://www.sec.gov/Archives/edgar/data/827054/000082705426000016/mchp-20260331.htm)】。
  - **主要市場：全球 MCU**。Omdia 估 2025 年約 221–222 億美元，年減 0.3%；2024 年 223 億【證實，[Infineon 2026-05 簡報引 Omdia](https://www.infineon.com/assets/row/public/documents/corporate/fy2026-q2-web-en.pdf)、[heise](https://www.heise.de/en/news/Europe-s-microcontroller-market-leaders-Infineon-NXP-and-STMicroelectronics-11247952.html)】。
  - **次要市場：類比 IC**。WSTS 估 2025 年 865 億美元，年增 8.7%；2026 年預估 954 億，+10.2%。2022–2024 年依序是 890、812、796 億【證實，[WSTS 2026-06（JEITA 版）](https://www.jeita.or.jp/japanese/stat/wsts/docs/20260602WSTS.pdf)】。

- **所有玩家**（MCU；類比另列兩行）：

| 公司 | 上市地／代號 | 和這家公司的關係（直接對手／替代品） | 相關營收或規模（口徑、期間） | 推估市佔 | 定位 | 來源 |
|---|---|---|---|---|---|---|
| Infineon | 法蘭克福 IFX | MCU 直接對手（AURIX 車用、PSoC，併購 Cypress） | MCU 2025 年約 51.5 億（23.2% 乘 222 億） | 2025 年 23.2%（2024 年 21.4%）【證實，Omdia】 | 龍頭，2025 年份額增加最多（+1.8pp） | Infineon 簡報、heise |
| NXP | Nasdaq: NXPI | MCU 直接對手（S32 車用、i.MX RT、LPC） | 約 43.1 億 | 19.4%（2024 年 20.0%） | 第二 | Infineon 簡報 |
| Renesas | 東證 6723 | MCU 直接對手（RH850 車用、RA、RX） | 約 34.6 億 | 15.6%（2024 年 16.0%） | 第三 | 同上 |
| STMicroelectronics | 紐約與巴黎：STM | MCU 直接對手（STM32 通用 MCU） | 約 28.9 億 | 13.0%（2024 年 13.7%） | 第四 | 同上 |
| **Microchip** | Nasdaq: MCHP | 本公司 | Omdia 口徑約 16.7 億；自報 MCU 產品線 FY2026 23.554 億 | 2025 年 7.5%（2024 年 8.4%）【證實，Omdia】；自報口徑 10.6%【推估】 | 第五，份額下滑 | 同上、10-K |
| Texas Instruments | Nasdaq: TXN | MCU 對手（Embedded Processing，含處理器）；類比龍頭 | Embedded Processing 2025 年 26.97 億，營益率 11%；MCU 未單獨揭露 | 不在前五 | MCU 追趕者，類比龍頭 | [TI 10-K](https://www.sec.gov/Archives/edgar/data/97476/000009747626000059/txn-20251231.htm) |
| Silicon Labs | Nasdaq: SLAB | 無線 MCU 與 SoC 直接對手；10-K 反向點名 Microchip | 全公司 TTM 8.56 億，年增 21.7% | 不到 4%（推定） | 利基（物聯網無線） | peer_metrics、本機 sources/MCHP.json |
| 新唐、兆易創新、樂鑫、Nordic、羅姆、東芝、三星等 | 台灣 4919／上交所 603986／上交所 688018／奧斯陸 NOD／東證 6963／東芝已下市／韓國 005930 | MCU 直接對手（含中國低價 Arm 與 RISC-V） | 個別未找到；前五以外合計約 21%，約 47 億 | 合計約 21% | 挑戰者與利基 | Omdia（推算） |
| 仿冒與複製晶片 | 中國、台灣 | 10-K 寫有公司複製或逆向工程其產品線 | — | — | — | 10-K |
| FPGA、MPU、ASIC | — | 替代品（高階控制應用） | — | — | — | 推定 |
| 類比：TI | Nasdaq: TXN | 類比直接對手 | 類比部門 2025 年 140.06 億 | 類比市場 16.2%【推估，÷ WSTS 865 億】 | 類比龍頭 | TI 10-K |
| 類比：ADI | Nasdaq: ADI | 類比直接對手 | 全公司 TTM 138.8 億（至 2026-08） | 約 16%【推估，期間不一致】 | 類比龍頭之一 | peer_metrics |
| （類比：Microchip） | — | 本公司 | 類比產品線 FY2026 13.29 億 | 約 1.5%【推估】 | 利基 | 10-K |

- **市佔怎麼推估**：
  - **主數字**：直接採用研究機構 Omdia，Microchip 2025 年 7.5%、2024 年 8.4%，排第五【證實】。
  - **交叉驗證 1：自報產品線**【推估】
    - Microchip 自報 MCU 產品線 FY2026 23.554 億 ÷ Omdia 222 億 = 10.6%。
    - Omdia 對 Microchip 的 MCU 估值約 16.7 億，只有自報產品線的 71%；2024 年是 83%（18.7 億對 22.50 億）。
    - 差距可能來自三點：自報產品線含 MPU（32 位元以上處理器）和開發工具；Microchip 財年是 4 月到 3 月，和日曆年錯位；Omdia 的估算模型。
  - **交叉驗證 2：不同研究機構、不同年份**
    - IC Insights 2021 年資料：MCU 市場 202 億，Microchip 排第二，前五名是 NXP、Microchip、Renesas、ST、Infineon，合計 82.1%【證實，[Leuze 轉述 IC Insights](https://www.leuze-verlag.de/en/news-electronics-production/three-mcu-providers-hold-82-market-share)】。
    - 依文中差額描述反推 Microchip 約 17–18%【推估】。
    - 兩家機構方法不同，不能直接相減；但方向一致：Microchip 從第二掉到第五，Infineon 從第五升到第一。
  - **合理區間**：2025 年 7.5–10.6%（Omdia 口徑到自報口徑）。

- **龍頭與落後者**：
  - **份額**：Infineon 2025 年 23.2%，是前五名中唯一增加的，+1.8pp。NXP −0.6、ST −0.7、Renesas −0.4、Microchip −0.9pp，Microchip 降幅最大。
  - **規模起伏**：Microchip 營收從 FY2023 高峰 84.39 億掉到 FY2025 44.02 億，−48%。MCU 產品線從 FY2024 42.72 億掉到 FY2025 22.50 億，−47%。同期整個類比市場從高峰到谷底只跌約 11%（2022 年 890 億到 2024 年 796 億，WSTS）。Microchip 的跌幅遠大於市場。
  - **獲利（TTM GAAP 營益率，peer_metrics）**：Microchip 15.5%，TI 37.3%、ADI 35.5%、NXP 32.0%、onsemi 10.8%。Microchip 的非 GAAP 營益率 FY27Q1 已回到 35.1%【公司說法】。

- **這波是庫存循環修復，證據如下**：
  - **通路庫存**：經銷商持有天數從 33 天（2025-03）降到 26 天（2026-03），十年區間是 17–43 天。10-K 直接寫經銷商的庫存調整「對 FY2025 與 FY2026 上半年營收有重大不利影響」【證實】。
  - **自家庫存**：天數從 185 天（2026-03-31）降到 175 天（2026-06-30）【證實，[FY27Q1 新聞稿](https://www.sec.gov/Archives/edgar/data/827054/000082705426000037/exhibit991q1fy27.htm)】。
  - **營收反彈**：FY27Q1（至 2026-06）營收 14.85 億，年增 38.0%；Q2 指引 15.89–16.18 億，中值年增約 40.6%。
  - **毛利率**：非 GAAP 毛利率 63.8%，Q2 指引 66–67%。公司說來自工廠稼動率提升、低稼動費用減少【公司說法】。
  - **市場背景**：WSTS 類比市場 2023 年 −8.7%、2024 年 −2.0%、2025 年 +8.7%、2026F +10.2%；Omdia MCU 市場 2025 年 −0.3%。
  - **結論**：營收反彈主要來自客戶與通路停止去庫存、開始回補。TTM 營收 51.2 億，仍只有高峰的約六成。2025 年 Omdia 份額還在掉，2026 年的反彈能不能拿回份額，要等 2026 年的排名。

- **商業模式與客群差異**：
  - **Microchip**
    - 客戶：約 10.1 萬家，長尾。經銷佔 47%，最大經銷商 Arrow 佔 12%（FY2026）；海外銷售約 75%。
    - 產品：8、16、32 位元自有架構（PIC、AVR）加 Arm，以「Total System Solution」把 MCU、類比、FPGA、記憶體綁售。
    - 定價：自有架構產品的平均售價相對穩定【證實，10-K】。
    - 製造：有自有晶圓廠，Tempe 的 Fab 2 正評估出售。
    - 毛利率：FY27Q1 GAAP 63.2%、非 GAAP 63.8%。
    - 客群：工業、車用、國防航太、消費、資料中心都有，偏中小客戶與長尾設計。
  - **Infineon**：車用 MCU 龍頭（AURIX），功率半導體也是第一，和車廠、Tier 1 直接合作；車用加功率的綁定度高，2025 年逆勢拿份額。
  - **NXP**：車用（S32）加工業與物聯網（i.MX RT），以 Arm 為主，大客戶直銷比重高。
  - **Renesas**：日系車廠核心 MCU 供應商（RH850），加上工業 RA、RX 系列。
  - **STMicroelectronics**：STM32 是通用 MCU 主力，經銷長尾強，2023 年曾是 Cohu 的第一大客戶（見 COHU 節）；和華虹合作在中國本地生產 MCU【證實，heise】。
  - **TI**：類比龍頭，自有 300mm 晶圓廠，以 ti.com 直銷為主。MCU 放在 Embedded Processing，2025 年營益率只有 11%，類比部門是 38.6%。

- **這家公司在地圖上的位置**：Microchip 是全球 MCU 第五大（Omdia 2025 年 7.5%），2021 年曾經是第二（IC Insights）。類比市場只佔約 1.5%。目前是庫存循環修復帶動的營收反彈，2025 年份額還在流失。

- **不確定、待查**：
  - Omdia 和 IC Insights 口徑不同；Omdia 對 Microchip 的估值只有自報 MCU 產品線的 71–83%。
  - 2026 年 MCU 排名要到 2027 年 3 月才會公布，反彈期有沒有收復份額目前無法驗證。
  - 中國 MCU 廠商的合計份額與成長未找到。
  - TI 的 MCU 營收未揭露。
  - Fab 2 出售對成本結構的影響待觀察。

---

### COHU　Cohu

- **市場怎麼定義**：
  - **業務範圍**：Cohu 做半導體後段（封裝後最終測試）的設備與耗材，包括分選機（test handler 或 test automation，含主動溫控 ATC）、測試介面（contactor、probe pin、power probe card）、少量 ATE 測試機、封裝檢測與量測、軟體分析。
  - **部門與營收**：三個營運部門（Test Handler、Semiconductor Tester、Interface Solutions）合併成一個報告部門。FY2025 營收 4.530 億美元：系統 1.806 億（40%）、經常性收入 2.723 億（60%，含介面、備品、套件、服務、軟體）【證實，[10-K FY2025](https://www.sec.gov/Archives/edgar/data/21535/000143774926004339/cohu20251227_10k.htm)】。
  - **公司自估 SAM**：約 30 億美元【公司說法，10-K】。
  - **市場規模**（分子市場）：
    - **測試設備整體**：SEMI 2026 年預估 153 億美元、+31.0%；2025 年 +55.3%，回推 2025 年約 117 億【推估自 [SEMI 2026-07](https://www.webull.com/news/15226022544172032)】。
    - **測試機（ATE）**：Advantest 估 CY2025 測試機市場 90 億，其中 SoC 69 億、記憶體 21 億；CY2024 是 60 億【公司說法，[Advantest 2026 股東會簡報](https://www.advantest.com/document/en/investors/shares-and-corporate-bonds/meeting/AGM_presentation_20260731_en.pdf)】。
    - **分選機**：研究機構估 2025 年 27.8 億，方法不明【摘要，[Intel Market Research](https://www.intelmarketresearch.com/test-handler-market-208)】；用 SEMI 測試設備減 Advantest 測試機，得約 27 億，但這裡面也含探針台、燒機等設備【推估，口徑不一】。
    - **測試座與接觸器**：未找到。

- **所有玩家**：

| 公司 | 上市地／代號 | 和這家公司的關係（直接對手／替代品） | 相關營收或規模（口徑、期間） | 推估市佔 | 定位 | 來源 |
|---|---|---|---|---|---|---|
| **Cohu** | Nasdaq: COHU | 本公司 | FY2025 4.530 億，年增 12.7%；TTM 至 2026-06 5.226 億，年增 32.7%；FY26 HPC 營收預估 1.0–1.1 億 | 分選機 4–10%；ATE 不超過 2%；自估 SAM 15% | 分選機加介面的中型專業廠 | 10-K、[Q2 2026 新聞稿](https://www.sec.gov/Archives/edgar/data/21535/000143774926025053/ex_994647.htm) |
| Advantest | 東證 6857 | ATE 龍頭；也賣分選機與 device interface；10-K 點名 | FY2025（至 2026-03）營收 1兆1,286 億日圓（約 74–77 億美元），年增 44.7%，營益率 44%；Test System 部門 1兆194 億日圓。舊口徑 Mechatronics（分選機加 device interface）FY2024 約 732 億日圓（約 4.8 億美元） | ATE 65%（CY2025；SoC 66%、記憶體 61%）【公司說法】；分選機 9–18%【推估】 | ATE 龍頭 | [FY2025 決算](https://www.advantest.com/news/2026/a81o6o0000000hgw-att/E_FR_FY2025_FN.pdf)、[FY2024 說明](https://www.advantest.com/document/en/investors/ir-library/result/E_BIZ_250425_note.pdf)、股東會簡報 |
| Teradyne | Nasdaq: TER | ATE 直接對手（SoC、記憶體、SLT），也反向點名 Cohu | Semiconductor Test 2025 年 25.24 億，年增 18.8%；2026Q2 約 11.22 億，年增 128% | ATE 約 22–26%【推估：扣掉 IST 後 20–23 億 ÷ 90 億】 | ATE 第二 | [10-K](https://www.sec.gov/Archives/edgar/data/97210/000119312526059002/ter-20251231.htm)、[10-Q Q2 2026](https://www.sec.gov/Archives/edgar/data/97210/000119312526327715/ter-20260628.htm) |
| 鴻勁精密（Hon Precision） | 台灣證交所 7769（2025-11-27 上市） | 分選機與 ATC 直接對手；Cohu 10-K 點名 | 2025 年營收新台幣 302.7 億（約 9.3–9.8 億美元），年增 166%；毛利率 56.5%（另一報導寫 55.0%）；稅後淨利 123.6 億；2025Q3 營收中分選機 42%、主動溫控 33%、水冷板 23%；AI 與 HPC 佔訂單約 72–80% | 分選機加 ATC 約 25–35%【推估：分選機加 ATC 約 7 億 ÷ 20–28 億】 | 分選機營收龍頭（推估），成長最快 | [富果法說摘要](https://blog.fugle.tw/post/earnings-call-7769-2026-03-12)、[旺得富](https://wantrich.chinatimes.com/news/20260311900421-420101)、[旺得富 2025-10](https://wantrich.chinatimes.com/news/20251027900460-420101)、[理財寶](https://uanalyze.com.tw/articles/8844238333) |
| 致茂電子（Chroma） | 台灣證交所 2360 | SLT 與分選、測試設備對手 | 未找到 | 未找到 | 挑戰者 | 推定 |
| Techwing、長川科技、上野精機等「其他亞洲廠」 | 韓國 089030／深交所 300604／日本 | 分選機對手（Cohu 10-K 寫 other Asia-based manufacturers） | 未找到 | 未找到 | 挑戰者 | 10-K（泛稱） |
| 華峰測控、長川科技 | 上交所 688200／深交所 300604 | 中國低階 ATE 對手（Advantest 稱中國業者壓低其低階 SoC 份額） | 未找到 | 未找到 | 中國挑戰者 | Advantest FY2024 說明 |
| SPEA | 未上市（義大利） | ATE 對手（被 Teradyne 點名） | 未找到 | 未找到 | 利基 | Teradyne 10-K |
| 穎崴（WinWay） | 台灣 6515 | 測試座與介面直接對手（AI、HPC） | 2025 年營收新台幣 78.57 億（約 2.4–2.5 億美元），年增 35.5% | 未找到分母 | 介面挑戰者 | 【摘要】[理財寶](https://uanalyze.com.tw/articles/4425644353) |
| Leeno、ISC、Smiths Interconnect、Johnstech、Yamaichi、Enplas | 韓國 058470／韓國 095340／倫敦 SMIN（部門）／未上市／東證 6941／東證 6961 | 測試座與接觸器直接對手 | 未找到（本次搜尋額度用盡） | 未找到 | — | 推定 |
| FormFactor | Nasdaq: FORM | 相鄰（晶圓測試探針卡），和 Cohu 的 power probe card 重疊 | TTM 9.02 億，年增 18% | — | 探針卡龍頭之一 | peer_metrics |
| KLA（及 Camtek、Onto） | Nasdaq: KLAC 等 | 檢測與量測對手；Cohu 10-K 點名 KLA | KLA 全公司 TTM 135.8 億；後段檢測部分未揭露 | — | 檢測龍頭 | peer_metrics、10-K |
| 系統級測試（SLT）、內建自我測試 | — | 部分替代：測試內容往 SLT 移；Teradyne IST、Advantest、鴻勁都有 SLT | — | — | — | Teradyne 10-K、鴻勁法說 |

- **市佔怎麼推估**：
  - **ATE**【推估】：Cohu 沒揭露測試機營收，但它一定小於整個系統營收 1.806 億，所以份額上限是 1.806 ÷ 90 = **2.0%**，實際應該更低。Advantest 65% 是公司自估；Teradyne 22–26% 是我的推估，用 Semiconductor Test 25.24 億扣掉 SLT、HDD 等 IST 業務（假設 10–20%）。剩下 10–13% 由中國廠、SPEA、Cohu、致茂分。
  - **分選機**【推估，信心低】
    - 分子：Cohu 分選機系統假設佔系統營收 55–75%，約 0.99–1.35 億；分選機套件與備品在經常性收入裡，另外再加幾個百分點。
    - 分母：20–28 億。上限用研究機構的 27.8 億，SEMI 減 Advantest 的約 27 億也在附近；下限是我考慮其中含探針台等設備後的判斷。
    - Cohu 約 **4–10%**。同口徑下，鴻勁的分選機加 ATC 約 7 億，佔 25–35%；Advantest 分選機假設 2.5–3.5 億，佔 9–18%。
    - 歷史對照：2000 年 VLSI Research 資料中，Cohu 的 Delta Design 是美國最大、全球第二大分選設備商【證實，[Cohu 2001 年 10-K405](https://www.sec.gov/Archives/edgar/data/21535/000093639202000182/a79538e10-k405.htm)】。
  - **測試介面**：查不到市場規模。Cohu 經常性收入 2.72 億是它介面營收的上限，和穎崴（約 2.4–2.5 億）同一量級。
  - **整體**：Cohu 4.53 億 ÷ 自估 SAM 30 億 = 15%【推估】；系統營收 1.806 億 ÷ SEMI 測試設備約 117 億 = 1.5%。

- **龍頭與落後者**：
  - **ATE**：Advantest 是龍頭，FY2025 營收年增 44.7%，營益率 44%，FY2026Q1 再年增 39%；SoC 份額 CY2024 到 CY2025 從 56% 升到 66%。Teradyne 第二，Semiconductor Test 2025 年 +18.8%、2026Q2 +128%，TTM GAAP 營益率 30.2%。
  - **分選機**：鴻勁 2025 年營收年增 166%、毛利率約 56%、淨利率約 41%【推估：123.6 ÷ 302.7】，規模約是 Cohu 的兩倍。
  - **Cohu**：營收從 2021 年高峰 8.872 億掉到 2024 年 4.018 億，−55%；2025 年 +12.7%，TTM +32.7%。毛利率 44%，GAAP 營益率 −6.9%（peer_metrics），是這組中規模最小、獲利最弱的；但 TTM 營益率改善了 13.9pp。

- **商業模式與客群差異**：
  - **Advantest 與 Teradyne：AI 晶片的 SoC 與記憶體測試機**
    - 賣的是高單價測試機，需求來自 AI GPU、ASIC、HBM。
    - 誰決定、誰付錢：Teradyne 10-K 寫，通常是「指定客戶」（OEM、IDM、fabless）選平台，「採購客戶」（封測廠等）下單【證實】。所以真正的決策者是 AI 晶片設計公司與雲端業者。
    - 對成熟製程的態度：Advantest 自己寫「車用、工業等成熟半導體的測試機需求仍疲弱」【證實，FY2025 決算】。
    - 獲利：營益率 30–44%。
  - **Cohu：分選機加耗材型接觸器，車用、工業、手機類比為主**
    - 客戶：IDM 與封測廠。STMicroelectronics 2023 年佔 Cohu 營收 12.0%【證實，10-K】；前十大客戶佔 60%；裝機量超過 25,000 台，分布在 108 家客戶、280 多座工廠。
    - 收入結構：經常性收入佔 53–60%，跟著測試量（測試機台稼動率，2026-06 約 80%）走；系統營收跟著客戶的資本支出走。
    - 週期：車用與工業的系統銷售 2023 年 −24%、2024 年 −65%、2025 年 +45%；手機 2023 年 −54%、2024 年 −10%、2025 年 −17%【證實，10-K】。
    - AI 曝險：Eclipse 分選機搭配 T-Core 主動溫控切入 AI 處理器，FY26 HPC 營收預估 1.0–1.1 億，約佔 TTM 營收的兩成【公司說法】。
    - 毛利率約 44–45%，低於 ATE 龍頭。測試機由 Jabil 在馬來西亞代工【證實，10-K】。
  - **鴻勁：專攻 AI 晶片的最終測試與 SLT 分選機，加液冷主動溫控**
    - AI 與 HPC 佔訂單約 72–80%；終端客戶美系約 57%、中國約 21%；毛利率目標 55–60%【公司說法】。
    - 和 Cohu 的差別在於客群幾乎全是 AI 高功耗晶片，散熱能力是主要賣點，所以這波 AI 拉貨幾乎全部受惠。

- **這家公司在地圖上的位置**：
  - Cohu 是「分選機加測試介面」的中型專業廠，在 ATE 只是不到 2% 的利基。
  - 分選機按營收推估排在鴻勁、Advantest 之後，約第三（推估）。
  - 產品曝險偏車用、工業、手機，這些客戶正在去化庫存後回補；AI 曝險在增加（約兩成），但比鴻勁小很多。

- **不確定、待查**：
  - Cohu 沒揭露分選機、介面、測試機、檢測各自的營收，分選機份額 4–10% 的分子是假設。
  - 分選機市場規模沒有可靠的第三方數字；測試座與接觸器市場規模未找到。
  - Leeno、ISC、致茂、Techwing、長川的營收，這次搜尋額度用盡，沒查到。
  - Advantest 分選機營收在新部門口徑下已不揭露；FY2024 的 732 億日圓是從簡報圖表讀出，且含 device interface。
  - 鴻勁毛利率兩個來源不一致（56.54% 對 55.03%）。
  - Cohu 投資人簡報（ir.cohu.com）被拒絕存取。搜尋摘要轉述其自估 SAM：AI xPU 分選約 6.5 億、HBM 檢測約 1 億【摘要】，未能核對原文。

---

## 研究過程紀錄

**步驟**
1. 讀本機資料：cards.md 四張卡、sources/*.json 的 10-K 競爭段落、peer_metrics.jsonl、四份最新財報新聞稿。新聞稿只有 MACOM 沒有分部門數字，要另外找法說逐字稿。
2. 用 curl 從 SEC 抓 15 份年報與季報，轉成純文字後 grep：四家公司本身，加上 Semtech、Qorvo、Credo、Marvell、MaxLinear、Teradyne、AMD、TI、Intel、AMD 10-Q、Teradyne 10-Q、Cohu 10-Q、Cohu 2001 年 10-K405。另用 SEC XBRL API 拉季度與年度營收，用來驗證 TTM 與回推單季。
3. 用 WebSearch 找第三方市場規模與市佔，共約 29 次，最後一次被擋。再用 curl 直接下載原始文件核對，包括 Infineon 簡報 PDF、WSTS PDF、Advantest 決算、法說說明與股東會 PDF、LightCounting 新聞頁、SEMI 新聞稿轉載、MACOM FY22 簡報、鴻勁法說摘要等。
4. 計算市佔，每家至少兩種分母（公司 SAM、研究機構、玩家加總），並列出區間。

**最有用的來源**
- 公司在法說或股東會自己公布的市場規模與份額，雖然是公司說法，但有口徑：Advantest 測試機市場與份額（CY2024、CY2025），MACOM 2027 年 SAM 的三段拆分。
- Infineon 投資人簡報引用的 Omdia MCU 前五名份額，2024 與 2025 年都有，最乾淨。
- SEC 10-K 的部門營收：Semtech Signal Integrity、Qorvo HPA、AMD Embedded、Intel 揭露的 Altera、TI 部門。

**查不到或互相矛盾的資料**
- 光通訊 driver 與 TIA 子市場規模沒有公開數字；自媒體的單價乘數量算出來比 MACOM 自己的營收還小，互相矛盾。
- 1.6T 光模組 2025 年出貨量，不到 100 萬只和約 300 萬只兩種說法都有。
- FPGA 市場研究機構的數字從 84 億到 138 億，都比玩家加總（53–67 億）高。
- Omdia 2025 年 MCU 市場，新聞稿寫 221 億、簡報寫 222 億；Infineon 2024 年份額，2025-03 新聞稿寫 21.3%，後來改成 21.4%。
- Advantest FY2025 營收，搜尋摘要寫 1兆1,718 億日圓，決算原文是 1兆1,286 億，以原文為準。
- 鴻勁 2025 年毛利率 56.54% 和 55.03% 兩種說法。
- 查不到：Altera 2025 全年營收、Microchip FPGA 營收、高雲、紫光同創、Efinix、Leeno、ISC、致茂、Techwing、長川、三菱電機與住友 SEDI 的相關營收、測試座市場規模。

**工具問題（照實寫）**
- WebFetch 對每個網域都回 DNS 錯誤（ENOTFOUND），所以全部改用 Bash curl 加自寫的 HTML 轉文字小程式；只有 sec.gov 帶指定的 User-Agent。
- ir.cohu.com 回 Access Denied，Cohu 投資人簡報讀不到。
- 第 29 次 WebSearch 時被告知「本輪搜尋額度已用完（與其他研究員共用 200 次上限）」，之後只抓已知網址的原始文件，沒有再搜尋。測試座的對手數字因此缺。
- 大約做了 29 次搜尋（1 次被擋）、3 次 WebFetch（全部失敗）、約 30 次 curl 抓網頁與 PDF、15 份 SEC 文件、4 次 XBRL API 查詢。

**既有卡片的錯誤或缺漏**
1. **MCHP 卡**的「市占推估：在 TI、ADI、NXP、onsemi、Microchip 五家裡約 9%」，分母混了類比龍頭和 NXP，不是 MCU 市佔。Omdia 的正確口徑是 2025 年 7.5%、排第五。卡片把 Infineon、ST、Renesas 標成「資料缺」，但它們正是 MCU 前四名中的三家。
2. **LSCC 卡**寫 Altera「沒有財報」不精確：Intel 10-K 有揭露 Altera 2023 年約 28 億、2024 年 15 億，Q2 2025 季報有上半年 8.16 億。2025-09-12 之後 Intel 不再合併 Altera；交割時保留 49%，2025 年底 10-K 寫的是 48%。卡片沒提 2026-07-27 完成的 AMI 收購（16.5 億），以及 2026 年起終端市場改成兩類。
3. **COHU 卡**只把 Advantest、Teradyne 當龍頭。但在 Cohu 的本業分選機，鴻勁 2025 年營收（約 9.5 億美元）已是 Cohu 的兩倍，應該補上。卡片判斷「應偏產業同步」，我同意：Advantest FY2025 +45%、Teradyne 2026Q2 半導體測試 +128%、鴻勁 +166%。
4. **MTSI 卡**的「市占推估：不適用」可以改成用公司自估 SAM（約 10–11%）加 LightCounting 交叉驗證（資料中心 4–6%）。卡片的對手清單少了三菱電機、Coherent、Lumentum（雷射與光偵測器）、中國業者，也沒提 Qorvo 和 Skyworks 合併中、Wolfspeed RF 已被 MACOM 收購。
