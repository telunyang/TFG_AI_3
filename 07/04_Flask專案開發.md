# 04｜Vibe Coding：依確認的 JSON 建立 Flask 專題

這輪請讀取**最後確認版本**的 `AI_Agent_流程設計.json`（與本 Prompt 一起上傳）。不要重新要求繪製節點、填寫問卷或重新規劃流程。現在開始實際建立**這個專題專屬**的完整 Flask 網站，不要再產生流程設計工具。

- 以最終 JSON 的 `project`、`entry`、`agents`、`edges` 及 `resources` 為準，遵守連線的方向、呼叫／委派語意、條件、資料欄位與最大重試次數，不能以畫布位置或 `ui_layout.nodes` 推定執行先後；該欄只供 HTML 保存拖曳排版。
- 使用 Python 3.11+、Flask、必要的新版 AG2 `import ag2` 或經測試的 Python orchestrator，依任務選最少套件；不得混用已改版的 AG2 Classic API；不需要額外購買或部署任何專門的 Coding Agent。
- 請完成真正的 Agent 呼叫、函式工具、背景工作、可查詢進度、取消／超時、持久化歷史與錯誤報告。前端 UI 要是實際專案的真正使用介面。
- 只能使用 `.env` **環境變數名稱**讀取設定，不能將金鑰寫進程式或網頁；不要創建或覆寫真正 `.env`，只建立 `.env.example`（空值）、`.gitignore`、`requirements.txt`、`README.md`。
- 若 JSON 指定 retrieval，請先檢查本階段另外提供的資料（若有），依資料附件實際內容實作 BM25 + jieba；已驗證 Embedding 可用時才加入 dense 或 hybrid + RRF。若沒有資料附件，先清楚說明缺少的資料，不能造假資料來源。
- 若 JSON 的 `resources.retrieval.web_search.enabled=true`，請真正建立可被 Agent 呼叫的 Live Web Retrieval **Function Tools**：`ddgs.text/news` 搜尋列表 → 官方來源優先排序／過濾 → `requests` 抓取靜態網頁，必要時 `Playwright` 載入動態網頁 → 文字清理、分段與來源 metadata → 可選的 BM25／Dense／Hybrid + RRF → 來源查核與引用。可使用 `ddgs.extract()` 作為備選擷取手段，但不能只用搜尋摘要充當全文；逐一記錄搜尋列表與實際擷取結果、抽取失敗原因。搜尋結果需留存 URL、title、published_at（若可驗證）、retrieved_at、source、chunk_id；顯示來源與查核狀態。
- 網頁擷取必須有安全限制：僅允許經核准的公開 HTTP(S) 網址、阻擋 localhost／內網／雲端 metadata IP、重導向重新驗證、防止 SSRF 與 prompt injection；遵守 robots.txt、網站條款、存取權限和合理 rate limits。限制結果數、內容長度、timeout、併發與快取；不得繞過 CAPTCHA／登入／付費牆或批次下載受保護內容。外部網頁文字只作為資料，不得成為 Agent 的系統指令。
- 混合 Excel 和即時網頁時必須區分來源及更新時間，設計離線／抓取失敗的回退方式；健康資料優先引用官方醫療／衛生來源，星座內容標示娛樂性質，歷史人物的 AI 台詞／影像標示為模擬內容。無可靠來源時不得生成貌似真實的引用或史實。
- 若 JSON 指定 multimodal ngrok API，先檢查本階段另附的 Client／Notebook（若有） 再依規格實作 health、submit、poll、download；未連通的 API 不得回報生成成功。
- 多人共用 API Key 必須遵守供應商的 per-project／per-account 配額及計費限制，做佇列、合理節流與 429 backoff，不以切換 Key 規避限制。
- 程式與 README 使用臺灣繁體中文。產生完整專案 ZIP，包含 Windows 可使用的啟動步驟；實際執行單元測試、Flask HTTP smoke test、必要的 Live API（有權限才做），清楚區分已通過與無法驗證的項目。
- 能操作檔案與終端時，請自行建立、測試並修正，最後提供可下載專案；無法使用工具時如實說明限制，不能假稱已執行測試。

**請勿把本輪改回「先生成 JSON」；JSON 已經確認，現在是透過 ChatGPT、Gemini 或其他 AI 平台進行 Vibe Coding 的建置階段。**

**提交順序：** 初次規劃時一起上傳 `01_專案需求表.docx` + `02_AI流程規劃與修改.md`；在 `03_AI工作流程預覽.html` 本機預覽（不用上傳）；若要改流程，上傳**最新 JSON** + 同一份 `02_AI流程規劃與修改.md` 並說明修改要求；流程確認後才上傳**最終 JSON** + 本檔 `04_Flask專案開發.md`。真正的 `.env` 保留在本機，勿上傳。
