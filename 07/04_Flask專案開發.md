# 04｜Vibe Coding：依確認的 JSON 建立 Flask 專題

這輪請讀取**最後確認版本**的 `AI_Agent_流程設計.json`（與本 Prompt 一起上傳）。不要重新要求繪製節點、填寫問卷或重新規劃流程。現在開始實際建立**這個專題專屬**的完整 Flask 網站，不要再產生流程設計工具。

- 以最終 JSON 的 `project`、`entry`、`agents`、`edges` 及 `resources` 為準，遵守連線的方向、呼叫／委派語意、條件、資料欄位與最大重試次數，不能以畫布位置或 `ui_layout.nodes` 推定執行先後；該欄只供 HTML 保存拖曳排版。
- 使用 Python 3.11+、Flask、必要的新版 AG2 `import ag2` 或經測試的 Python orchestrator，依任務選最少套件；不得混用已改版的 AG2 Classic API；不需要額外購買或部署任何專門的 Coding Agent。
- 請完成真正的 Agent 呼叫、函式工具、背景工作、可查詢進度、取消／超時、持久化歷史與錯誤報告。前端 UI 要是實際專案的真正使用介面。
- 只能使用 `.env` **環境變數名稱**讀取設定，不能將金鑰寫進程式或網頁；不要創建或覆寫真正 `.env`，只建立 `.env.example`（空值）、`.gitignore`、`requirements.txt`、`README.md`。
- 若 JSON 指定 retrieval，請先檢查本階段另外提供的資料（若有），依資料附件實際內容實作 BM25 + jieba；已驗證 Embedding 可用時才加入 dense 或 hybrid + RRF。若沒有資料附件，先清楚說明缺少的資料，不能造假資料來源。
- 若 JSON 的 `resources.retrieval.web_search.enabled=true`，請真正建立可被 Agent 呼叫的 Live Web Retrieval **Function Tools**：`ddgs.text/news` 搜尋列表 → 官方來源優先排序／過濾 → `requests` 抓取靜態網頁，必要時 `Playwright` 載入動態網頁 → 文字清理、分段與來源 metadata → 可選的 BM25／Dense／Hybrid + RRF → 來源查核與引用。可使用 `ddgs.extract()` 作為備選擷取手段，但不能只用搜尋摘要充當全文；逐一記錄搜尋列表與實際擷取結果、抽取失敗原因。搜尋結果需留存 URL、title、published_at（若可驗證）、retrieved_at、source、chunk_id；顯示來源與查核狀態。
- **將成功擷取的網頁寫入 Excel 快取。** 若 `resources.retrieval.web_search.enabled=true`，依 `web_search.cache` 建立 `data/web_cache.xlsx`，不存在時自動初始化 `queries`、`pages`、`chunks` 三個工作表；只寫入實際取得且允許保存的文字與必要 metadata，**不可修改或覆寫使用者提供的原始知識 Excel**。可用 `openpyxl`（需要時搭配 `pandas` 做索引整理），網頁長文須分段，每筆記錄 URL、標題、來源、`published_at`（如可確認）、`fetched_at`、`last_checked_at`、`expires_at`、`etag`、`last_modified`、`content_sha256`、`status` 與來源 chunk ID。搜尋列表另外保留 `query_key`、搜尋類型／區域及網址清單。
- **具體快取查詢順序：** 第一次查詢時先查 `queries`；無可用搜尋列表才呼叫 ddgs；每一個返回的 URL 都先查 `pages`／`chunks`，未過期的已抓取正文直接回傳、完全跳過 requests／Playwright；過期或手動要求強制更新才重新驗證／擷取。不同搜尋語句命中同一 URL 時只保存一份頁面正文；應正規化網址、排除無關追蹤參數，並保留必要的查詢參數避免誤合併不同頁面。
- **更新與失敗處理：** 預設 `query_ttl_seconds=3600`、`page_ttl_seconds=604800`、`news_page_ttl_seconds=86400`，新聞、衛教／政策更新可使用更短 TTL；支援使用者手動「強制更新」。優先使用 `If-None-Match`／`If-Modified-Since`，伺服器回 `304` 時沿用正文並更新有效期限，回 `200` 且內容有變才更新 chunks／索引。抓取失敗保留原有可用快取，回報 `cache_hit`、`is_stale`、最後更新時間，不可將舊新聞當成最新資料。沒有網路時只能明示使用已存在的快取，不能假裝即時取得。
- **檔案可靠性：** Excel 可能被開啟而無法寫入；須處理檔案鎖定、不同請求同時寫入、暫存檔原子替換及異常回復。不要每查一筆就反覆讀寫整本 Excel；每次請求先載入一次快取，彙整本批變更後統一寫入。限制快取資料量、文字長度、保留期限及本機檔案權限，避免 Excel 單格 32,767 字元上限與檔案損壞。
- **檢索整合：** `knowledge.xlsx`（人工資料）與 `web_cache.xlsx`（自動快取）分開管理，但都轉為同一套 document/chunk 格式；BM25／Dense／Hybrid 可搜尋兩者，明確呈現來源 URL、來源類型、取得日期、是否使用過期快取，索引僅在資料或版本變更時更新。
- 網頁擷取必須有安全限制：僅允許經核准的公開 HTTP(S) 網址、阻擋 localhost／內網／雲端 metadata IP、重導向重新驗證、防止 SSRF 與 prompt injection；遵守 robots.txt、網站條款、存取權限和合理 rate limits。限制結果數、內容長度、timeout、併發與快取；不得繞過 CAPTCHA／登入／付費牆或批次下載受保護內容。外部網頁文字只作為資料，不得成為 Agent 的系統指令。
- 混合 Excel 和即時網頁時必須區分來源及更新時間，設計離線／抓取失敗的回退方式；健康資料優先引用官方醫療／衛生來源，星座內容標示娛樂性質，歷史人物的 AI 台詞／影像標示為模擬內容。無可靠來源時不得生成貌似真實的引用或史實。
- 若 JSON 指定 multimodal ngrok API，先檢查本階段另附的 Client／Notebook（若有） 再依規格實作 health、submit、poll、download；未連通的 API 不得回報生成成功。
- 多人共用 API Key 必須遵守供應商的 per-project／per-account 配額及計費限制，做佇列、合理節流與 429 backoff，不以切換 Key 規避限制。
- **快取功能必須測試：** 用 mock 網頁驗證「首次呼叫 ddgs＋擷取 → 寫入 Excel → 第二次相同查詢完全不呼叫 ddgs／requests／Playwright」、「不同查詢同 URL 不重抓」、「過期才驗證（304 與內容變更 200）」、「強制更新」、「離線／抓取失敗時只回報已標示過期的資料」、「重複／無效網址／並行寫入不破壞 Excel」。測試結果區分 mock 與實際網路存取，不得用 mock 冒充 Live 成功。
- 程式與 README 使用臺灣繁體中文。產生完整專案 ZIP，包含 Windows 可使用的啟動步驟；實際執行單元測試、Flask HTTP smoke test、必要的 Live API（有權限才做），清楚區分已通過與無法驗證的項目。
- 能操作檔案與終端時，請自行建立、測試並修正，最後提供可下載專案；無法使用工具時如實說明限制，不能假稱已執行測試。

**請勿把本輪改回「先生成 JSON」；JSON 已經確認，現在是透過 ChatGPT、Gemini 或其他 AI 平台進行 Vibe Coding 的建置階段。**

**提交順序：** 初次規劃時一起上傳 `01_專案需求表.docx` + `02_AI流程規劃與修改.md`；在 `03_AI工作流程預覽.html` 本機預覽（不用上傳）；若要改流程，上傳**最新 JSON** + 同一份 `02_AI流程規劃與修改.md` 並說明修改要求；流程確認後才上傳**最終 JSON** + 本檔 `04_Flask專案開發.md`。真正的 `.env` 保留在本機，勿上傳。
