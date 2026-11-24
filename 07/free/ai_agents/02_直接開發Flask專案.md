# 02｜一階段 Vibe Coding：建立真正的 AG2 AI Agent Orchestration Flask 專案

**需求表閱讀規則**：`01_專案需求表.docx` 每題的「例如」僅供參考；請只把各題下方空白框內實際填寫的內容視為使用者需求。空白代表未指定，不可將範例當成已選定的模型、數值、URL 或功能。明確填寫「無」則視為不使用該項；「請 AI 建議」才由 AI 在能力及附件驗證後提出設定。

**提交時**：將填好的 `01_專案需求表.docx` 與本檔一起提供給 ChatGPT、Gemini 或其他能建立檔案的 AI 平台；若有檢索知識庫或多模態服務，再附所需 `.xlsx` 以及**每個選用模型對應的** `.ipynb`、`.py`。**直接開始規劃、實作、測試並交付完整 Flask 專案 ZIP**；不需要先產生 JSON、HTML 節點圖或要求使用者確認 Agent 結構。

## 一、不可省略的要求：真正的 Agent orchestration

1. 這是一個**必須實際使用 AG2 v1.3.3 的多 Agent orchestration 專案**，不是單一 LLM 加幾個 Python 函式、固定 Prompt 串接、寫死的 `if/else` 流程，或只有 Agent 名稱的展示圖。必須能從執行紀錄驗證不同 Agent 確實交接任務及使用工具；不可為了湊角色數量設置沒有實際工作或不會執行的 Agent。
2. 使用新版 `ag2`（`import ag2`）的 **`Agent`、`@tool`／Agent tools、Network／Workflow**。以 **`TransitionGraph`、`Transition`、`FromSpeaker`、`ToolCalled`、`ContextEquals`、`AgentTarget`、`TerminateTarget`、必要時 `Handoff`／`Finish`** 等已確認適用於 v1.3.3 的 API 建立可執行的條件交接、路由、結果回傳與結束規則。**禁止混用 AG2 Classic 的 `autogen.*`、`ConversableAgent`、`GroupChat`、`GroupChatManager`，也不要混用 Microsoft AutoGen 的 `autogen_agentchat`。**實作前核對對應版本的官方文件及實際 Python 簽名，不能盲用網路舊範例。
3. **Agent 的數量與職責由 AI 根據 Word 的實際任務自動規劃，不強制至少三個，也不預設固定上限**。多 Agent 協作至少須有兩個真正參與交接的 LLM Agent；例如簡單的研究／查核任務可用 Researcher＋Reviewer，複雜的檢索與影片生成可加入 Planner、Scriptwriter、Multimodal Director 等。Router、Reviewer、工具都不是所有任務一律必備，應根據風險與工作需求決定；工具不計入 LLM Agent 數量。每個 Agent 必須有明確目的、獨立提示或設定與實際可驗證的工作。若單一 Agent 已足夠，應清楚辨識其為單 Agent＋工具方案，不能誤稱多 Agent；由於本專案要求多 Agent orchestration，需設計合理的最小協作分工，而非徒增空角色。
4. **必須實作可執行驗證的條件分支與 Agent 交接**，以及在任務需品質控管時的有限次回饋修正：例如檢索成功／失敗、證據可信／不足、審查通過／退回重寫。預設最多修正 2 次（Word 若另有設定則依其設定），達上限須終止並回報失敗原因；不需審查循環的簡單任務應說明理由，且仍需有真實的 Agent 協作與條件路由。禁止預先假裝審查通過。
5. **必須真實使用 Function Tools**：由 Agent 透過 AG2 發起並得到結果，再把結果傳給下個 Agent。Excel 讀取、ddgs 搜尋、正文擷取、快取、BM25／RRF、影片生成提交／輪詢／下載與檔案驗證等確定性操作以 Python Tool 執行，不需要再用 LLM 假裝工具。長任務可交由 Flask 背景工作執行，但**背景佇列不是 Agent orchestration 的替代品**。
6. 跨 Agent 傳遞明確的結構化資料（任務、證據片段、來源 URL、引用、草稿、審查結果、修改意見、產物），檢查必填欄位、上限與錯誤。保留任務 ID、Agent 名稱、工具呼叫、交接類型、結果狀態及耗時供 Flask UI 顯示；不要公開 API Key、原始機密資料或模型私有推理過程。
7. **區分兩種「動態」**：開發時依任務規劃 Agent 數量及職責；執行時依請求、工具結果與條件選擇哪些已配置 Agent 參與、執行次序及重試。**執行期間自動產生／銷毀新的 Agent 並非預設要求**，除非 Word 明確提出此需求。不要只因節點多就視為架構更好。

**歷史或知識解說影片的可選協作流程**（僅為參考，Agent 數量仍由 AI 決定）：檢索 Agent 動態收集、重排並核對多份來源 → 故事規劃／編劇 Agent 萃取事件時間線、因果與人物觀點，製作足量口述稿 → 審查 Agent 核對故事覆蓋、史實與演繹邊界，不合格則退回 → 多模態 Agent 依審查過的總片長限制提交一次生成並檢查聲音與嘴型 → 下載驗證 MP4 與獨立 SRT。Planner／Router 可以視任務需要加入，不必為了示例而固定建立；影片人物台詞屬模擬內容，不能冒稱歷史人物真實發言；SRT 應區分「依腳本估計」和「實際語音辨識」。


### 1.1｜AG2 v1.3.3 非同步 API 正確性（避免 coroutine 未 await）

1. **以實際環境的 AG2 v1.3.3 簽名與回傳型別為準**：在實作 Network／Channel、Agent、Tool、事件訂閱與 Task 前，先檢查套件版本、`inspect.signature`、`inspect.iscoroutinefunction` 及官方相應版本文件；不可僅憑方法名稱猜測它是同步或非同步函式。若某方法回傳 awaitable，必須在正確的 `async` 呼叫鏈中 `await`，不能把 coroutine 當作 metadata、dict、已完成的工具結果或成功事件。不同版本可能調整 API，禁止直接以別的 AG2 版本範例取代。
2. **將使用者回報的錯誤列為回歸測試**：`RuntimeWarning: coroutine 'Channel.info' was never awaited`（原錯誤行為是 `info = channel.info()`）。對這個實際場景，若 `Channel.info()` 回傳 coroutine，必須先 `await channel.info()` 再使用結果；對需要同時支援不同實作的適配器，可在明確知道回傳型別後使用 `inspect.isawaitable` 判斷，但不能刻意遮蔽 RuntimeWarning。`channel.send`、`channel.close`、事件／Task 相關方法也要逐個檢查，不要一律假設是同步或一律亂加 `await`。
3. **Flask 與 async 執行邊界必須清楚**：後端使用可管理的 async 執行環境／任務執行器，明確管理 event loop、任務所有權、取消與例外；不得在已運作的 event loop 內呼叫 `asyncio.run()`。未等待的 `Task`、遺失的 coroutine、背景例外、未關閉的客戶端、斷線後遺留的任務都需正確清理與記錄。SSE／WebSocket 只是觀測介面，不可控制 AG2 工作的存活。
4. **必須提供針對性測試**：使用 `AsyncMock` 或實際可用的 Channel 介面，驗證 `info()` 的 metadata 已解析而不是 coroutine；在測試期間開啟 RuntimeWarning 捕捉，對 `coroutine was never awaited`、`Task exception was never retrieved` 視為失敗；驗證非同步 Agent handoff 與 Tool 呼叫確實完成並回收資源。
5. **不得將 Channel／AG2 錯誤轉成靜默成功**：AG2 對象狀態讀取失敗、通知失敗或下游沒有收到交接時，應記錄 `channel_info_failed`、`handoff_timeout` 等明確事件，保留 `run_id`、`handoff_id`、`agent_id` 與堆疊摘要（遮罩敏感資料），不得持續讓 Ollama 重複產生相同內容。

## 二、現有 requirements.txt：以使用者版本為準

使用者的套件版本如下。請以此作為開發與相依性檢查基準，**不要擅自換成不同版本或額外安裝 AG2 Classic**；最終專案的 `requirements.txt` 原則上保留下列鎖定版本，確有必要增補依賴時才增列，並說明原因及經過的安裝驗證。不要因為某項套件與這次功能無關，就擅自把使用者的既有環境當成可任意替換。

```text
pandas==3.1.1
numpy==2.5.5
matplotlib==3.11.2
scikit-learn==1.9.1
ollama==0.6.3
google-genai==3.4.0
python-dotenv==1.2.4
Flask==3.1.3
requests==2.34.2
selenium==4.53.0
tqdm==4.70.1
pooch[progress]==1.9.0
openpyxl==3.1.5
yt-dlp[default]==2026.10.26
beautifulsoup4==4.15.0
lxml==6.1.3
ag2[openai,gemini,anthropic,ollama]==1.3.3
ddgs==9.16.1
```

- AG2 v1.3.3 與 `google-genai==3.4.0` 等套件的**實際安裝相容性**需在目標 Python 環境檢驗；不要僅依版本字串宣稱所有套件可同時安裝。若 `pip` 解出衝突，完整列出衝突鏈與最小修正建議，**不得偷偷修改上述版本**。
- 目前已有 `selenium`，必要時可用於 JS 動態頁面；若因需求而選擇 `playwright`，它**不在現有清單中**，須明確列為新增依賴、安裝瀏覽器及測試。若中文 BM25 需要 `jieba`，亦須明確增列並在 README 記錄版本與用途；不得在程式 import 了卻漏列。
- 依 AG2 新版官方文件確認 `ag2` 的模型設定方式。專案中的模型由實際可使用的 Ollama 或具授權的雲端 Provider 提供；不宣稱所有模型都能工具呼叫。若模型缺少必要的工具呼叫能力，提示需切換模型或標示不可執行，不可把靜態模擬流程說成真實 Agent 工作。

## 三、模型服務、金鑰與多模態附件

1. Word 第 6-1 題只提供 `.env` **變數名稱**，例如 `GEMINI_API_KEY`、`OPENAI_API_KEY_01`；後端使用 `os.getenv()`／`python-dotenv` 讀取本機實際值，絕不把金鑰寫入前端、日誌、JSON 或交付 ZIP。若是「無」，就不能假設有任何商用金鑰。
2. Word 第 6-3 題的 Ollama API URL 可直接填 ngrok、域名或 `127.0.0.1`。在有權限且連得上時透過 `/api/tags`、`/api/show` 探測可用模型與能力，按任務選擇聊天、工具呼叫及 Embedding 模型。URL 可於 `config/services.json` 或受保護的 Flask 後端設定中更新，**不需把 URL 寫進 `.env`**；`127.0.0.1` 指的是 Flask 所在主機。
3. Word 第 9 題每項多模態服務填寫「**模型名稱：API URL**」，例如 `LTX 2.5：https://...`、`Z-Image-Turbo：https://...`、`HeartMuLa：https://...`；**只需附上實際選用模型對應的 `.ipynb`＋`.py` 組合**，不是上傳所有模型。
4. 必須先讀取每組附件並驗證**真實 API 協定**（health、submit、poll、result、download、payload、模型任務類型），不能假設所有端點一樣；沒有附件或無法連線時，清楚指出哪些尚未驗證，不可捏造影片／圖片／音樂成果。
5. 多模型與多 Key 使用必須遵守 Provider 的專案／帳戶配額及計費規則；加上佇列、節流、429 backoff、失敗重試和可取消機制，不得透過輪替 Key 規避限制。服務 URL 也須做存取權限和 host／scheme 驗證，不能允許任意內網請求造成 SSRF。


### 3.0｜自訂雲端 Provider／模型 ID（依 Word 第 6-1／6-2 題）

1. **金鑰名稱與模型 ID 分開填**：第 6-1 題填 `.env` 的變數名稱，第 6-2 題逐行寫 `API_KEY_ENV_NAME → Provider／model_id`（可多組）。例：`GEMINI_API_KEY → Google／gemma-4-26b-a4b-it`；`OPENAI_API_KEY_01 → OpenAI／使用者自訂模型 ID`；也可使用 `ANTHROPIC_API_KEY`、`XAI_API_KEY` 與合法編號的變數名稱。不得將模型名稱當作金鑰值，也不得在 Word、程式碼、設定檔、日誌或 ZIP 中放入真實 Key。
2. **優先尊重明確指定的模型**：各 Agent 可以根據任務需要使用不同 Provider／model_id／API Key 環境變數，但不得未經告知就將使用者指定模型替換成其他模型。沒指定則先做能力與授權探測，再選擇適合任務且實際可用的模型；如需 fallback，須記錄原因與實際使用者設定。模型名稱、費率及可用權限會變，不能單憑本 Prompt 認定可呼叫。
3. **實機確認模型可用性**：在本機載入 `.env` 後依各官方 SDK／API 列舉可用模型或取得模型資訊（如 Google `client.models.list()`），檢查所選 `model_id` 是否能在目前 API version、帳戶、地區、配額與權限下完成最小請求；列表存在仍不代表所有 API 方法都可用。不能連線時應標記 `unverified`，不能虛構成功。
4. **依能力分配工作**：分辨對話、工具呼叫、結構化 JSON、Embedding、視覺理解、音訊及多模態生成能力。文字／視覺理解模型不等於影片生成模型，Embedding 模型不等於聊天模型；不能只因模型具備 `tools` 或 `thinking` 宣告便假設 AG2 handoff、submit／poll 已經成功。對 Provider 設定合法的訊息角色與 System／User Prompt，保留每個 Agent 的實際模型及模板版本。
5. **設定需可日後修改**：在受保護的 Flask 設定頁或 `config/services.json` 中保存 Provider 類型、`model_id`、環境變數**名稱**、功能用途與狀態（不得保存金鑰內容），讓模型升級時只需修改設定而不必重寫 orchestration；更換模型後重新驗證能力、tool schema 與測試。多把 Key 必須遵守供應商帳戶／專案限制，不可輪替以規避額度。

### 3.1｜依使用者意圖與需求動態建立各 Agent 的 System Prompt／User Prompt（必須實作）

1. **每次請求先做意圖辨識**：根據使用者自然語言、Word 專案目標、所提供的 Excel／網頁證據、輸出格式（文字、圖片、影片、音樂）、模型能力及任務限制，建立可驗證的 `IntentPlan`（例如 `intent`、`subtasks`、`required_capabilities`、`tool_choices`、`output_requirements`、`acceptance_criteria`、`constraints`）。同一網站不同請求可以走不同 AG2 分支，不能所有輸入都套用寫死的影片／搜尋 Prompt。
2. **每個實際需要呼叫 LLM 的 Agent 都必須有自己的 System Prompt**：按角色分別設定責任邊界、目標、可用工具、禁止事項、語言風格、輸入／輸出欄位、交接條件、失敗與終止規則。例如 Researcher 必須引用可追溯的證據，Scriptwriter 需覆蓋重要事件與台詞，Reviewer 核對來源與腳本，Multimodal Director 只依已審核分鏡製作模型請求；不得把同一份通用 System Prompt 複製給每個 Agent。
3. **每次 Agent 呼叫需建立對應的 User Prompt**：由使用者原始目標、目前子任務、經過審查的上游結構化資料、檢索結果（含來源 ID、時間、可靠度）、影像／影片參數、要求的 JSON schema 與驗收條件組成；上游輸出只做帶來源標記的資料輸入，不得直接提升為 System 指令。應使用小而完整的上下文，不得每回合無限附加整段聊天歷史。
4. **模板可追蹤、輸出可解析**：把各角色模板集中在專案 `prompts/` 或明確版本化的配置中，依 `intent` 與 `agent_role` 選擇模板並可測試。要求結構化輸出（例如下一個 Agent、已通過檢查的證據、可提交的多模態參數）並用程式驗證；若格式錯誤，有限次修復後回報失敗。不要靠 LLM 輸出「下一步請生成影片」這種自由文字，就認定已呼叫影片 API。
5. **Ollama 模型偵測與能力分工**：根據 Word 指定的 URL，經授權呼叫 `/api/tags` 與 `/api/show` 探測現有模型及其能力，分配聊天、工具呼叫、思考／規劃、Embedding 等用途；不具必要 Tool Calling／JSON 結構能力時採可驗證的替代模式或清楚終止。Ollama 的 System／User 角色應使用該版本 API 實際支援的訊息欄位；不要把全部內容串成單一 Prompt 假裝有角色隔離。模型與服務不可連線時顯示 `unverified`，不能宣稱已完成。
6. **重試與 token／回合上限**：依需求設置每次 LLM 輸出長度、超時、總 Agent 交接回合數、審查回合數與總任務期限。偵測重複輸出、相同 Agent 連續無進展與循環交接；若腳本已通過驗收，立即依 AG2 路由觸發真正的多模態 Function Tool，**不能繼續讓 Ollama 無限制重寫 Prompt**。多模態提交失敗時只在合理條件內重試並保留失敗原因，不要將「已生成 Prompt」等同「已提交影片」。
7. **安全紀錄**：供除錯使用的事件只保存意圖標籤、Agent／Prompt 模板 ID 與版本、輸入／輸出 schema 驗證結果、字數／token 用量（若 API 確實提供）、prompt hash、工具選擇與耗時。預設**不要記錄完整 System Prompt、完整 User Prompt、使用者私密內容、金鑰或模型內部推理**；若有除錯記錄需求，必須經明確授權且有遮罩、權限與保留期限。

**必須測試的 Prompt 情境**：相同服務分別輸入「歷史人物口述影片」、「只要可靠文字答案」、「產生歌曲封面」等需求，應選到不同的 Agent／Tools、System／User Prompt 模板與輸出 schema；提供惡意網頁文字也不能覆蓋系統角色或偷走金鑰。

## 四、Excel／即時網頁檢索與快取（只在需求需要時建立）

1. 讀取提供的 `.xlsx` 知識庫，辨識欄位，保留每筆資料的來源資訊。BM25 若需中文斷詞使用 jieba；能驗證 Embedding API 時再加入 Dense Retrieval；Hybrid 可用 RRF 合併，但不能以虛構向量代替實際檢索。
2. 即時檢索使用 `ddgs.text()`／`news()` **先取得多筆候選，而不是只取第一個網址，也不是固定只採用前 5 筆**。預設先查詢約 20 筆候選（可依需求、配額及實際可取得數量動態調整），整理標題、摘要、來源並去重，再用 `requests` 真正取得候選網頁的正文；必要時用 Selenium 或另行明確加入的 Playwright 載入動態頁。摘要與正文嚴格區分，保留 URL、標題、發布日期（有證據時）、擷取時間、來源類型與 chunk ID。只把搜尋列表當候選，不可直接將搜尋排名或搜尋摘要當作已查證的故事證據。
3. 使用獨立的 `data/web_cache.xlsx`，至少有 `queries`、`pages`、`chunks` 三個工作表；有效搜尋列表或正文快取命中時直接重用，不重做 ddgs／正文擷取。不同查詢命中同一正規化 URL 時正文僅存一份。預設搜尋列表 TTL 1 小時、一般網頁 7 天、新聞 1 天；可強制更新。過期時支持 HTTP ETag／Last-Modified／304，並回報 `cache_hit`、`is_stale`、更新時間。快取不能覆寫使用者上傳的 Excel。
4. 寫入 Excel 時處理鎖定／並行、批次寫入、文字分段、32,767 字元單格限制及原子替換；失敗可保留原快取，但必須顯示過期狀態。檢索與抓取需遵守網站使用規範、合理速率及權限，阻擋任意內網／metadata URL、重新導向繞過、防護 prompt injection，外部頁面只是資料而不是 Agent 指令。


### 4.1｜動態相關性檢索與來源門檻（必要時強制實作）

1. **分開處理候選搜尋量與最終證據量。** `candidate_limit` 與 `final_max_sources`、`relevance_threshold`、`min_evidence_coverage` 是不同參數：推薦起始候選約 20 筆，通過門檻後選取約 0～8 筆高品質來源（僅為可調預設，不是硬性固定筆數）；需要更多故事證據時可增量搜尋或分批抓取，並受網路安全、時間及來源品質上限控制。不得「固定抓一筆」或「找到 5 筆就全部引用」。
2. **真正計算相關性。** 對去重後的候選及正文段落使用 BM25（中文搭配 jieba／經測試的 tokenizer）、字詞 N-gram 相似度（例如 1～3 gram）及關鍵字覆蓋率／keyword count 中至少一種明確量化方法，建議多訊號結合；得分須基於**實際正文**，標題／摘要只能用於擷取優先順序。BM25、N-gram 與 count 尺度不同，需在同一查詢候選集合內正規化或校準後才合成；不可將未正規化的 BM25 分數當成跨查詢通用的百分比。
3. **設置可檢查的採用門檻。** 例如同一查詢下 `normalized_score >= 0.50` 並通過關鍵概念覆蓋檢查（數值只是起始建議，實作需以測試題校準）；短問題、姓名、異名、特殊專有名詞應有相應規則。未達門檻就淘汰，保留每筆分數、拒收原因與命中的關鍵字。`min_evidence_coverage` 也要檢查故事各個重要面向是否已有證據，避免只蒐集同一事件的一小段。
4. **動態補查與來源多樣性。** 如果相關來源不足、事件時間線缺段、前因後果缺證據，Research Agent 必須依條件嘗試擴展關鍵字、使用別名／相關時間地點改寫查詢、提高候選量，最多執行可設定輪數（例如 2 輪）；優先選取不同且可信的來源，避免被相同網站轉載洗版。若仍無足夠證據，回傳「資料不足」與未涵蓋主張，不可為湊出固定筆數而收錄不相關頁面。
5. **排序、檢索與 Excel 快取整合。** 同一份已擷取網頁可重用 `web_cache.xlsx`，但新查詢仍要重新計算查詢相關性；快取命中不等於該來源對本次問題相關。提供 UI 設定與實際 trace：候選數、擷取成功數、快取命中數、門檻、合格來源數、最終採用數、各來源分數與引用段落。不同檢索方法可做可重現的 A/B 比較。
6. **歷史題目特別處理。** 依時間、人物、地點、起因、經過、結果、爭議／不同史料觀點分解查詢，並且明確區分史實記載、文學演繹及 AI 重建。例：「桃園三結義」應說明其《三國演義》文學敘事背景，不能未經查核當成確定的史實。歷史人物的「我當時說……」屬演繹口吻，不得偽稱逐字真實史料。

### 4.2｜Hybrid Retrieval 的完整性與降級規則（不可被 Overview／診斷功能改動）

1. **檢索管線為獨立的業務功能**：Excel 人工知識庫與 `web_cache.xlsx` 網頁快取先標準化為文件／段落，保留 `document_id`、`chunk_id`、來源 URL、擷取日期與版本。Sparse 分支使用 BM25（中文經測試的 jieba/tokenizer）；Dense 分支使用**已驗證**的 Embedding 模型與相同資料版本的向量索引，確實取得 query/document embeddings 並排名。兩者並行或依資源策略執行，使用 **RRF 依各分支排名融合**，不能把原始 BM25 與 cosine 分數直接相加冒充 RRF，也不能以聊天模型輸出冒充向量檢索。
2. **依能力明確選擇 `bm25`／`dense`／`hybrid`**：有 Embedding API 且索引就緒時可啟用 Hybrid；無法連線、模型不具 Embedding 能力、索引缺失時，允許經明示的 BM25 fallback，但要記錄 `requested_mode`、`effective_mode`、`fallback_reason`，在 Flask UI 告知使用者，**不得仍顯示「Hybrid 成功」**。若使用者明確要求一定要 Hybrid，可選擇停止並回報不符合條件。Dense 的索引／維度／模型版本變更時必須重建或拒用舊向量。
3. **先重排，再採用證據**：Candidate Retrieval → BM25/Dense 排名 → RRF（適用時）→ 正文／chunk 相關性門檻與關鍵概念覆蓋 → 動態證據來源數量 → 事實查核；不能因加了視覺化而改變候選集合、門檻、top-k、排名、快取 TTL 或引用。RRF 例如使用 `1/(k+rank)` 的排名融合；`k`、各分支 top-k 與最後來源上限均須可調並記錄設定版本。閾值要用校準後的相關性分數，而非錯把 RRF 當作通用機率。
4. **AG2 與檢索工具分層**：Agent 負責判斷使用者意圖、是否需要檢索、改寫查詢、要求補證據、引用與成果查核；Python Function Tools 負責 BM25、Embedding、RRF、抓取、Excel 快取與段落排序。不得讓多個 Agent 自由轉述取代實際的 Hybrid 演算法；Tool 必須回傳有來源 ID 的結構化結果及失敗原因。
5. **Observability 僅旁路觀測**：每個檢索階段以事件回報 `retrieval_started`、`cache_hit`、`sparse_completed`、`dense_completed`、`rrf_completed`、`threshold_applied`、`evidence_ready`、`retrieval_failed`（只在真的發生時發送）；事件只包含 query/run ID、方法、候選／採用數、索引版本、耗時、fallback 原因及經遮罩摘要。事件傳送失敗不得讓 Tool 變更排名、丟失證據、卡住 Agent 交接或重試檢索；記錄使用有界佇列與適當的失敗隔離。
6. **不變性測試必做**：對固定的 Excel／快取快照與同一批測試問題，在「關閉 Overview／診斷」與「開啟 Overview／SSE」兩種模式，比對 `effective_mode`、BM25 top-k、Dense top-k（有模型時）、RRF 順序、被採納的 source IDs、引用與最終檢索 payload；除事件時間戳等觀測欄位外應一致。用故障注入測試 SSE 中斷／事件儲存失敗也不影響 Hybrid 檢索及後續 Agent 的實際工具結果。

## 五、資料驅動的口述影片生成（僅在 Word 要求影片時啟用）

1. **使用者指定的秒數是整部成品的硬性總長度上限。** 在 Word／網頁指定 `seconds=15` 時，一律映射為 `total_duration_seconds=15`，不是「每段 15 秒」；即使目前的 Notebook／Client 以 `duration` 或 `seconds` 表示單次生成長度，對使用者呈現的語意仍是**整部影片成品不得超過 15 秒**。在任務開始時將總長度上限寫入不可變的 `run_config`，禁止下游 Agent／工具重新解讀。未指定時才可由需求與模型能力提出建議值，並清楚顯示預設的總片長；不預設可無限制延長。
2. **先蒐證，再濃縮成有限時間內可講完的故事。** Researcher 建立可追溯的「起因 → 關鍵經過 → 結果」與來源清單；Writer 根據 `total_duration_seconds` 的實際語速、停頓、鏡頭餘裕與模型能力，產生**一段精簡但可完整理解**的口述稿；Reviewer 必須在提交前核對史實、三段敘事是否成立、台詞能否在總片長內講完，並提出明示的資訊取捨。超出時先退回 Writer 精簡（有限次），**不得以拆段增加成品長度**、不得擅自省略關鍵因果，也不能僅把未講到的內容塞進字幕。
3. **原則上一個任務只生成一支影片。** 預設 `planned_clip_count=1`、每個邏輯工作的正常執行最多一次有效的遠端 submit，生成一支符合上限的 MP4；若品質不合格且使用者事先授權有限次重新生成，須使用**新的品質重試 attempt 與 request_id**，不得把它當作網路重試或恢復操作；禁止 `split_script(script, int(seconds*3))` 等按單段秒數切出多個完整長度影片、重複提交再拼接。若使用者**明確要求多鏡頭／多段**且端點支援，必須先規劃所有片段的時長預算（含銜接／拼接），各段總和與最後 FFprobe 實測成品都不得超過 `total_duration_seconds`；不可因故事長而自行開啟多段模式。若模型無法提供合乎總長度上限的輸出，應在 submit 前回報可支援的秒數與替代方案，經確認才調整；不得事後粗暴截斷人物說話來假裝符合限制。
4. **人物／互動由語言模型依證據規劃。** 有參考圖或明確角色設定時遵守提供的形象；沒有時根據可查證的年代、年齡、服飾、典型場景與角色關係提出角色視覺設定（character bible），不可確定的外觀標記為藝術想像。輸出人物外觀、聲線、構圖、互動、動作與發言者，並讓主講者臉部和嘴型清晰可見；若獲准使用多段影片，應維持人物身分、臉部、服裝與聲線一致。
5. **重要故事必須由畫面人物實際口述。** T2V／I2V Prompt 包含人物、場景、鏡頭、臺灣國語或指定口音、可在時間預算內講完的原創對白、語速、停頓、可見臉部和自然 lip sync；優先保證人聲可辨讀，不可把網頁文字或字幕視為「人物已講完」。如果 API 只會輸出無聲影片，只有在附件確認支援且使用者同意時才加入 TTS／lip-sync 等流程；不能把無聲影片宣稱為已成功口述。
6. **禁止將字幕或任何文字燒進成品畫面。** Prompt 可明確寫 `no on-screen text, no subtitles, no captions, no lower thirds, no signs with readable text, no watermark, no credits, no typography`，但僅靠 Prompt 無法保證畫面絕不出現文字，必要時抽檢影格。Flask 可在播放器外顯示來源及「AI 模擬演繹」，MP4 不嵌入可讀文字；SRT 必須是**獨立的檔案**。
7. **影音品質與口述時間必須真實驗收。** 遠端完成後下載 MP4，以 FFprobe／ffmpeg 核對檔案可讀、實際 duration（嚴格不超過 `total_duration_seconds`）、尺寸、FPS、視訊與音訊串流；有授權 ASR 時核對實際語音、句序、關鍵資訊覆蓋、口述結束時間及 SRT 時間戳，並視可行性檢查 lip sync。無 ASR 只能標示「依腳本估計的 SRT」，不能聲稱已逐字發音或精確對齊；生成模型沒有講完、成品超時、沒有音軌或檔案損壞時明確標示驗收失敗，依核准的**有限次品質重試**或停止，不得默默重新提交。
8. **成果及來源可追溯。** 保存 `story_facts.json`（含來源 IDs）、限時口述稿與 Reviewer 驗收、character bible、使用的 Prompt、模型與參數快照、實際 `run_id`／`request_id`／`job_id`、下載影音與 FFprobe 報告、外部 SRT、最終 manifest。只使用已提供 `.ipynb`／`.py` 與經驗證的模型能力，不臆造 LTX／其他模型的端點與產物格式。
9. **影片參數遵守 Word 與網站的實際設定。** UI 以 `total_duration_seconds`（整部影片總片長上限）作為主要秒數欄位；其他常見選項包含 `seed`、`width`、`height`、`fps`、`aspect_ratio`、語音／人物設定及核准的重試上限。`seconds_per_clip` 只在使用者**明確選擇**多段模式時顯示，且不能取代總片長上限。未填欄位依模型能力提供標示清楚的預設，不得默默更動使用者指定的值。

### 5.1｜跨 Agent 到多模態生成的端對端交付門檻（必須驗證）

使用者回報過一種情況：Flask 已啟動、Ollama 模型顯示 `ready` 且有 `completion`／`vision`／`audio`／`tools`／`thinking` 能力、AG2 已出現真實 handoff、LTX 2.5 `/health` 顯示 `ready` 且偵測到兩張 T4 GPU，但整體工作仍未進入實際影片生成。**這些都是各自的階段性證據，不能用其中任何一個推定已成功提交影片或完成整體 workflow。**

1. **建立強制階段閘門**（依實際模型 API 協定調整名稱）：`intent_resolved → research_completed → script_validated → review_passed → multimodal_handoff_received → tool_invoked → submit_requested → submit_accepted(job_id) → polling → artifact_verified → postprocess_completed → workflow_terminated`。每一階段必須有真實事件、結構化輸入／輸出及失敗分支。上游資料缺少必填欄位時明確拒絕交接，不得跳過工具呼叫卻顯示影片正在生成。
2. **handoff 不等於 Tool Call**：AG2 Multimodal Director 收到合格分鏡後，必須**真正呼叫**已註冊且具備授權的 Function Tool，並把上游 `run_id`／`handoff_id`／`scene_id` 與 `submit_request_id` 關聯；不能以 Director 回覆一段「已開始產生影片」的文字代替工具請求。若 Tool 未觸發，明示 `tool_not_called` 並報告路由條件、tool schema、模型 tool-call 能力或上下文解析失敗原因。
3. **health ready 不等於 submit accepted**：獨立驗證健康檢查、API path／method、payload schema、HTTP status、回傳結構與 `job_id`。只有真正收到有效的非同步 job id（或附件規定的等效執行識別）才可進入 `polling`；若 API 是同步直接返回媒體產物，則依附件的實際回傳協定處理。`/health` 顯示的 GPU 資訊只表示服務當時可被探測，不代表生成已開始或可以保證成功。
4. **輪詢與產物是獨立驗收**：polling 須使用實際的 job id，記錄最近回覆、排隊／執行／失敗／取消狀態及最後實質進度；回傳完成後再確認媒體 URL 或檔案、下載權限、檔案大小、影音格式、可播放性與必要的 SRT。即使外部服務說 `completed`，仍須驗證 artifact 真實存在。預設一個邏輯任務只追蹤一個 job；只有明確授權的多段模式才逐段追蹤，不能把部分片段成功當成最終成功。
5. **終止必須有明確條件**：成功時 AG2 工作須在產物驗證與使用者要求的後處理完成後進入 `workflow_terminated`／`run_completed`，不得讓 Ollama 在背景繼續產生與既有成功任務無關的回覆。失敗、取消、確實無進展時必須有明確終止或可重試狀態；多模態生成可能耗時很久，**不得設定任意過短的預設生成總時限**。以可配置的網路逾時、階段停滯警示、健康回報及授權取消取代固定短秒數強制中止。
6. **端對端回歸測試**：使用 mock AG2 Channel／LLM／LTX API 逐項證明 `Director → Tool → submit → job_id → polling → artifact → termination`，包括 `health=ready` 但 submit 4xx／5xx、submit 回覆無 job id、tool 未觸發、polling 一直無結果、下載損壞、HTTP submit 結果不確定時禁止盲重試、已完成 job 只下載不重送、Flask 重啟恢復、15 秒成品超時、AG2 交接重複及 Channel 未 await；可連線時才進行 Live 驗證。測試報告逐段標示 `passed / failed / unverified`，不能把 mock 假稱真實影片生成成功。


### 5.2｜遠端生成只提交一次、可恢復下載及交付（必須實作）

1. **持久化工作識別與明確狀態機**：建立唯一的 `run_id`（本地執行）、`request_id`／`submit_request_id`（邏輯提交）、`external_job_id`／`job_id`（遠端工作），和一次提交所對應的 `run_config` 指紋；用 SQLite 交易或其他可靠持久化機制，在 submit 前記錄 `submit_pending`，收到遠端回應後原子保存 job ID、遠端狀態和輸出路徑。狀態至少包含 `planned → reviewed → submit_pending → submitted → polling → remote_done → downloading → media_verified → completed`，另有 `failed`／`cancelled`／`submission_uncertain`，且狀態轉移需防止併發執行與重複提交。
2. **同一邏輯工作去重**：刷新網頁、SSE 重連、Flask 重啟、Agent 重新執行或 HTTP 輪詢重試，都不得觸發新的影片生成；如已有 `external_job_id`，只能恢復查詢該 job 或重試下載。若本地影片已驗證完成，直接返回既有產物，不再推論腳本、重新送出 job 或變更原有 run。歷史功能的「**重新生成**」是使用者主動操作，必須建立新的 `run_id`，與自動恢復同一工作嚴格區隔。
3. **重試與遠端冪等性必須查證**：HTTP 提交時可傳固定的 `X-Request-ID` **僅作為追蹤**；只有當實際服務文件或 `.py` Client 證明該服務會以它去重，才可把它當成冪等鍵。若 submit 已送出卻遇到斷線／讀取逾時，不能假設遠端沒有受理，也不能盲目重試；應先透過服務支援的 request/job 查詢介面核對，否則標記 `submission_uncertain`、停止自動重送，讓使用者安全處理，避免重複扣額度與重複生成。
4. **遠端一完成就下載**：當遠端回傳 `done`／`completed`，立即使用**原 `job_id`**取得產物資訊並下載到每次 run 專屬、權限受控的工作目錄；下載失敗只可重試**同一產物的下載**（支援時可續傳），不能重新 submit。下載使用暫存檔與原子更名，完成後執行 FFprobe、檔案大小與格式檢查；驗收通過就將 MP4、外部 SRT、來源與狀態推送至 Flask 頁面，並發送 `artifact_ready`／`run_completed`，終止 AG2 Workflow。若影音品質未過關，進入明確的 `quality_failed`，不得把遠端 `done` 當成最終成功。
5. **斷線／重啟恢復**：背景 worker 在啟動時掃描尚未完成的 run，依持久化狀態恢復已有 job 的 polling／download／verification；避免兩個 worker 接手相同 run（例如 DB 鎖或 lease）。若服務不支援查詢或產物已過期，清楚標記未恢復原因。Flask 及瀏覽器的連線生命週期與遠端生成工作分離；即時監控失效時不得重複提交工作。
6. **驗收與可觀測性**：事件要明確顯示 `submitted`、`submission_uncertain`、`polling`、`remote_done`、`download_retry`、`artifact_verified`、`quality_failed`、`workflow_terminated`，以及最後已知 `run_id`／`request_id`／`job_id`（授權後可見）。加入模擬重啟、兩個 worker 競爭、重複 HTTP request、未知 submit 結果、已完成 job 的下載失敗及成功恢復、重複點擊、15 秒上限驗收、無音軌／口述不完整等回歸測試。測試區分 `mock passed`、`live passed`、`unverified`；未完成真實 AG2／Provider／LTX／Flask 端對端測試時不能宣稱 live passed。

## 六、Flask 網站、真實測試與交付

1. 直接建立符合 Word 需求的 Flask 專案：`app.py`、AG2 orchestration 模組、Tool 模組、背景任務與狀態儲存、`templates/`、`static/`、`config/services.json`、`requirements.txt`、`.env.example`、`.gitignore`、`README.md` 及 `tests/`。勿建立另一套通用 Agent Builder；UI 採臺灣繁體中文並符合 Word 的視覺偏好。
2. UI **必須**顯示**真實、可互動的 AG2 Orchestration Overview**與預設收合的「查看執行細節／開發診斷」面板：完整 Agent／Tool 拓樸、目前執行中的角色光暈、並行 Agent、交接線條動畫、工具呼叫、審查通過／退回次數、背景生成任務狀態，以及可下載產物。任務須有 job ID 與持久化狀態；長時間模型生成不得阻塞 Flask 請求；不得在前端暴露金鑰或敏感日誌。
3. 自動測試至少覆蓋：**(a)** AG2 Agent 實例與 Network／Workflow 被真正初始化；**(b)** 在 mock LLM／mock API 環境下可觀察**實際規劃的 Agent 之間**的交接（不預設 Router／Researcher／Reviewer 都存在）；**(c)** Agent 真正呼叫 Tool，結果流向下一角色；**(d)** 若設計了審查迴圈，須驗證退回修正及達上限終止，未設置則驗證其條件路由與錯誤終止；**(e)** 有網頁快取需求時驗證首次擷取寫入 Excel、第二次有效快取不重抓；**(f)** 不同關鍵字查詢會重新計算 BM25／N-gram／keyword coverage，相關性門檻能拒絕不相關結果，最終來源數量會依測試題動態改變；不足時會觸發擴展檢索或明示證據不足；**(g)** 要求口述影片時，測試 `total_duration_seconds` 為整部成品上限、生成前起因／經過／結果與口述時長審查、預設單一 submit、FFprobe 實測秒數與音軌、無嵌入文字約束、獨立 SRT，並區分 ASR 與估算字幕；**(h)** 模型故障、生成失敗、無證據時有清楚終止與紀錄；**(i)** Flask HTTP smoke test 與 ZIP 產物存在且可讀。測試需分清 mock、離線與 Live，不得把 mock 當成實際模型成功。
4. README 須以簡短的**角色／條件／工具表**說明 Agent orchestration，並提供 Windows／Linux 安裝、執行、API URL 調整、必要模型附件及實際測試結果。引用的 AG2 API 必須符合 v1.3.3。**若開發時遇到 AG2 與其他釘選套件衝突，應先提供可重現的錯誤及最小修改方案，不能自行改版本後宣稱完全遵守使用者環境。**
5. **直接交付可下載的完整 Flask 專案 ZIP**。具備檔案與終端工具時必須自行編寫、執行測試、修正並打包；無法測試外部模型或無法產出 ZIP 時，清楚說明實際限制，不得捏造連結、執行結果或模型生成成果。

### 6.1｜必須內建可即時觀看的 Multi-Agent Orchestration Overview

以下要求**是生成的實際 Flask 專案首頁／工作頁功能，不是獨立離線展示工具**。可參考另外提供的 `03_AI工作流程預覽_執行總覽版.html` 視覺樣式與事件契約，但即使沒有提供該 HTML，也必須完成等效的 Flask 前後端功能。

1. **自動建立完整拓樸**：開發時依 Word 決定實際 Agent 數量；Flask 啟動後從真正註冊的 AG2 Agent、Function Tool 及 Workflow／Transition 產生 Overview，不要要求使用者手工上傳 JSON。節點包括 Agent、Tool／服務、網站入口；連線包括委派、工具呼叫、條件交接、退回修改、成果回傳與並行分支。可提供 `GET /api/orchestration/graph` 回傳與預覽 HTML 相容的 `project`／`entry`／`agents`／`edges` JSON。使用**穩定且跨事件一致的 agent_id、edge_id**；圖形位置不代表執行順序。
2. **每個 Agent／Tool 有真實狀態**：`queued`（排隊）、`running`（執行中）、`waiting`（等待工具、LLM 或其他 Agent）、`succeeded`、`failed`；沒有執行過應維持未執行。執行中的 Agent 卡片出現清楚的光暈／呼吸燈效果，已完成為綠色、失敗為紅色、等待為黃色。符合 `prefers-reduced-motion`；用文字與圖示顯示狀態，不可只靠顏色。
3. **多 Agent 並行及交接視覺化**：同一 run 可以有多個 Agent 同時 `running`，全部一起亮起，不能只用單一 `current_agent` 覆蓋其他工作。發生 `handoff`、`tool_started`、`feedback`、`result` 時，對應連線暫時高亮／流動，並顯示交接來源與目的、工作摘要；可拖曳節點但不能改動真實執行次序。不能用固定延遲的展示動畫冒充真實執行進度。
4. **Overview 即時統計與追蹤**：顯示任務 `run_id`、目前所有執行中 Agent／工具、已完成數、失敗數、等待數、執行歷史與重試次數。使用者可查看單一 Agent 的職責、當前工作、輸入／輸出摘要、工具呼叫結果、開始與結束時間、耗時及錯誤（需遮蔽敏感資料）。若工具執行很久，顯示真實 waiting／polling 狀態，無真實進度值時用不定進度動畫，不捏造百分比。
5. **實際 AG2 事件串流**：從目標 AG2 v1.3.3 的真實 Stream／Observer／事件回呼或等效的已驗證 hook 擷取生命周期事件，在後端統一成事件格式，寫入每個 run 的持久化紀錄。建議以 Flask 同源 SSE `GET /api/runs/{run_id}/events`（`text/event-stream`）即時提供事件，以 `GET /api/runs/{run_id}/snapshot` 恢復斷線前狀態；離線操作可匯出 JSONL。事件至少包含 `event_id`、`run_id`、`timestamp`、`type`、`agent_id`、`message`，交接額外有 `from`、`to`、`edge_id`。事件種類包括 `run_started`、`agent_queued`、`agent_started`、`agent_waiting`、`agent_succeeded`、`agent_failed`、`tool_started`、`tool_succeeded`、`tool_failed`、`handoff`、`run_completed`、`run_failed`。支援遞增事件 ID、SSE 重連、重送去重、心跳、任務資料隔離與授權控管。
6. **真實執行與示範嚴格區隔**：可以提供「播放示範」以便沒有 Ollama／API 時體驗動畫，但必須顯著標記「模擬示範」，且真正執行時所有狀態都來自 AG2 執行事件，不得以前端計時器、虛構成功事件或固定序列掩飾模型尚未回覆。所有敏感金鑰、原始私人資料、內部推理文字不得送往前端；對外 SSE 必須驗證使用者是否有權存取該 run，跨來源接入使用明確 CORS allowlist，避免公開任務日誌。
7. **必須測試 Overview**：使用 mock AG2 事件及 mock 工具測試「單 Agent 狀態變化」、「兩 Agent 並行、同時光暈」、「工具交接連線高亮」、「審查失敗退回再成功」、「失敗與逾時」、「重新整理頁面從 snapshot 還原」、「SSE 中斷及事件去重」。另在可連線的實際 AG2／模型環境中，測試 Overview 事件能對應真正的 Agent 工作，而不是只測前端展示動畫。對未驗證的 Live 部分必須明列限制。

**範例 SSE**（不包含真正的模型推理內容）：

```text
id: 42
data: {"event_id":"42","run_id":"run-001","type":"agent_started","agent_id":"researcher","timestamp":"2026-11-24T14:00:00+08:00","message":"正在核對史料"}

id: 43
data: {"event_id":"43","run_id":"run-001","type":"handoff","from":"researcher","to":"scriptwriter","edge_id":"e-research-script","message":"史料整理完成，交接編劇"}
```

### 6.2｜可收合的即時開發診斷面板（必須實作）

這是**實際 Flask 網站的必備功能**，不只是另外附一個 HTML 示範檔。預設在 Overview 下方以「**查看執行細節／開發診斷**」的 `<details><summary>…</summary>` 或 Accordion **收合隱藏**；使用者點開後才看到逐步日誌。正式使用者可只看到簡短狀態，具有診斷權限者才可展開完整（仍已去識別／遮罩）紀錄；發生失敗時，在收合標題顯示簡短錯誤訊息與最近故障步驟。

1. **按實際階段回報，不使用籠統的「LLM 生成中」**：至少區分 `intent_detected`、`prompt_prepared`、`llm_request_started`、`llm_first_token`（有串流能力時）、`llm_response_completed`／`llm_request_failed`、`output_validated`／`output_rejected`、`handoff`／`handoff_rejected`、`tool_started`／`tool_succeeded`／`tool_failed`、`multimodal_health_started`／`multimodal_health_succeeded`／`multimodal_health_failed`、`multimodal_submit_started`／`multimodal_submit_succeeded`／`multimodal_submit_failed`、`multimodal_poll`、`multimodal_artifact_ready`／`multimodal_download_failed`、`run_completed`／`run_failed`。未發生的步驟不能提前顯示成功。
2. **每次交接都要有對帳**：當上游 Agent 輸出通過 schema 驗證後，記錄 `from_agent`、`to_agent`、`edge_id`、`handoff_id`、`payload_schema`、`payload_valid`、交接開始／收到時間及實際下游 `agent_started`。若已送交但未收到、缺欄位、錯誤路由或死循環，應輸出 `handoff_rejected` 或 `handoff_timeout`，註明是哪一筆資料缺失，不得無限回到 Ollama 生成。
3. **LLM 與工具的耗時分開計算**：記錄每次 Ollama 呼叫的 `request_id`、`model_id`、`agent_id`、`prompt_template_version`、開始／首 token／結束時間、回傳狀態、輸出 schema 驗證結果、錯誤類型、重試次數與耗時。若可得才顯示 token 計數；無資料就標示未提供。非串流 Ollama 請求可能沒有首 token 事件，不可偽造。若 LLM 回覆完成卻未觸發 Tool，診斷應明示「**LLM 已完成，但多模態工具未被呼叫**」並指出路由／驗證失敗的原因。
4. **多模態服務每一步獨立追蹤**：分別檢查健康狀態、真正送出的 API 方法／路徑（不包含 token）、HTTP 回應狀態、上游傳入的任務參數摘要、回傳 `job_id`、排隊／生成／失敗狀態、最近一次 poll 時間、下一次重查時間、最終產物是否確實存在及可播放。若從未取得 `job_id`，不得標示「正在產生影片」；應顯示「尚未提交／提交失敗」。SRT 的產生與驗證也是獨立步驟。
5. **活性偵測與卡住判定**：後端持續發送 SSE heartbeat（代表**連線仍活著**，不能當作 Agent 有進度），並追蹤 `last_progress_at`、`stage_started_at`、`stage_deadline_at`。當 Agent／工具超過可設定時限仍未出現**實質進度事件**，發出 `stage_stalled`／`stage_timeout` 警示或終止，標示停住階段、已等待秒數、相關 `request_id` 與修復建議。心跳正常但 Ollama 一直沒有完成時，UI 應明示「連線正常，LLM 尚未完成」，而非把它視為多模態正在生成；若工作仍在進行且 API 無法提供細節，只能顯示等待與最後已知狀態。
6. **即時傳輸與狀態還原**：優先沿用本檔 6.1 節的 Flask 同源 SSE（`EventSource`）＋ snapshot；單向傳送狀態不必為了「即時」另裝 WebSocket。需要即時雙向控制時才評估 WebSocket；取消或重試可用正常授權的 HTTP POST API。事件持久化至 SQLite 或權限受控的 JSONL，SSE 帶遞增 ID 並支援重連與去重，重新整理後可還原正在執行階段與診斷紀錄。不得讓日誌被其他使用者存取。
7. **診斷面板內容**：顯示 `run_id`、目前 Agent／工具、目前階段、上一個成功階段、耗時、重試次數、`job_id`（若存在）、HTTP status、錯誤摘要及每個事件的時間戳。提供「全部／警告與錯誤」篩選與**經過遮罩**的 JSONL 下載；每行可展開看結構化 metadata，但不顯示完整 Prompt、原始私密資料、內部推理或 Key。當應用為多 Agent 並行時，按照 `agent_id`／`request_id` 分開顯示，不能互相覆蓋。
8. **真實告警與停止規則**：可設定 `max_agent_turns`、`max_same_agent_retries`、`llm_timeout_seconds`、`handoff_timeout_seconds`、`multimodal_submit_timeout_seconds`、`multimodal_poll_interval_seconds` 及總 `run_deadline`。到上限時寫出帶原因的失敗事件並停止或按明確策略回退；避免反覆呼叫 Ollama 卻始終不進入多模態工具。無 API 連線、權限錯誤、模型不支援工具、回傳 payload 不合法，都必須在介面顯示可操作的錯誤原因。

**統一診斷事件契約**：在 6.1 節既有 SSE 欄位之外，可加上 `level`（`debug`／`info`／`warning`／`error`）、`stage`、`request_id`、`handoff_id`、`tool_name`、`model_id`、`external_job_id`、`duration_ms`、`http_status`、`attempt`、`error_code`、`last_progress_at` 與**已遮罩**的 `detail`。建議事件例：

```json
{"event_id":"104","run_id":"run-001","type":"llm_response_completed","level":"info","stage":"scriptwriting","agent_id":"scriptwriter","request_id":"ollama-012","duration_ms":18520,"message":"口述腳本已產生，正在檢查格式"}
{"event_id":"105","run_id":"run-001","type":"handoff_rejected","level":"error","stage":"multimodal_handoff","agent_id":"scriptwriter","request_id":"ollama-012","error_code":"MISSING_SCENES","message":"腳本缺少 scenes 欄位，尚未呼叫影片生成 API"}
{"event_id":"106","run_id":"run-001","type":"multimodal_submit_succeeded","level":"info","stage":"multimodal_submit","agent_id":"video_tool","external_job_id":"video-job-01","http_status":202,"message":"已提交影片生成任務，等待服務回報進度"}
```

**非同步與階段性驗收也必須列入測試**：檢測 `Channel.info()` 等 AG2 非同步 API 有否正確 await、捕捉未等待 coroutine／未處理 Task 例外，檢查從 LLM 完成到 Director 收到交接、Tool 真正觸發、submit／job_id／poll／artifact／workflow termination 的每個關聯 ID；不得以 `ready`、LLM 回覆或 SSE 心跳代替完成證據。

**必做測試**：用 mock Ollama／AG2／多模態 API 重現「模型持續回覆但不交接」、「LLM 已完成但 payload 缺欄位」、「工具未呼叫」、「API health 成功但 submit 失敗」、「成功提交後長時間 polling」、「ngrok 中斷」、「同時兩個 Agent 運作」、「SSE 斷線重接與 snapshot 恢復」；每個測試都要有清楚的診斷步驟、錯誤顯示和有限次結束策略。可連線時另做真實 Live API 驗證，不可把 mock 結果視為已成功生成影片。

### 6.3｜AI Agents Coordination 視覺化與業務流程隔離（驗收必要條件）

1. **在真正的 Flask 網頁顯示完整協作圖**：自動從本專案實際註冊的 AG2 Agents、Function Tools、Transition／Workflow 與選用外部服務組成拓樸；包含條件分支、並行、審查退回、工具依賴、成果回傳，且支持拖曳節點、縮放與「顯示全圖」。節點狀態與邊線的動態高亮須依 `run_id`／`agent_id`／`edge_id` 的**真實後端事件**更新；即使有兩個以上 Agent 同時 `running`，也要同時發光，而不是只標示單一 current_agent。工具節點要能看見 BM25、Dense、RRF、網頁快取以及多模態 submit/poll 等確實執行的步驟。
2. **清楚區分流程圖／即時狀態／進度值**：圖形描述的是可執行協作關係；光暈描述現在真的在執行的角色；進度僅在 API 確實提供數值時顯示百分比。具體 Tool 呼叫成功或錯誤用事件標示，離線示範則必須有「模擬」標記。可收合診斷區預設不顯示大量 log，但失敗時應在 Overview 露出簡短錯誤，展開後查看原因、上下游交接、Ollama 呼叫與多模態 job ID。
3. **事件與工作執行解耦**：AG2 工作流程與 retrieval/multimodal Tools **不能依賴前端 SSE 連線是否存在才繼續**；SSE 只是輸出事件及恢復狀態的管道。慢速瀏覽器、斷線、使用者關閉診斷面板，都不得取消或重新觸發檢索與生成。對事件採用任務內順序編號和快照恢復；事件欄位需可對應真實 Agent/Tool，不以定時器產生假的 `succeeded` 或影片 `job_id`。
4. **可追蹤 Agent coordination 及跨層因果**：每次從 Ollama → Reviewer → Multimodal Director → API submit，必須能將 `handoff_id`、上游輸出 schema、下游接收事件與工具執行關聯到同一 `run_id`。若 LLM 已完成而影片工具未呼叫，應標示 `handoff_rejected`／`tool_not_called` 及原因；若 Hybrid 無法使用，顯示是 `bm25` fallback 而非虛構 Dense/RRF 已完成。
5. **驗收測試**：除 6.1、6.2 的 SSE／診斷測試外，新增「兩個 Agent 同時運作顯示雙光暈」、「Agent 交接線條匹配真實 transition」、「Hybrid 三階段 Tool 事件確實顯示」、「觀測端故障對檢索與生成結果零影響」、「重整頁面恢復原 run 與最後真實狀態」；以 mock 與可連線的 Live 測試分別報告。所有自動化測試需確認 API 事件的 ID 與實際執行物件一致，不能只截圖驗證動畫。

### 6.4｜網頁可收合的執行參數設定（按專題功能動態顯示）

1. **設定區使用 Accordion／`<details>`，預設收合**，例如「影片生成設定」、「資訊檢索設定」、「進階網路／快取設定」。不要把所有技術參數直接塞滿首頁；點開後用有單位的欄位及簡短說明顯示，並提供「還原本次初始設定」。送出工作時，後端必須保存本次生效的**參數快照**，執行中修改畫面不應偷偷改變既有工作。Flask 需要正確區分設定草稿、已提交的 run 與後端實際採用值。
2. **影片設定（有影片功能才顯示）**：提供 `seed`、`width`、`height`、`total_duration_seconds`（整部成品總長度上限；主要欄位）／`duration`（依 API 映射）、`fps`、`aspect_ratio`，以及所選模型確實支援的生成步數／量化／生成模式等常用選項。依附件實際模型 API 調整欄位；不能發送 Client 不支援的參數。`seed` 可用「自動／隨機」選項，並記錄後端真正採用的 seed（若 API 提供）；秒數預設只表示「整部成品的總片長上限」，不得誤當每段秒數；只有使用者明確啟用多段模式時才另外出現「單段秒數」，且各段合計不得超過總長度。FPS 需和實際輸出影片核對，不能把期望值顯示為實際值。
3. **預設值的優先順序**：以 `01_專案需求表.docx` **實際填寫的回答**為初始值，接著是經過附件 `.ipynb`／`.py` 與 API capability／health 驗證的模型相容預設，最後才是清楚標示的建議值。Word 中的「例如：1280×720、24 FPS、每段 15 秒」只是範例，未填寫不得視為使用者已明確指定；`seed` 未填時不可自行假定某個固定值。URL 仍由已設定的服務清單管理；真正的 API Key 只從本機 `.env` 讀取。
4. **前後端驗證與清楚回報**：檢查整數範圍、寬高對齊、長寬比、FPS、最大幀數、時長、所選模型支援能力、GPU 記憶體風險及服務限制。若不支援，顯示允許範圍及原因，要求使用者確認可替代設定；不可在未告知時悄悄更改解析度或秒數。可提供 `GET /api/services/capabilities` 顯示**已驗證／未驗證**的服務能力；不得編造固定解析度與最長秒數。後端仍需獨立驗證，不能信任前端欄位。
5. **執行中設定不可任意突變**：每次任務連同模型 ID／URL 設定版本、選項、聲音／字幕策略、來源資料版本建立不可變的 `run_config`。需要變更時建立新任務或取消後再送出；重試要能辨認「同參數重試」和「修改參數重新生成」。Accordion 的開關狀態只影響視覺化，不得影響 Agent 或多模態執行。

### 6.5｜可調檢索設定與逐筆即時進度（有檢索功能才顯示）

1. **檢索設定 Accordion**：至少提供 `candidate_limit`（候選搜尋筆數）、`final_max_sources`／`top_k`（最終來源／段落上限）、`relevance_threshold`、`retrieval_mode`（`bm25`／`dense`／`hybrid`，依實際支援啟用）、`request_timeout_seconds`（單筆網頁請求逾時）、`max_search_rounds`、`max_concurrency`、`force_refresh`（是否略過有效快取）；可加入語系、查詢日期範圍、N-gram 或 Keyword Coverage 的權重。初始值由 Word 的實際需求、能力限制與合理預設決定；前端註明候選筆數與最後採用筆數是不同概念，並驗證合理上下限。逾時欄位只能管單次 HTTP 請求，不可不明就裡地拿來當 LTX 整段生成的總時限。
2. **開始檢索即顯示待處理清單**：在 `ddgs` 回傳候選列表後，立即呈現各筆 `title`、來源網域／URL、順序與 `queued`；擷取時逐筆更新 `fetching`、`cache_hit`、`fetched`、`failed`／`skipped`、HTTP status（可得時）、耗時、取得時間與簡要失敗原因。顯示「目前正在擷取第幾筆／哪個網址」、已成功、失敗、略過與快取命中數；所有顯示需由**真實 Tool 事件**驅動，不可只有 Agent 卡片持續發光但沒有明細。對不可信 URL 只顯示可安全開啟的來源連結，拒絕在介面執行網頁腳本。
3. **檢索階段分段通報**：至少記錄 `search_started → search_results_received → fetch_queued → fetch_started → fetch_succeeded|fetch_failed|cache_hit → chunking_completed → sparse_completed → dense_completed|dense_unavailable → rrf_completed|rrf_skipped → threshold_applied → evidence_ready`；發生動態補查則新增搜尋輪次及原因。顯示每筆相關性分數、過門檻與否、最終採用／淘汰原因、引用來源，以及 Hybrid 降級原因。不得因更新 UI 而改變 BM25、Dense、RRF 或證據採用結果；**Overview／SSE 只旁路觀測**。
4. **持續可觀測且不假裝有進度**：網頁可顯示「已處理 7／20 筆候選」等有分母的擷取進度；若後續動態補查或候選數變動，更新分母與輪次，不把 100% 擷取誤作整體工作 100%。若 ddgs 尚未回覆、頁面正在等待或模型在重排，顯示階段、已等待時間、最後成功事件與下一步；SSE heartbeat 只表示連線正常，不能算作檢索進展。每個頁面單獨處理 timeout／retry，不因單頁失敗就假裝整輪失敗或永遠卡住。
5. **測試**：使用 mock `ddgs`／HTTP 擷取證明同一批候選逐筆顯示 `queued→fetching→done/error`，快取命中不重抓、逾時與失敗可被看見、並行抓取事件不互相覆蓋、最後來源數量依閾值動態改變、切換 `bm25`／`hybrid` 的有效模式被正確記錄。關閉詳細面板或 SSE 斷線後，實際檢索結果必須與開啟時相同，並可由 snapshot 還原清單及結果。

### 6.6｜多模態影片生成狀態、GPU 資訊與時間預估

1. **依實際 API 分清階段**：網頁顯示 `handoff_received → multimodal_health_check → submit_requested → submit_accepted(job_id) → queued → generating → postprocessing → artifact_ready → downloading → verified → completed`，僅在使用者明確啟用多段模式時才逐段顯示 `scene_id`、已完成／總段數、目前生成段落與檔案狀態。只有 API 真的接受任務後才出現「已提交」；健康檢查 `ready` 不代表已開始 GPU 推論。若外部 Client 使用不同回傳格式，依附件適配並保存原始狀態與標準化狀態的對應。
2. **進度與剩餘時間只用可驗證資料**：若生成 API 的 `/jobs/{job_id}` 或事件介面提供 `progress`、`current_step`／`total_steps`、`frames_done`／`frames_total`、排隊位置、`estimated_remaining_seconds`，才顯示對應真實進度與百分比；保留回報時間與來源。若沒有，就顯示目前階段、真實已等待／運作時間、最後更新時間及「剩餘時間未知」，用不定進度動畫而非假百分比。可用**同模型／相同參數的實測歷史耗時**顯示明確標註「粗略估計」的範圍，不能保證完成時間；不可用前端固定計時器假造進展。
3. **GPU 使用情況須由生成服務端回報**：若 API／Notebook Server 有授權的 telemetry（例如 `/health`、`/status`、job metadata 或專屬 `/metrics`），可顯示服務所在主機的 GPU ID、名稱、目前 job 對應 GPU（確有提供時）、GPU 利用率、顯存已用／總量、最近更新時間；資料需標示**設備資訊**與**即時利用率**之差異。對 NVIDIA 可由生成伺服器適當整合 NVML／`nvidia-smi`，AMD 由相容的 ROCm 監控介面提供（實際可用性依環境）；不能從 Flask 主機的 GPU 狀態推定遠端 ngrok 主機 GPU 狀態，也不能由「兩張 T4 ready」推定目前兩張都在為這個 job 運算。
4. **不支援 telemetry 必須誠實顯示**：「生成服務未提供 GPU 即時資料」或「此任務 GPU 對應資訊未提供」，不得假造 GPU、VRAM、利用率或 token／step 數。遠端監控 API 若需額外開發，僅在獲授權的多模態服務端加入，採存取控制與合理頻率；不要把 GPU 監控或任務 ID 暴露在未受保護的公開 ngrok 端點。
5. **長任務穩定性與錯誤提示**：polling 只讀取狀態，不要重複 submit；支援可配置輪詢頻率、暫時斷線重連、工作持久化、可取消（實際 API 支援時）及下載失敗重試（同一 job 不得重送；僅經明確授權才可重新生成）。請求 timeout、任務停滯提醒與遠端任務允許的運算時間上限要分別設定；**影片成品秒數上限**不得誤作 API 請求 timeout；不得用不合理短的強制總時限中斷長影片。日誌顯示哪個 Agent、Tool、API job 與 GPU telemetry 來源發生問題；SSE 斷線不影響生成工作。
6. **測試**：模擬「有進度／無進度 API」、「GPU 僅回報硬體清單／有真實 utilization」、「多 GPU 但無 job→GPU 對應」、「任務排隊、生成、後處理、下載」、「長時間 polling、ngrok 中斷與重連」、「已完成 job 只下載不重送」、「指定 15 秒的成品實測不超過 15 秒」。必須證明無數值時不顯示虛構百分比／剩餘時間；Overview／診斷收合與否不影響多模態 API 的 submit 次數與結果。

### 6.7｜生成歷史、設定還原與重新生成（必須實作）

1. **每次生成保存可追溯紀錄**：在任務建立時立即記錄 `run_id`、`request_id`、使用者原始 `query`、`created_at`（含時區）、任務狀態與設定快照；完成後補充 `finished_at`、模型 Provider／模型 ID／服務設定版本、seed（實際採用值若可取得）、`width`、`height`、`fps`、`total_duration_seconds`（硬性總片長上限）、只有明確要求多段才有的 `seconds_per_clip`、FFprobe 實測片長、檢索模式與門檻、有效來源 IDs、腳本／人物設定與必要的生成 Prompt 版本、實際 `external_job_id`（預設單筆；只有明確多段時才逐段記錄）、產物 manifest（MP4／SRT 路徑、檔案大小、驗證狀態）及錯誤摘要。失敗／取消也保留狀態，避免 UI 重新整理後紀錄消失。**儲存可重現任務需要的非敏感資訊；API Key／原始敏感資料不寫入歷史。**
2. **持久化格式**：可用 SQLite 儲存可查詢的任務與事件，並為每次工作保存一份 JSON manifest（例如 `data/history/{run_id}.json`），或在小型單人環境直接使用有鎖定與原子寫入的 JSON／JSONL；需要 Excel 匯出可另提供，但不要每輪輪詢都重寫整本 `.xlsx`。歷史資料和 `data/web_cache.xlsx` 分開管理；只在事件或工作狀態確實改變時更新。路徑以受控的工作產物目錄為根，保存相對路徑／安全識別子，不可讓瀏覽器任意讀取伺服器磁碟。
3. **網頁的歷史紀錄區可收合或分頁**：顯示時間、問題摘要、模型、任務狀態、影片縮圖／播放、SRT 及可授權下載連結；依日期、查詢與狀態篩選，點選後把**當時的 query、檢索參數、影片尺寸、FPS、seed、選用模型、角色／口述設定**填回原表單（Accordion 自動展開相關欄位），可先編輯再按「重新生成」。重新載入歷史不應立即呼叫 Ollama 或影片 API，避免意外產生費用／工作。
4. **重新生成必須建立新 run**：保留 `parent_run_id` 或 `regenerated_from`，建立新的 `run_id` 與當次不可變設定快照，絕不覆寫前一次影片、SRT 或檢索證據；「重新生成」需明確再次確認才會新 submit；可選擇「沿用當時已保存的來源／腳本」（須有權限且資料仍存在）或「重新檢索最新資料」，並明確顯示選項。若過去使用的 ngrok URL、模型、附件或原始檔已失效，先提示缺失與替代選項，不要默默套用其他模型。隨機 seed 的工作能否精確重現由實際服務是否回傳 seed 及模型決定，不可保證位元級相同。
5. **生命週期與安全**：歷史資料依使用者／工作權限隔離，禁止透過任意 `run_id` 讀取其他人的 query／影片；提供可設定保存期限、容量上限、刪除單筆歷史與相關產物（有確認流程）、安全檔名及下載防路徑穿越。不要直接把完整 Prompt、敏感個資、秘密 URL／token 或 `.env` 放進前端／日誌；必要時做最小化、遮罩與授權檢視。
6. **測試**：完成／失敗／取消任務都能持久化、重啟 Flask 後仍能載入、回填所有表單參數、只載入不觸發 submit、「重新生成」建立新的 run 且保留舊影片、來源檔案不存在時正確提示、歷史查詢／刪除權限有效、SSE snapshot 和歷史狀態一致；測試 JSON 原子寫入／並行讀寫及檔案缺失。若影片實際未生成，不得在歷史顯示可播放成功產物。


### 6.8｜口述影片的無字幕策略、口述稿濃縮與語速控制

**對應 Word 的獨立影片設定欄位**：`E-1` 畫面寬高、`E-2` FPS／畫面比例／Seed、`E-3` 整部影片總長度、`E-4` 人物語速、`E-5` 人物形象與聲音、`E-6` 畫面文字與字幕。每一項都有個別的「例如」和回答欄，**只讀取使用者實際填入的內容，不可把例句當成使用者指定值**。使用者填「請 AI 建議」時，由模型能力及需求推導後明確呈現建議值；留白或填「無」時依適用性處理，不可默默啟用不必要的選項。

1. **預設影片不燒錄字幕。** 對於歷史人物口述影片、教學說明影片或其他重視人物表演的作品，預設要求輸出**乾淨畫面**：不要在影片中嵌入字幕、標題、條列、浮水印式說明文字、下方字幕條（lower thirds）或其他 on-screen text。字幕如有需求，應以**獨立 SRT／VTT 檔案**提供，並在網頁播放器中作為可開關的外掛字幕；不得因為生成方便而把字幕直接燒錄進畫面。若使用者明確要求「影片內要有字幕」才可覆蓋此預設。
2. **多模態 Prompt 需明確寫出「不要畫面文字」。** 建立 LTX 或其他影片模型 Prompt 時，除了描述人物、場景、鏡位、動作、口白與聲音，也要加入等價限制，例如：`no subtitles`, `no captions`, `no on-screen text`, `do not embed any text in the video`, `subtitle-free visuals only`。若模型容易自行加上文字，Reviewer／Director 需把「畫面中不應出現字幕或標題」列為驗收條件，失敗時標記 `burned_subtitle_detected`、`onscreen_text_detected` 等事件，並在有限次數內重試或回報失敗。
3. **檢索到的資料先濃縮，再決定可說完的句子。** 歷史人物影片不是把全部檢索資料逐條塞進 Prompt，而是由 Researcher／Writer 先將來源整理為「起因 → 關鍵經過 → 結果」的**短版口述稿**，挑選最重要、最能代表故事的句子，讓人物在指定總秒數內說完。可以參考使用者提供的孔子範例風格：人物鏡頭穩定、自然說話、嘴型對應、無嵌入字幕；但實際台詞內容由語言模型根據檢索結果與驗收條件產生，不是固定照抄範例文字。
4. **總秒數優先，口述內容其次。** `total_duration_seconds` 代表整部影片成品的總長度上限。若檢索資料很多，必須**先摘要、再生成**；不能先產出過長台詞，最後靠多段拆片或超時影片硬塞內容。當使用者要求 15 秒時，Writer 應主動壓縮成一個在 15 秒內可清楚講完的版本；如果無法兼顧全部細節，必須明確資訊取捨，並在來源／說明中指出哪些內容因長度限制而被摘要或省略。
5. **加入「語速／口述速度」概念，控制可放入的台詞量。** 專案應支援 `speaking_rate`／`speech_speed`（例如 `slow`、`normal`、`fast`）或等價欄位。Word E-4 已提供獨立欄位；即使使用者未填寫，Flask 與 Agent 規格也要先支援這個概念。建議：
   - `slow`：較從容、停頓較多、適合教學感或長者語氣。可先抓 **約 2.5～3.0 個中文字／秒** 的有效口述速度。
   - `normal`：自然教學或敘事速度。可先抓 **約 3.0～3.8 個中文字／秒**。
   - `fast`：資訊密度較高，但仍需維持可懂度與對嘴自然。可先抓 **約 3.8～4.5 個中文字／秒**。
   以上僅為起始估算，實際可講字數仍需留語氣、停頓、轉頭、手勢、表情與模型口型對齊的餘裕。
6. **以安全係數估算可講字數，不要把理論上限塞滿。** 建議由 Reviewer 用「`可用字數 ≈ total_duration_seconds × 每秒字數 × 安全係數`」估算，其中安全係數可先抓 **0.75～0.85**。例如 15 秒、`normal`、3.2 字／秒、0.8 安全係數時，可先控制在 **約 38 字左右**的實際口述稿，而不是直接寫滿 48 字以上。若使用者選擇 `slow`，就應自動降低口述內容量；若選擇 `fast`，可以略增字數，但必須提醒可能降低清晰度、自然度與對嘴品質。
7. **Prompt 與腳本要明確描述聲音風格與節奏。** 若 Word 或網站有指定口音、語速、音色、年齡感、情緒與停頓方式，System／User Prompt 與多模態 Prompt 都要同步帶入。例如：標註「臺灣國語」、「清楚咬字」、「自然停頓」、「像老師對學生說話」、「平穩但有感情」。語速不是單純的 `fast/slow` 文字標籤，還要落到腳本長度、句子長短、停頓設計與分鏡節奏上。
8. **影片驗收要檢查「有沒有真的講完」而不只檢查 Prompt。** 即使影片 Prompt 寫入完整台詞，也不能假定模型一定會逐字說完。必須驗證：影片總長度、音軌存在、語音是否清楚、是否有明顯未講完、嘴型與語音大致一致、畫面是否出現不該有的字幕。若有 ASR，應比對真實口述與預期台詞；若沒有 ASR，SRT 只能標記為「依腳本估計」，不得冒稱為精確逐字稿。
9. **角色形象可依人物描述或史料推定，但要與內容邏輯一致。** 若影片主角是歷史人物，應根據檢索到的人物背景、時代、服飾與場景建立合理形象；若資料不足，可依描述生成「合理想像」的人物外觀，但不得把不確定的視覺細節當成史實。人物造型、年齡、口吻與場景應與其講述內容一致，例如講學型情境可採正面中近景、清楚嘴型、穩定鏡頭，以提高口述可懂度。
10. **網頁可提供相關設定，但不應破壞既有流程。** 若網站啟用影片功能，建議在可收合設定區加入：`字幕方式（預設獨立 SRT、不要燒錄）`、`speaking_rate`、`voice_style`、`accent`、`show_subtitle_in_player` 等選項。這些欄位只影響本次 `run_config` 與後續 Agent／多模態 Prompt，不得直接改寫已提交任務，也不得因 UI 開關而影響 Hybrid Retrieval、Agent handoff 或多模態 submit 的正確性。
11. **實作時優先採用概念映射，而不是硬套單一範例 Prompt。** 使用者提供的孔子 Prompt 可視為「無字幕、自然口述、穩定鏡頭、乾淨音訊」的風格參考。實作時應抽取出可重用的規則：`clean frame`, `no embedded text`, `speech-centered scene`, `stable face visibility`, `natural lip sync`, `spoken summary based on retrieved evidence`，再依實際人物與故事自動填入；不要只把同一長段 Prompt 套到所有歷史人物題目。

## 七、開發順序與交付門檻

讀取 Word 與實際附件 → 查 AG2 v1.3.3 官方 API／驗證 requirements → 建立真實多 Agent Workflow 與 Tool → 完成 Flask 與資料流程 → 測試動態證據篩選與故事覆蓋 → 測試 AG2 非同步 Channel API／await、交接、審查循環和工具呼叫 → 依選用功能測試總片長限制、預先濃縮口述稿、預設單支影片、SRT 與無字畫面 → 驗證各 Provider 的 Key 變數名稱與模型 ID、測試 Ollama System／User Prompt 動態路由、Agent 交接防呆與停滯偵測 → 測試 Hybrid RRF 與 BM25 fallback、觀測開關的不變性 → 測試 Director→Tool→單次 submit→固定 job_id polling→直接下載→FFprobe→artifact→termination、重啟恢復與模糊提交狀態全鏈路及 Flask、Overview／診斷面板的 SSE、並行顯示、快取與下載 → 驗證可收合影片／檢索設定與 Word 初始值、逐頁擷取事件、真實 GPU／進度來源、無法估 ETA 的誠實顯示、歷史紀錄還原及建立新 run 重新生成 → 打包 ZIP。若外部 API 無法連通，仍交付可以重現的**程式碼、mock 測試與未驗證清單**；但不能以模擬代替真實 Agent orchestration 的程式實作。

## 八｜參數實際生效、內容修正與成果驗證：跨層回歸測試（依實際案例補強）

> **適用範圍**：以下是從其他 Flask 專案的實際問題整理出的**防錯與驗收要求**，不是本次產出的 Flask 程式已通過測試的宣告。只在需求表啟用對應功能時實作；不需要影片或檢索時不要為此加入多餘功能。保留上文指定的套件版本、模型 URL、Excel／Hybrid、使用者總片長、即時進度、歷史紀錄與安全限制。

### 八.1｜UI 參數必須真的影響執行結果（Parameter Effectiveness）

1. **端對端資料流不能斷**：`Word 實際答案 → UI 初始值 → 使用者修改 → JavaScript POST → Flask 解析及驗證 → 不可變的 run_config → 執行流程 → Provider payload → Provider 接受的設定 → 真實產物驗證`。欄位可輸入、Job JSON 有保存數值，都**不等於參數生效**；需追查每一階段，不得偷偷交換、捨棄或覆寫設定。
2. **以實例做映射回歸測試**：輸入 `width=640`、`height=360`、`fps=30`、`seed=123`、`total_duration_seconds=12`，檢查前端、POST、run_config 的使用者要求值一致，Provider payload 則必須依**已驗證的服務契約**精確映射（不保證數值相同），並用 FFprobe 核對實際寬、高、FPS、片長（不超過 12 秒）。**另有疑似 width／height 對調的案例（原需求 512×288，紀錄卻為 288×512）**：先確認使用者當時有無手動修改；若屬映射錯誤，新增固定 regression test，不能直接假定原因並只改某一行。
3. **逐一建立參數效力表**：`width/height/fps → 經過 Provider Contract Adapter 的 payload＋FFprobe（不假設同值）`；`seed → 真正提交的 seed（有提供時另核對服務回傳）`；`total_duration_seconds → 口述預算＋Provider duration／frame_count＋成品上限`；`speaking_rate/accent → 腳本預算／實際 Prompt／語音驗收`；`subtitle_strategy → 外掛 SRT、MP4 無燒字策略`；`candidate_limit/search_rounds → DDGS 搜尋行為`；`relevance_threshold/final_max_sources/retrieval_mode → 排名及最後採用的證據`；`page_timeout_seconds → 逐頁 HTTP 請求`；`force_refresh → 跳過有效快取並實際更新`。檢查「改變某個值時，相應的下游行為是否真的改變」，對不能驗證者標示未驗證。
4. **設定不可隱形替換或跨工作污染**：檢查所選模型的 capability／合法範圍，無法支援的寬高、FPS、時長等，於提交前回傳 422 與允許選項；如 Provider 參數與成品尺寸的語意不同，須用已驗證的 Adapter 映射，不得私自改用預設值。每個工作獨立保存 `run_config`，Job A（512×288、seed 42）與 Job B（640×360、seed 999）併行時不可共用或覆寫設定；網頁編輯中的值也不得修改執行中的工作。

### 八.2｜內容修正循環不是 HTTP Retry

1. **明確區分兩種重試**：網路逾時／429 等暫時性故障的「同一請求重試」與 LLM 已成功回覆但**內容不符合需求**的「修正循環（revision loop）」不同，分別記錄次數與原因。腳本超過口述時間預算時，不能第一次就把整個 Job 設為 failed；應先把超限資訊送回內容產生步驟修正，預設最多 2 次（需求表有指定時依其設定），超限後才 `revision_exhausted`，而非自動增加影片數量。
2. **每次修正傳遞結構化失敗回饋**：至少包括 `revision_number`、`error_code`、`current_characters`、`estimated_duration_seconds`、`maximum_characters`／時間預算、違反的證據或來源 ID、`must_preserve`（事件性質、主要人物、關鍵經過、結果、史實與文學區別）。不能只有「再寫短一點」；保留原始 query 與通過查核的證據，避免每次重抽完全不同的故事。
3. **每修正一次都重跑全套 Validation**：`schema → fact/source_id/chunk_id grounding → 重要知識點及起因／經過／結果 coverage → unsupported claims → historical framing → 預估口述時間`。不能只重測第一次失敗的字數，因為濃縮可能刪掉關鍵事件、加入幻覺或弄丟引用。字數和語速只是**估算**，實際講完與否仍需影片或 ASR／人工驗收。
4. **硬性阻擋條件**：若 `script_validation != passed`，影片 `submit` 的呼叫次數**必須等於零**；證據不足時不得假裝有可靠故事，取消後不能再生成新腳本或提交影片。只有腳本通過、服務設定合法、工作未取消且尚未提交，才可往多模態階段走。有限次失敗要回傳具體原因，而不是讓 UI 永遠顯示「生成中」。
5. **測試五個情境**：首次即合格（0 次修正）；超長後修正 1 次成功；修正 2 次成功；達上限仍超長（`revision_exhausted` 且 submit=0）；長度合格但新增無來源主張／使用者中途取消（不得通過或繼續 LLM／生成）。

### 八.3｜檢索品質、實際 BM25 與查核證據（僅啟用檢索時）

1. **分開計量不同概念**：`candidate_count`、`fetch_success_count`、`valid_body_count`、`relevance_pass_count`、`accepted_sources`、`source_quality`、`source_diversity`、`evidence_coverage`。DDGS 搜尋列表的 URL 可能 403、反爬或無可用正文；例如 7 個候選、5 個 403、2 個取得成功，**不代表此工作必然失敗，但也不代表證據已足夠**。是否進入下一步取決於來源可信度、主張覆蓋及缺口，而不是只看合格筆數。
2. **名實相符的檢索方式**：標記 `bm25` 就必須對正文分段語料的 token／文件集合**真正計算 BM25**，不能以 keyword overlap 冒充。N-gram、關鍵字覆蓋與 BM25 原始分數尺度不同，不能把原始 BM25 直接當 0–1 相關率；任何 `relevance_threshold=0.5` 都需明確說明同一模式內的正規化或校準方式。Hybrid 必須真的具備 Sparse＋Dense／Embedding＋RRF，Embedding 不可用時要明確降級，不能假造 Dense 分數。
3. **相關性不等於來源可信度**：高分新聞或論壇不必然比官方原始資料可靠。保留 `relevance_score`、`source_quality`、`source_diversity`、`evidence_coverage` 為不同訊號；不同網站的轉載不能算多份獨立證據。重大主張需能追到 `fact_id → source_id → chunk_id → script_sentence`，不能只在整份腳本底下籠統附兩個 URL。
4. **按缺口補查而非固定湊筆數**：尤其人物史料要涵蓋「背景、人物、事件、結果、史實／文學區別」。同一來源已回覆部分問題但其餘缺證據，應視搜尋輪數上限進行 query expansion（別名、正史／文學、反方觀點等），失敗後標明 `insufficient_evidence`。外部網頁只是 untrusted evidence，不得執行其中的系統指令或命令。
5. **快取可重用正文，不可重用別的 query 的相關性**：同 URL 被兩個問題查到時，頁面正文可命中 Excel 快取，但相關性／coverage 須針對**本次問題重新計算**。`force_refresh=true` 必須真的繞過有效查詢與頁面快取、重新擷取並更新紀錄；未成功時可明示舊資料已過期但不得冒充最新。把「HTTP 200 後因 `http_status` 變數未定義而失敗」列入具體 regression test：HTTP 成功、正文解析、狀態記錄、後續評分全程不得因 metadata 命名錯誤中止。

### 八.4｜遠端多模態工作：避免重複提交與誤判終態

1. **分開內容修正與外部提交階段**：內容通過前只允許在檢索／LLM／驗證範圍修正。進入 `submitting` 前先持久化 `run_id`、`request_id`、設定快照及提交意圖；取得遠端 `external_job_id` 後立即持久化。遠端 API 支援原生冪等鍵時才使用其保證（例如受支援的 `X-Request-ID`）；**無遠端查詢／冪等機制時不能保證 exactly-once**，只能避免本地重送，遇到未知狀態必須暫停、核對。
2. **提交結果不明不能當一般 failed 立刻 POST**：POST 逾時時遠端可能已接受，將狀態標為 `submission_unknown`／`needs_reconciliation`，先用服務提供的既有 request ID／job 查詢；不能無條件重複生成。成功提交後的 polling 5xx 只重試查同一 `job_id`，下載錯誤只重試下載同一成果，不再 POST 生成。遠端 `done` 後下載、FFprobe 驗證並立即呈現已完成的 MP4。
3. **取消與終止要從後端真正生效**：在搜尋、逐頁擷取、LLM 呼叫、內容修正、提交、輪詢及下載等昂貴階段前檢查取消／終止旗標；`completed`、`failed`、`cancelled` 之後不再觸發新昂貴工作、修改終態或增加重試次數。`submission_unknown` 為**暫停待核對狀態**，不能偷偷進入新 submit；遠端若無 cancel API，明確提示可能仍在運作。前端也須停止已終止工作的無效 elapsed timer／輪詢。
4. **狀態轉換要有可核對的進入條件**：`retrieving → evidence_ready` 需有相關性／coverage／有效來源；`script_validating → script_ready` 需全套驗證通過；`script_ready → submitting` 需設定合法、尚未提交、未取消；`artifact_ready → downloading → verifying → completed` 需實際 MP4、FFprobe、片長／寬高／FPS、音軌及獨立 SRT 的時間邊界。禁止只用 `running/failed` 兩種狀態，也禁止 HTTP 200 或模型回覆「已完成」就宣稱成品成功。

### 八.5｜真實影音驗收、診斷與歷史還原

1. **三層時長驗證**：生成前驗證依 `speaking_rate` 估計的口述時間；提交前驗證 Provider 的 `duration`／frame count 轉換及能力範圍；生成後以 FFprobe 驗證 `actual_duration <= total_duration_seconds`、實際 width、height、FPS、影片流與音軌。有音軌不等於人物講出指定台詞，沒有 ASR 或人工查核時應把 speech／lip sync 標為 `unverified`，不得假稱完成；孔子等第一人稱台詞要在網頁標註「AI 模擬演繹，非史料原話」。
2. **字幕與媒體一致性**：預設 MP4 不燒字，獨立 SRT 依腳本估計時，UI／metadata 清楚標示 `estimated`；若由 ASR 校準才標 `aligned`。最終 SRT 必須在下載影片、取得**實際影片秒數**後再檢查：末句 end 不可超出實際 duration、時間戳要合法、不重疊。角色外觀無法查證的細節標示 `artistic reconstruction`，不得當成確證史實。
3. **診斷應有可執行資訊**：每次失敗至少顯示 `stage`、`reason/error_code`、revision/retry 次數、上一個成功階段、`external_job_id` 是否存在、已保存資料及使用者可採取的下一步。內容修正事件示例：`script_generated → script_validation_failed(duration_budget_exceeded) → script_revision_requested(1) → script_revised → script_validation_passed → script_ready`。逐頁抓取需顯示 URL／HTTP code／拒收原因；預設收合明細不等於隱藏簡短錯誤摘要。事件只能反映真實執行，不能用 UI 動畫虛構已處理或生成的進度。
4. **歷史載入與重新生成是不同操作**：點歷史記錄只能讀入 query、來源、當次設定和既有成果，**絕不呼叫 DDGS、LLM 或影片 submit**；使用者明確按「重新生成」才新建 `run_id/request_id`，設定 `regenerated_from`，且不可覆寫舊產物。歷史與快取各自保存、正確隔離權限。並行的兩個工作要驗證快取和任務設定不互相污染。

### 八.6｜必需的回歸測試與完成標準

| 必測案例 | 合格條件 |
|---|---|
| UI 的寬高／FPS／seed／片長 | 前端、POST、snapshot 需求語意一致；Provider payload 經驗證的 Adapter 正確轉換；FFprobe 驗證真正成品，不能僅測 snapshot |
| 超長腳本 | 有限次內容修正，**每次重跑完整驗證**；達上限才失敗；未通過時 submit=0 |
| 正文 HTTP 200 | 能完成狀態記錄及後續處理；不得因 `http_status` 未定義而中止 |
| 403／少數頁成功 | 逐頁顯示真實結果；不只憑來源筆數判定覆蓋完整，必要時補查 |
| BM25／Hybrid／門檻 | 真正計算相應方法並校準分數；不拿關鍵字重疊冒充 BM25 或拿 raw score 當百分比 |
| `force_refresh` 與快取 | 關閉時有效快取不重抓；開啟時真正重新擷取；新問題重算相關性 |
| 不可重複的外部提交 | POST 斷線標未知待核對；poll／download 故障不重新 generate |
| 取消／終態與並行 | 取消後不發新昂貴請求；終態不被覆寫；A、B Job 設定完全隔離 |
| 影音與 SRT | FFprobe 核對實際寬高、FPS、片長與音軌；SRT 結尾不超過實際片長，估算字幕標明 estimated |
| 歷史紀錄 | 載入不呼叫外部生成；按重新生成才建新 run，保留舊檔 |

**驗證證據須分級**：`mock passed`（模擬外部服務但實際執行應用流程）、`offline passed`（本地真實測試）、`live passed`（真正模型／生成 API 成功）、`manual verified`（人工影音查核）、`unverified`（尚未確認）。交付專案時在 `TEST_REPORT.md` 記錄測試命令、環境、逐項 pass／fail／skip、已知限制與可重現步驟；不能僅憑 UI 顯示、HTTP 200、模型健康檢查或幾項 Mock 測試宣稱完整服務可用。


### 八.7｜AG2 特有的交接及可觀測性回歸測試

- **把關在 Agent handoff，而不只是 Flask Route。** 檢索／查核 Agent 輸出要有 `evidence_ready`，Scriptwriter 的 `script_ready` 必須攜帶通過驗證的結構化腳本及 fact／source 對應；Reviewer 發現超長或 unsupported claim 時，**真實退回 Scriptwriter** 並保留 `handoff_id`、`revision_number`、`validation_errors`。只有審查通過，Director 才能收到 `approved_script` 並真正觸發 Function Tool。不得因 Agent 發出「下一步請生成」等文字就視為完成交接。
- **最重要的硬性測試**：在 mock AG2＋真實 workflow 下強制 Scriptwriter 回傳超長、缺來源或未通過審查的腳本，斷言 `video_submit_tool.call_count == 0`；在修正通過後，驗證 handoff 至 Director、有真實工具呼叫、只提交一次並在完成後終止。若 Agent 同時並行，事件的 `run_id`、`agent_id`、`handoff_id` 必須對應到正確任務，不得互串。
- **非同步與監控解耦**：保留對 `Channel.info()` 未 `await` 的既有 regression；SSE/Overview 只觀察執行，不得導致下一 Agent 在診斷面板收合時無法運作。對一次交接記錄 `handoff_requested → handoff_received → tool_called/validation_failed`；超過期限回報 `handoff_timeout`，而不是無限回到 Ollama。

## 九｜易讀的即時進度面板與輪詢合併顯示


### 九.1｜分階段計時、可捲動執行紀錄與輪詢彙整（Flask UI 必須實作）

1. **用易讀的分階段進度面板取代不斷累積的 log。** 在 Flask 網頁提供始終可見的「目前階段／簡短狀態／該階段已用時間／工作總耗時」摘要，下方以原生 `div` 等區塊建立有適當高度上限（例如桌面 280～360 px）、`overflow-y: auto` 的可捲動清單；進階診斷以 Accordion／`<details>` 預設收合。使用者可在不離開頁面的情況下查看詳細資訊，頁面不應因持續增加文字而無限變長。沒有檢索或影片功能的任務不顯示無關階段。
2. **各階段獨立計算真實耗時。** 依實際任務提供「搜尋候選／逐頁擷取／BM25、Dense、RRF 檢索」、「LLM 產生腳本」、「腳本驗證與第 N 次內容修正」、「多模態提交」、「遠端排隊／影片生成」、「下載」、「FFprobe／ASR／字幕驗證」等階段。每段保存 `stage_started_at`、`stage_finished_at`、`stage_duration_ms`、`status`、`attempt`；佇列等待時間與真正生成時間分開計算，並行階段允許時間重疊，**總耗時不可簡單相加當成實際經過時間**。後端持久化 UTC 時戳與單次階段耗時，前端僅對 `running` 使用視覺計時，完成／取消／失敗時立即停止且保留最後數值；重新整理、重連後以後端 Snapshot 還原，不把每次重新載入當作重新開始。
3. **用溫和而一致的狀態色彩，搭配文字標籤。** `queued`／尚未開始使用中性灰，`running` 使用清楚的藍色，`completed` 使用綠色／藍綠色，`waiting`／可恢復警告使用琥珀色，`failed` 使用紅色；色彩不得是唯一辨識方法，另加「等待／進行中／已完成／失敗」文字與易辨認圖示，維持足夠對比與色覺友善。不要使用刺眼閃爍、彩虹色或對比不足的淡色字；尊重 `prefers-reduced-motion`，不以動畫假裝進度。
4. **LTX polling 只更新既有狀態列，禁止每輪洗版。** 對同一 `run_id + external_job_id + poll_stage` 使用固定 UI row／key，輪詢時更新 `poll_count`、`last_polled_at`、`elapsed`、遠端狀態與 API 真正提供的 progress。例如同一行由「LTX 生成中（1）」更新為「LTX 生成中（2）」，之後到「LTX 生成中（12）｜已執行 02:34」；**不能每隔幾秒新增一行同樣的「生成中」**。只有狀態實際轉變（queued→generating→artifact_ready 等）、Job ID 變化、首次警告、錯誤或有意義的生成里程碑才新增歷史事件；仍可在受控的診斷紀錄中保留必要的原始輪詢摘要，但必須設定長度／頻率上限，避免資料庫與瀏覽器不斷膨脹。計數應反映實際發出的輪詢次數，不得用前端 timer 虛增。
5. **各階段要有足夠細節，但維持畫面穩定。** 搜尋階段顯示候選數、目前擷取 URL、`queued/fetching/cache_hit/fetched/failed`、HTTP status、成功／失敗數及逐頁耗時；LLM 階段顯示第幾次生成、字數或預估口述秒數、驗證是否通過及有限次修正的原因；LTX 階段顯示 submit 是否受理、`job_id`、poll 次數、遠端真實狀態、已執行時間和可得的 GPU／步數／進度。若 Provider 未提供百分比或 ETA，顯示「進度／剩餘時間未提供」，不得製造假百分比。錯誤摘要要直接顯示，即使詳細 Accordion 已收起。
6. **串流事件與渲染負載分開管理。** 後端依真實 Python／模型／工具事件透過 SSE（或等價已實作通道）傳送增量資訊，並提供可恢復的 Snapshot；同一 `event_id` 不可重複套用。前端對高頻、同性質的 polling 訊息做 keyed upsert／節流重繪，而不是無限 append；限制保留的可見事件數（例如最多 200 筆，舊內容可分頁或匯出）、避免整頁重新 render 與強制跳到最底。預設可跟隨最新訊息，但當使用者向上捲動閱讀時暫停自動捲動，提供「回到最新」操作。頻繁 count 更新不要逐次觸發螢幕閱讀器廣播或全頁通知。
7. **只允許觀測，不能改動執行邏輯。** 進度顯示、診斷收合、SSE 斷線、換頁或關閉瀏覽器都不得影響搜尋結果、Hybrid/BM25 排序、模型呼叫、任務取消判斷、LTX submit 次數或已存在的 `job_id`；取消／完成後停止無效的前端計時及不必要的輪詢。觀測資料與工作狀態以 `run_id` 隔離，多個工作不可互相覆蓋，外部 URL、query 和錯誤內容須經安全轉義與授權控管，不輸出 API Key 或完整私密 Prompt。
8. **驗收與回歸測試不可省略。** 模擬同一 Job 連續 50～100 次 polling：畫面**只能有一條**該 Job 的生成中狀態列，計數正確累加；切換遠端狀態才產生里程碑事件。測試搜尋三頁成功／一頁 403、腳本第一次超長後兩次修正、不同階段各自計時、並行兩個 Job、SSE 斷線重接與事件去重、使用者向上捲動時不被強制拉回、工作結束後計時停止與結果可還原。對照後端 trace 驗證每個顏色、時間、計數與狀態均來自真實資料，且關閉面板前後的實際工作結果及外部 API 呼叫次數相同；無法實測的數值清楚標為 `unverified`。

9. **AG2 版特別驗證 Agent Coordination。** 保留即時 Agent／Tool 關係圖及執行中光暈；同時運作的 Agent 應同時亮起，各自記錄此次 active interval 與交接耗時。以真實 `run_id/agent_id/handoff_id/tool_call_id` 對應至上述階段清單；一個 Researcher 可跨檢索工具執行多個階段，但不能因 Agent 卡片持續 `running` 就隱藏下方正在擷取哪一頁、Scriptwriter 正在第幾次 revision 或 Director 是否已呼叫 LTX。確保 Overview 觀測故障不影響 AG2 handoff、Hybrid RRF 與多模態提交。



### 九.2｜階段總覽＋可展開細節＋分層獨立計時（必須實作）

1. **資訊層級與畫面位置**：每個 `run_id` 在首頁有固定且可捲動的「執行階段總覽」；每個主階段是一張可展開／收合的區塊（可使用 `<details><summary>` 或 Accordion），**摘要列始終顯示主階段名稱、狀態、累計耗時與必要的計數**，不需打開診斷才能知道系統正在做什麼。展開後列出細部子步驟、各筆來源、結果與各自耗時；深度診斷、stack trace 仍獨立預設收合。主階段沒有使用時不顯示；失敗時在收合狀態也要能看見失敗摘要。
2. **檢索主階段 `retrieval`**：摘要可顯示「網頁搜尋與擷取｜進行中｜00:38｜候選 20、成功 7、快取 3、失敗 2」。展開可見：搜尋引擎 `ddgs` 的搜尋輪次／耗時、候選結果及 URL 清單、每一頁 `queued → fetching → fetched|cache_hit|failed|skipped`、HTTP status、開始／完成時刻、逐頁耗時與錯誤；正文清理／chunking、BM25、Dense、RRF、相關性門檻、證據覆蓋的各自狀態與耗時。各次 query expansion 顯示輪次及理由；若關閉 Dense，明示 `not_used`，不能用 0 秒假裝已完成。對重複 URL 使用同一列更新，不讓結果清單因重試暴增。
3. **語言模型與驗證主階段**：`llm_generation` 展開可見意圖解析（若有）、Ollama／雲端模型實際呼叫、模型 ID、請求開始與結束、有限次重試及耗時；`script_validation` 展開可見 schema、fact grounding、story coverage、史實／文學區別、字數／預估時長、每次 revision 的失敗原因、修正次數與各自耗時。**HTTP retry 與內容 revision 分別統計**；驗證通過才顯示 `script_ready`，不能因第一次口述稿過長就直接跳到失敗或影片提交。
4. **多模態主階段**：分開顯示 `multimodal_submit`（預檢／payload／提交與確認 job ID）、`remote_queue`（遠端排隊）、`video_generation`（實際遠端生成）、`artifact_download`（下載）與 `media_verification`（FFprobe、音軌、ASR／人工待驗、SRT）。每個階段獨立計時；只有遠端提供 `generating` 起點時，才能把排隊和生成準確分開，否則標為「遠端處理（無法細分）」而非編造生成時間。輪詢保持同一列，如「LTX 生成中（12）｜已等待 02:34」，以實際 poll 次數更新，不新增第 12 條相同紀錄。
5. **時間計算規則**：每個主階段保存 `stage_id`、`started_at`、`ended_at`、`elapsed_ms`、`status`；子階段與每筆頁面以 `parent_stage_id`、`step_id`、`attempt` 關聯，另存自己的時間。後端以單調時鐘計算**同一程序內**的時間差，並持久化 UTC 時間戳、已完成耗時與恢復資訊；重啟後以已保存的事件／狀態恢復，不能重置成零，也不能用變動的系統時間直接替代單調計時。**主階段耗時是該階段從開始到結束的牆鐘時間，不是子步驟耗時加總**：並行擷取三頁可能每頁各 8 秒，但檢索主階段只經過約 8 秒加必要的其他處理；總工作耗時亦不能把並行階段相加。需要成本分析時可另列「所有子步驟耗時加總」，但必須清楚標示是累計工作時間。
6. **等待時間與重新開始的語意**：將本機排隊、遠端排隊、LLM 推論、API 往返、poll 間隔、下載與驗證區分；若某個子步驟重試兩次，可顯示「第 2 次｜本次 00:06｜累計 00:19」。同一主階段重新進入可保存多個 `interval`，主階段累計時間只加總實際活動區間，不重複計入已記錄區間。錯誤／取消／完成立即封存當次區間；停滯時顯示「最後事件已過 00:45」與目前階段，不虛構外部進度。
7. **事件和前端呈現**：以 `run_id + stage_id + step_id (+ attempt)` 做固定列 key，SSE 傳遞 `stage_started`、`step_started`、`step_updated`、`step_finished`、`stage_finished`；輪詢採 keyed upsert 及適當節流。摘要列不應隨新事件重新建立，以免捲動位置、已展開區塊被重置。事件可恢復、去重並保留安全遮罩；每個開關僅影響 UI，不影響執行流程或外部提交。用藍色表示進行中、綠色表示完成、琥珀色表示等待／警告、紅色表示失敗、灰色表示尚未開始或未使用，**搭配文字標籤，不單靠顏色**。
8. **必測例子**：模擬檢索 4 頁（兩頁同時擷取，各 8 秒；另有一頁 403、一頁快取命中），UI 應逐頁呈現結果及耗時，檢索主階段不能把並行的兩個 8 秒加成 16 秒；LLM 第一次超長、revision 一次後通過，兩次模型生成與驗證耗時皆須可展開核對；LTX 100 次輪詢只佔一列，poll_count=100；再測兩個同時運作的 run、取消／失敗／成功結束、重新整理與 SSE 重連，時間與數量都須與持久化的後端執行資料一致。當服務沒有進度百分比或 ETA 時只能顯示耗時及階段，不能虛構數值。
9. **架構邊界**：AG2 版的 Agent／Tool／Handoff 視覺化仍保留，使用相同 run_id 關聯事件，但「執行階段」與「Agent 身分」是不同維度；一個 Agent 可執行多個階段，並行 Agent 可以同時屬於不同主階段。觀測層不得改變 AG2 路由、Hybrid RRF 或多模態提交。

**畫面示意（數字僅為說明，不是實際量測）：**

```text
總耗時 03:26｜目前：影片生成
✓ 網頁搜尋與擷取       00:32  （展開）
  ├─ DDGS 搜尋候選     00:03  20 筆
  ├─ 網頁 A            00:07  成功，HTTP 200
  ├─ 網頁 B            00:01  快取命中
  ├─ 網頁 C            00:08  失敗，HTTP 403
  └─ BM25／Dense／RRF  個別顯示狀態與耗時
✓ LLM 口述稿產生       00:19  （展開）
✓ 口述稿驗證與修正     00:12  （展開）
● LTX 生成中（12）      02:23  （展開：job ID、遠端狀態）
○ 下載與影音驗證       尚未開始
```

**最後執行指令：**直接依 Word 與本開發規格完成可執行的 AG2 Flask 專案、回歸測試與 ZIP；保留真正的 Agent 協作及 Hybrid Retrieval，不以測試計畫代替程式實作。


## 十｜Provider 參數契約：使用者設定、模型請求與實際成品必須分離（新增回歸規範）

> **適用條件**：有圖片／影片／音樂等外部生成 API、且 Provider 的請求參數與最終成品可能不相同時才採用。這一節來自實際 LTX 服務的參數不一致案例，**不是證明所有 LTX 版本都固定輸出 2 倍尺寸**；不得為了符合範例硬套倍率。保留原本的 Hybrid Retrieval、影片總片長、修正循環、一次邏輯提交、進度觀測和歷史紀錄。

### 十.1｜三層參數契約與實際案例

1. **使用者參數（Application Contract）定義的是最終成品。** 網頁的 `width=288`、`height=512` 表示希望下載的 MP4 **最終為 288×512**，與 Provider 接受何種內部解析度無關；工作建立時保存不可變的 `requested_width/height`、FPS、總秒數及 seed。不能因為 API 接受 `width`／`height` 欄位，就認定它們與最終像素有相同語意。
2. **Provider Adapter 必須按服務契約轉換，而非盲目複製。** 本次觀察到某 LTX 服務收到 `288×512` 後輸出 `576×1024`，顯示這組部署當時可能有 `output_dimension_scale=2`。若目前特定服務經 Notebook／Server 程式、官方協定與 **live smoke test** 確認存在 2 倍輸出，則要求最終 288×512 時可計算候選 `provider_width=144`、`provider_height=256`，**但這組映射本身尚未因此被證明在該端點可成功**，仍需驗證其尺寸對齊、最小邊長、最大幀數與實際回傳；若 144 不合法應事先報錯或提供取得使用者同意的替代方案，不可直接送出。無從驗證時標示 `provider_contract_unverified`，不要假設倍率為 1 或 2；但必須提供網站內可操作的初始化／相容性驗證流程，不能讓此狀態成為只能手動修改程式的永久阻擋。
3. **觀測成品（Artifact Contract）獨立驗證。** 下載成功後用 FFprobe 取得 `observed_width`、`observed_height`、`observed_fps`、`observed_duration`、影音流；最終輸出仍必須符合最初的 requested 設定，而不是只和 provider payload 比較。對 FPS 應依檔案特性檢查 `avg_frame_rate`、`r_frame_rate` 與影格時間戳，處理合理編碼誤差但不可把 30 FPS 誤判為 24 FPS；影片秒數以實測及明確的上限規則為準。
4. **每次工作追蹤三組值與契約版本。** 記錄（不含金鑰）`requested_*`、`provider_*`、`observed_*`、`provider_name`、`model_id`、`adapter_version`、`provider_contract_version`、`output_dimension_scale`（僅在已證實時）、轉換與能力檢查結果，以及 FFprobe 驗證證據。除非 Provider 有回報，不能將 seed 已傳送誤寫成可重現性已驗證；語速與口音也需區分「Prompt 指定」與「音訊實測」。

### 十.2｜提交前驗證與禁止靜默替換

1. **轉換必須精確且合法**：檢查輸出倍率、尺寸倍數對齊、最小／最大長寬、任務模式與可用 GPU／模型能力。如果 `requested_width % scale != 0` 或 `requested_height % scale != 0`，**不得使用 `//` 無聲截斷**；例如需求 289×513、倍率 2 不可偷偷變成 288×512。對不能精確映射或 Provider 不支援的參數，返回可解釋的 422 與合法替代值。後製 resize／重採樣只有在使用者明確要求或同意、並在 manifest 標記 `postprocessed=true` 時才允許；**不得偷偷 resize 來掩蓋 Adapter 映射錯誤**。
2. **轉換與模型版本綁定**：`config/services.json` 可保存經管理者確認的 `output_dimension_scale`（如當前服務證實為 2），但應與 service URL、模型、生成模式、版本及驗證日期綁定，僅授權設定／正式測試才能變更。不得看到一次不符合預期，就自動 `observed/requested` 修改永久倍率；mismatch 也可能是舊成品、錯 job、postprocessing、旋轉資訊或 Server 更新造成。Provider 更新後要重新做 contract smoke test。
3. **其他參數也需要語意轉換**：`total_duration_seconds` 可能被 API 表示為秒、毫秒、frames 或含首尾影格的幀數；`fps` 可能受輸出封裝影響；`seed` 可能僅部分流程使用；`speaking_rate/accent` 可能只是口述稿與 Prompt 的規劃值。每個可調參數都要有 `UI → POST → immutable run_config → Adapter → Provider payload → 真實行為或成品驗證` 的路徑；不得把欄位存在或 snapshot 正確，當成已生效。
4. **不得破壞工作冪等與隔離**：先驗證 Provider 契約、腳本、證據、取消狀態與提交許可，再送出**單一邏輯工作**；持久化 `run_id/request_id/external_job_id`，提交逾時且無法辨認遠端是否受理時用 `submission_unknown` 待核對，不得改倍率後直接重送。Polling／下載失敗只查原 job 或重下載；同時執行的 Job A、B 各用自己的不可變設定、Provider payload、產物目錄及暫存檔，嚴防錯抓其他工作已完成的影片。

### 十.3｜端對端回歸測試與可觀測性

| 測試案例 | 必須觀察／驗收的結果 |
|---|---|
| 觀察到的 LTX 2 倍輸出 | 將 `request=288×512 → observed=576×1024` 保存為**此部署的觀察證據**，不得視為所有模型的通則 |
| 經驗證的 `scale=2`，直式需求 288×512 | Adapter 候選 `144×256`，但先檢查 Provider 合法尺寸；只有 Live 回傳 288×512 才可標 `live passed` |
| 經驗證的 `scale=2`，橫式需求 640×360 | Adapter 候選 `320×180`；檢查合法尺寸及不得寬高顛倒 |
| 無法整除／尺寸不對齊 | `289×513` 或其他不合法值回 422，不能 `//` 截斷或暗中調整 |
| 最終尺寸不符 | 若 requested 288×512，FFprobe 得 576×1024 → `verification_failed`，不可標完成，也不可私下 resize 掩蓋 |
| FPS／總片長不符 | 要求 24 FPS／最長 15 秒，實際 30 FPS 或 17 秒 → 驗證失敗並保留實測證據 |
| 工作隔離／舊產物 | 兩個 Job 尺寸與 seed 不同，需驗證各自 `request_id/job_id/manifest/MP4` 一一對應 |
| Provider 升級 | 當 output scale、端點或模型版本變更時先標記未驗證，執行契約 smoke test 後才恢復相容聲明 |

**驗收要求**：測試不應只 assert Job snapshot 或 mock payload；應在條件允許時從瀏覽器表單經 Flask／AG2 Workflow、Function Tool 與真實多模態 submit；各階段需關聯 run_id/agent_id/handoff_id／Provider Adapter 到實際下載成品、FFprobe、最終回報完整檢查。以 `mock passed`、`offline passed`、`live passed`、`manual verified`、`unverified` 分別記錄。失敗時顯示 requested／provider／observed 與 Adapter 版本及可行修復步驟；在預設收合的診斷區保留明細，但**只觀測、不修改**已提交工作、檢索排名或後續工作邏輯。


## 十一｜DDGS 單筆查詢失敗的隔離、恢復與檢索快取防錯（必須實作，僅在啟用即時搜尋時適用）

> **實際故障背景**：Flask 背景工作曾在 `DDGS().text(...)` 遇到 `DDGSException: No results found.`，但同一 Python／Conda 環境另以簡單詞查詢可取得結果。這只能證明單次特定請求失敗，**不能由此認定 DDGS 固定額度用盡、套件全面故障或完全無網路**。成因可能包含特定查詢、上游搜尋端點、短暫網路或限流，但未取得確切服務證據前不得斷言。此錯誤發生於候選搜尋階段，不能歸因於 Ollama 或多模態影片服務。

### 十一.1｜每個 Query 都有獨立的例外邊界與有限重試

1. 檢索流程應處理原始查詢與必要的 expansion queries；**一個查詢詞失敗，不得直接把整個 Flask 任務標成 `failed`**。對 DDGS 可辨識的查詢／連線異常做 query-level exception handling；不可使用 `except Exception: pass` 把程式錯誤、資料型別問題及不可預期 bug 全部吞掉。對不可恢復的程式錯誤應記錄並按原有錯誤處理機制顯式失敗。
2. 每個 query 可配置 `max_search_attempts`（建議起始 **3 次總嘗試，包含第一次**）；首次失敗後可短暫等待約 1 秒、第二次約 2 秒，再加適量 jitter，必要時遵守可靠的 `Retry-After`；重試次數與等待需受整體 `run_deadline`、取消狀態、搜尋輪數與速率限制約束。**不是無限重試，也不是強行繞過上游限制**。失敗達上限就記錄該 query 的結果，繼續下一個合理的 query 或已取得的資料。
3. 將至少三種情況分開：**(a) 搜尋呼叫成功且有候選；(b) 搜尋呼叫成功但回傳空集合；(c) DDGS 拋出例外／無法可靠判斷有沒有結果**。`No results found` 例外不等同已確認的「內容不存在」。允許有可信證據時標記真正的空結果，但不可把暫時性錯誤偽裝成有效的 0 筆結果。
4. 若原始詞失敗或 evidence coverage 不足，依原有 `max_search_rounds` 擴展人物別名、年代、背景、事件及史料面向；合併成功查詢的候選、正規化 URL 去重、再做逐頁擷取、BM25／Dense／Hybrid（實際可用時）、相關性門檻、來源可信度／多樣性與證據涵蓋判斷。**查詢擴展的目的是補證據，不是為湊固定筆數而搜尋**。單一 query 失敗不應破壞原本的 Hybrid RRF 或 Excel 知識庫檢索。
5. 明確區分最終結果：`retrieval_partial_success`（部分 query 失敗但證據足夠）、`insufficient_evidence`（有成功檢索但正文或引用不足）、`search_service_unavailable`（所有允許的查詢在有限重試後都無法可靠完成）、`no_relevant_results`（搜尋成功但確無合格結果），必要時加上 `cancelled` 與 `deadline_exceeded`。**最後採用何種狀態必須由實際搜尋與證據檢查決定，不能只看是否存在 1～2 個候選 URL**。

### 十一.2｜搜尋快取不得放大暫時性故障

1. `data/web_cache.xlsx` 的 query cache **只寫入成功完成且具有可辨識結果狀態的搜尋**；DDGS 例外、逾時、限流或未知結果不得以正常的空列表寫入，也不能覆寫先前有效快取。成功但空集合是否快取、有效期限多長，應明確制定短 TTL 與狀態標記，不可和「搜尋失敗」共用同一筆空值。
2. cache key 應納入經規範化的 query、搜尋型別（text/news）、語系／日期等影響結果的選項，以及必要的搜尋參數版本；不要跨不同查詢直接共用上一個 query 的候選清單或 relevance 分數。`force_refresh=true` 須確實略過有效搜尋快取重新取得資料；快取讀寫失敗不得冒稱成功。
3. **正文快取與搜尋列表快取分離**：先前已抓到的有效網頁可以依 TTL 重用，但對當次新問題仍須重新計算相關性與 evidence coverage；某個 query 失敗也不得刪除其他成功 query 已保存的正文。

### 十一.3｜即時 UI、逐次 Trace 與使用者能理解的錯誤訊息

1. 每一筆 query 的追蹤資訊至少有 `run_id`、`query_id`、查詢文字或經隱私處理的摘要、`search_round`、`attempt/max_attempts`、開始／結束時間、耗時、狀態、`exception_type`、遮罩及截斷的錯誤訊息、下一步行動。**每次失敗需可追蹤，但不把 traceback、金鑰、cookie、token 或敏感查詢原文暴露給其他使用者**。已成功的查詢可回報候選數、去重數；後續逐頁擷取另記 HTTP status 與成功／403／快取命中。
2. 在可捲動的「網頁搜尋與擷取」階段展開細節時，顯示每個 query 的第幾次嘗試、目前是否等待重試、是否改用擴展詞、各子階段獨立耗時，以及最終可用來源與涵蓋程度。重複輪詢或同一狀態持續更新時應**更新原有狀態列／計數器，不無限洗版**；關鍵失敗與查詢切換保留必要的離散事件。
3. 若全數搜尋失敗，UI 應顯示「搜尋服務暫時無法取得結果」並提供最後失敗階段、重試次數、可用的診斷資訊；如果查詢成功但資料不夠，顯示「資料不足」。這兩種情況不可合併成「找不到資料」，也不應直接推測「DDGS 配額用完」。必要時指引開發者在**相同環境**用簡單 query 做 smoke test，再檢查實際 query、網路／DNS／proxy、timeout、並行與上游服務狀態。

### 十一.4｜必備回歸測試及驗收條件

- **Case A：首個 query 連續 3 次拋出 `DDGSException("No results found.")`，下一個 expansion query 成功**。驗證原流程不中斷、trace 有三次失敗、後續擷取與相關性計算仍執行、採用證據依實際內容決定；失敗的 query 不得被快取成正常空結果。
- **Case B：其中一個 query 發生短暫錯誤，第二次嘗試成功**。驗證實際總嘗試次數、退避行為與 cache 寫入僅發生在成功回傳後；測試應 mock 掉 sleep，避免拖長測試。
- **Case C：所有 query 均在可配置上限內失敗**。應回報 `search_service_unavailable` 並有明確終態，不能在無效來源上進行腳本生成或多模態提交，也不能永久停留在 searching。
- **Case D：搜尋回傳成功但候選為 0／正文全為 HTTP 403／正文低於相關性門檻**。分別檢查 `no_relevant_results`、擷取失敗與 `insufficient_evidence` 等對應狀態；不得將 403 與 DDGS 搜尋例外混為一談。
- **Case E：程式自身有非 DDGS bug**（例如未定義變數、schema 錯誤）。不可被 query fallback 靜默吃掉；必須留下真實錯誤與安全的使用者訊息。
- **Case F：取消／期限到達／快取命中／強制刷新／多個查詢並行**。驗證沒有取消後的新昂貴呼叫、查詢與任務間狀態隔離、快取不污染，以及前端 SSE／Accordion 開關不影響實際檢索結果。

驗證紀錄需分清 `mock passed`、`live passed` 與 `unverified`。**在 mock 測試下通過 DDGS 恢復邏輯，只能證明容錯流程，不能證明外部搜尋後端沒有故障。**


**AG2 特有要求**：由檢索 Function Tool 回傳結構化的逐 query 結果（如 `successful_queries`、`failed_queries`、`retrieved_candidates`、`coverage`、`retrieval_status`），讓上游／下游 Agent 可依條件交接、補查、停止或繼續；不要讓單筆 DDGS 例外直接打斷整個 Network，也不要新增一個只是重試搜尋的虛構 Agent。Overview 的 Search Tool 節點須顯示真實 query 重試與擴展狀態；即時事件仍只是旁路觀測，不能改動 AG2 handoff 或既有 Hybrid Search 排名。若 evidence gate 不通過，Director 不得提交多模態 API。

## 十二｜口述稿事實連結（Grounding）驗證、精準修正與可追溯證據（必須實作）


> **實際故障案例**：網頁檢索已完成，但 Flask 背景工作在口述稿修正達上限後回報「台詞缺少事實連結」。這是 **Script Grounding／Schema／Revision 階段**的問題，不能直接歸因於 DDGS 或 LTX。必須先找出失敗台詞、錯誤規則、Fact ID 的來源與傳遞路徑，判斷究竟是無史料支持，還是 Prompt 未傳 ID、Schema 缺欄、ID 被改名、驗證器誤判。**禁止為了讓流程通過而刪除 grounding、讓所有驗證回傳 True，或替每一句話硬塞第一個 fact ID。**

### 十二.1｜來源→事實→台詞的可驗證證據鏈（適用於需史實依據的文字／影片）

1. 先完成 `retrieved_source → source_id／chunk_id／evidence_quote → fact_id／fact_text → script_line` 的資料鏈。**Fact 不能只因 LLM 自己產生並再次引用，就被認定為外部佐證**；每個被接受的歷史事實須能回溯到真正擷取、可引用、可檢查的來源片段。若 evidence／facts 為空、ID 不合法或關鍵內容缺證據，先回報 `EVIDENCE_INSUFFICIENT`，不要仍讓模型產生需要事實證據的腳本，再在下游反覆修正。
2. 口述稿每個語句建議有結構化欄位 `line_id`、`text`、`claim_type`、`fact_ids`；`claim_type` 使用簡明的 `factual`／`transition`／`framing`／`intro`／`outro`。**包含具體史實主張的語句必須有真正支持該主張的既存 `fact_ids`**；不包含史實主張的過場、問候、引言或結語可以是空陣列，不能強迫每句都附來源。若一句話同時包含過場與具體史實，仍須驗證其史實部分；`claim_type` 是輔助訊號，**不能讓模型把史實錯標為 transition 便繞過驗證**。
3. **ID 全鏈一致且型別明確**：Evidence／Fact extraction／Script generation／Revision／Validation 使用同一組穩定的字串 ID；檢查 `fact_1` 與 `fact_01`、`1` 與字串 `"1"`、未知 `fact_999`、跨 Job ID 混用等情況。只確認 `fact_ids` 非空仍不夠：須逐筆驗證其存在、對應 `source_id／chunk_id` 存在、引文可定位、以及該來源內容**確實支持那句話的主張**；不可讓引用僅因文字相似就通過，也不可接受隨意附上不相干的有效 ID。
4. **Quote matching 明確分級**：如果宣稱精確引用，應核對引文與已擷取正文的對應關係；可針對 Unicode、CRLF、連續空白、HTML 空格作受控正規化並標記 `normalized_exact_match`，而不是冒稱 `raw_exact_match`。若屬改寫／意譯，使用獨立的語意支持檢查或人工待驗狀態，不能把語意相近當作逐字引文；也不能以不可靠自動比對替代來源可信度與內容核對。
5. **模型收到的資料必須和驗證條件對得上**：交給 Ollama／Gemini 等模型的有效 facts 應包含 `fact_id`、事實摘要、`source_id`、必要的 `chunk_id` 與來源證據；輸出 Schema 明確要求 `claim_type`、`fact_ids` 的型別及可用 ID 集合。若模型未提供必填欄位，應先回報 `SCRIPT_SCHEMA_INVALID`，不可把 `line.get('fact_ids', [])` 的預設空陣列當成模型真的輸出了空列表，再誤報 `MISSING_FACT_LINK`。

**結構化語句例（僅為資料格式示例）**：

```json
[
  {"text":"建安十三年，曹操率軍南下。","claim_type":"factual","fact_ids":["fact_03"]},
  {"text":"事情要從那段時期說起。","claim_type":"transition","fact_ids":[]}
]
```

### 十二.2｜驗證順序、精準修正與硬性提交門檻

1. 建議依序檢查：`schema → claim_type 與實際主張 → fact_ids 存在性／一致性 → fact→source／chunk／quote 證據鏈 → 主張是否被證據支持 → 重要故事面向 coverage／史實與文學敘事界線 → 語速／總片長預算`。每次修正後都要**重新跑全部檢查**，不能只補 fact ID 便跳過其他驗證。對沒有檢索及史實要求的任務，按 Word 的功能需求調整相應檢查，勿不必要地強制引用。
2. **明確分開錯誤類型**：缺少整個 `fact_ids` 欄位 → `SCRIPT_SCHEMA_INVALID`；欄位存在但 factual line 仍是 `[]` → `MISSING_FACT_LINK`；ID 不在有效集合 → `UNKNOWN_FACT_ID`；有 Fact 但沒有來源 → `FACT_MISSING_SOURCE`；來源／chunk ID 不存在 → `UNKNOWN_SOURCE_ID`；引文缺失／不吻合 → `EVIDENCE_QUOTE_MISSING`／`EVIDENCE_QUOTE_MISMATCH`；主張未被來源真正支持 → `FACT_NOT_SUPPORTED`。多個錯誤可同時回報，不要全部合併成「台詞缺少事實連結」。
3. **Revision loop 不等於 HTTP retry**。驗證失敗時將 `line_index／line_id／text`、`claim_type`、`fact_ids`、`error_code`、`validation_rule`、**可使用的相關 facts 與證據**、必須保留的史實與已通過台詞等，作為結構化 feedback 交給內容修正步驟；修正次數採既有有限上限（例如初稿＋最多 2 次修正）。優先只修有問題的台詞或 metadata，保留其他已正確段落；若語意需要跨句調整，仍須完整重新驗證，避免修好第 3 句卻破壞第 1 句的反覆震盪。
4. 不要因達上限便直接將 `MAX_REVISIONS=2` 改成 10；要先檢查生成 Prompt 是否給了 Fact ID、輸出 Schema 是否符合實際 SDK、ID 是否遺失、驗證器是否過度要求無事實主張的句子也附來源、修正 Prompt 是否真的收到錯誤資訊。**Validator 不能暗中幫 LLM 自動填入看似相近的 Fact ID**；若需要自動對齊，另建可查核的 alignment 步驟並重新驗證，不要把它偽裝成 validation。
5. **必須滿足提交門檻**：`script_validation != passed`、`evidence_gate != passed`、`cancelled` 或 `revision_exhausted` 時，影片 Submit Tool／一般生成函式的呼叫次數必須為 **0**。若修正達上限，回傳 `REVISION_LIMIT_REACHED` 並保存最後的根本原因、錯誤台詞及已有成果；不能讓 LTX 在失敗後被啟動或繼續浪費 GPU。真正的遠端 Job 仍沿用既有的冪等提交及恢復規範。

### 十二.3｜可診斷的狀態、階段耗時與開發證據

1. 在既有的分階段計時／可捲動、可展開介面中，將「事實萃取」、「腳本生成」、「Schema／Grounding 驗證」、「第 N 次內容修正」區分為子步驟，各自記錄開始／結束時間、結果、修正次數。失敗概要可簡短顯示 `腳本證據驗證失敗（2/2）`，展開後顯示**哪一句、哪個 fact、哪條規則**，而不是只寫 `Job failed`。輪詢仍應更新現有狀態列，不造成洗版。
2. 保存結構化且可追溯的診斷資料：`run_id`、`stage=script_validation`、`error_code`、`revision_index`、`invalid_lines[]`（至少 `line_index`、文字或安全摘要、`claim_type`、`fact_ids`、`missing_fact_ids`、`source_ids`、`validation_rule`）、`last_validation_error` 及每一輪結果；必要時保存有權限的 `script_generation_0.json`、`script_validation_0.json`、`script_revision_1.json` 等檔案。避免把私密原始資料、API 金鑰、完整敏感 Prompt 或私有推理記錄在公開 UI／log。
3. **HTTP 200 不等於工作成功**：`GET /jobs/<id>` 返回 200 只表示成功查到工作狀態，仍可能 `status=failed`、`stage=script_validation`。失敗時 UI 顯示失敗階段、具體規則、已修正次數、目前保存內容、是否尚未提交 LTX，以及下一步可行處理方式；前端錯誤詳情與歷史紀錄應能在 Flask 重啟後還原。不得將 Schema 問題冒充純內容問題，或將模型服務健康檢查視為整條流程成功。

### 十二.4｜必做回歸測試（不可只讓例外消失）

- **Schema 與分類**：完整 factual line＋正確 ID 通過；有 factual 主張但缺整個欄位為 `SCRIPT_SCHEMA_INVALID`，明確空列表為 `MISSING_FACT_LINK`；純 transition／intro／outro 無 ID 可通過，但把具體史實錯標 `transition` 不能繞過 grounding；混合過場與事實句仍應受查核。
- **ID／來源鏈**：不存在的 fact ID、fact 無 source、source／chunk ID 不存在、quote 不在正文、引文正規化前後比對，分別回報正確錯誤；有效但無關的 Fact ID、模型自產 facts 自我引用均不可被誤判為已查證。
- **修正迴圈**：能從具體錯誤資訊修復 missing link 並停止；修正後既有正確台詞與來源仍有效；反覆失敗在上限終止並保留最後 `MISSING_FACT_LINK` 等 root cause；不應無限模型重試。測試 evidence 為空、SDK 缺少 JSON 欄位、fact ID 被改名／型別改變，以及中途取消。
- **提交阻擋**：任何 Schema／Grounding／Coverage／Duration gate 不合格時，mock 多模態 Submit 呼叫數皆必須為 0；通過全部檢查才可進入提交。測試階段 trace／錯誤 UI、重新整理後歷史恢復、並行 Jobs 的 ID 與參數隔離。
- **測試標記**：分清 `mock passed`、`offline passed`、`live passed`、`manual verified`、`unverified`。不得因離線的 validator 測試成功，就聲稱真實 Ollama/Gemini 生成的 JSON、史實正確性或 LTX 成品已經實機驗證。

**AG2 特有整合要求**：可依實際需求由 Researcher／Fact Extractor 提供具證據鏈的 Fact 清單，Scriptwriter 使用同一組 ID 產生台詞，Reviewer 依結構化回饋執行內容修正與重新驗證，Director **只能在 `script_ready` 且所有 gate 通過後**經真實 AG2 Handoff 呼叫多模態 Tool。每次交接保留 `run_id／handoff_id／agent_id／validation_result_id`，在 Coordination Overview 中追蹤每一輪修正、Reviewer 退回與提交阻擋；不要新增只用來裝飾的 Agent。**Tool／Reviewer 的確定性檢查結果不能只靠 LLM 自述通過**；AG2 Network 未完成真實交接前不能把影片狀態標成 submitted。


## 十三｜Provider 自動初始化、相容性驗證與可操作性交付（適用於使用外部模型／多模態服務的專案）


### 十三.1｜禁止「只有錯誤代碼、沒有修復途徑」的交付

1. **模型服務的安全阻擋必須附帶可操作的恢復流程**。`output_dimension_scale=null`、`contract_version="unverified"` 等狀態可以存在，但不得讓使用者啟動 Flask 後只收到 `provider_contract_unverified`、`NotImplementedError`、`TODO` 或「請自行修改 services.json」而無法使用核心功能。未完成驗證時應提供可到達的「檢查服務／驗證相容性」入口、清楚原因、可用操作及下一步；在確認契約前**仍不得偷填倍率、略過合法性檢查或提交不安全的正式生成請求**。
2. **以使用者能完成操作為交付標準**：從 ZIP 解壓、安裝相依、啟動 Flask、連線檢查、必要的相容性驗證、提交工作、查看真實進度、下載並驗證產物，皆應有可執行的流程。開發者無法連線遠端服務時，需完成專案內的部署端初始化與 Live 驗證工具、mock 測試、README 疑難排解；不可要求一般使用者研究 latent shape、tensor resolution、內部 frame-count 契約或手動改原始碼。
3. **功能按實際 Word 專題啟用**：只有涉及外部模型／多模態服務才需要此流程；純文字或僅本地運算不必無端加上影片驗證。不同服務按實際 API 實作，不要打造無用的通用 Provider 框架。這份規範是對前面「Provider Contract／禁止靜默變更」的操作性補強，不取代原有的 Param Audit、一次提交、腳本品質門檻或回歸測試。

### 十三.2｜先閱讀真實 Notebook／Server／Client，再建立 Provider 契約

1. **優先讀取使用者提供的 `.ipynb`、`.py`，尤其是 Notebook 內真正啟動 API Server 的程式**；檢查實際 route、HTTP method、health/schema/版本、request body 或 multipart、必填與可選參數、支援 T2V/I2V 等任務、最小／最大尺寸與倍數、FPS、`seconds → frame_count`、seed、音軌、job submit/poll/download/cancel、idempotency 及錯誤回傳。調查 Upscaler／Interpolation／Refiner／編碼後處理是否改變最終輸出。不能只看 Client 範例，或憑「LTX」名稱套用別的版本端點。
2. **契約證據分級**：`source_inspected`（從附件 Server 原始碼推定）、`provider_declared`（遠端 API／schema 宣告）、`artifact_verified`（已完成真實生成且用 FFprobe／實際解析器量測）。來源程式碼若已足以定義欄位與範圍，先依其建立 Adapter；只有部署版本不同、附件不完整或輸出行為仍未知時，才提出 Live 相容性測試。不可把 `health=ready` 或 API 宣告視為已確認真實畫面尺寸／口述內容。
3. **契約需綁定部署身分及適用範圍**：service ID、服務網址安全識別、模型名稱／版本、schema hash、Server／Notebook 版本（有來源時）、任務模式、影響結果的後處理開關；無法得知的欄位標 `unknown`，不要虛構時間戳或版本。若有重大不一致，應拒絕不安全的參數映射，並顯示可重新驗證的操作入口。

### 十三.3｜Flask 自助式服務檢查、受控 Live 驗證與狀態機

1. **網站提供服務狀態頁／設定區**，按需要提供「檢查服務」、「驗證相容性」、「重新驗證」、「取消驗證」、「檢視已驗證範圍」及失敗解法。狀態至少區分 `unverified`、`checking`、`awaiting_approval`、`testing`、`verified`、`partially_verified`、`verification_failed`、`expired`、`offline`；用清楚的臺灣繁體中文呈現，不把「驗證服務成功」誤稱「生成成功」。驗證工作有自己的背景 Job ID 與分階段時間，更新既有可捲動／可展開進度面板，不讓 polling 重複訊息洗版。
2. **不花費推論成本的探測可在啟動或點擊時進行**：受控讀取服務設定與 URL 安全驗證 → 依附件實際協定做 health → 取 service/model/schema/capabilities → 與已保存契約比對 → 解析合法參數範圍。不要假設每個服務均有 `/schema`、`/api/tags`、`/api/show` 等相同路由；只有實際存在才呼叫。ngrok 網址失效、HTTP HTML warning、401/403/404、模型未載入、GPU OOM、非 JSON 回應、schema 缺欄位都要有明確錯誤碼和操作提示。
3. **需要花費 GPU、排隊或付費的實際相容性測試，必須先告知成本／產物用途並取得明確同意**。不要每次啟動 Flask 自動提交生成。測試選擇合法的最短片長與尺寸、固定可重現 Prompt，預先驗證需求及服務限制，記錄唯一 `validation_run_id`、`request_id`、`external_job_id`；若正式服務有明確支持的 idempotency 才能安全重送 POST，否則提交結果不明須標記 `submission_unknown` 並等待核對，不能盲重送。
4. **Live 測試必須下載真正的產物並獨立量測**：MP4 使用 FFprobe／必要時 FFmpeg 檢查實際寬高、FPS（注意 `r_frame_rate`／`avg_frame_rate` 語意）、時長、frame count（可取得時）、codec、影像與音訊軌、解碼可行性；圖片或音樂按實際檔案型別驗證。音軌存在不代表人物真的說對台詞、臺灣國語或對嘴完成，相關項目仍需 ASR／人工檢查，未做就標 `unverified`。一筆測試只證明其參數組合與部署版本，不能推論任何尺寸／模式都安全。

### 十三.4｜Requested／Provider／Observed 三層映射、合法替代及經同意的後處理

1. **UI 填的 `width/height/fps/total_duration_seconds` 是使用者要求的最終成品規格**，每個 Job 保存 immutable `requested_*`。Provider Adapter 依真正服務契約算出 `provider_*`；產物下載後以工具得到 `observed_*`。不得直接假定「API payload 寬高 = 最終 MP4 寬高」，也不得僅檢查已儲存設定就宣稱生效。
2. **倍率只在證據足夠時使用**。例如某部署有經確認的空間上採樣倍率 2，理論上要求最終 `512×288` 會得到候選 Provider 尺寸 `256×144`。若該部署**確實要求**模型輸入最小邊長 256 且為 32 的倍數，`144` 就不合法；這些限制只是特定部署的條件例，**不得當成所有 LTX 2.5 的通用規格**。倍率可不相等、受任務／後處理影響或非固定，不能從單一 mismatch 自動自我修改 `config/services.json`。無法整除時不能用 `//` 截斷蒙混。
3. **先找能直接合規的參數，再考慮可授權的替代方案**。如沒有合法 Provider 輸入能直接得到所需最終尺寸，可在 UI 顯示各方案的模型原始輸出尺寸、是否等比例縮放／補邊／裁切、畫質／視野損失、成本及可否維持指定長寬比；使用者明確同意後才可執行相應後處理。**禁止偷偷 Resize 或以後處理隱藏原有 Provider 映射錯誤**；保留原始模型產物及 `postprocessed=true`、明確方法、核准紀錄，並分別驗證「原始輸出」與「最終交付品」。無法滿足要求則提供合法尺寸／模型替代，不可默默更改 FPS、總片長或解析度。
4. **提交前先驗證**：範圍、倍數、整數、FPS、時長與 frame count 換算、seed、使用任務模式和後處理支援能力；不能確定就標示原因並引導驗證，而非先消耗 GPU 後才發現不合法。FFprobe 最終量測以使用者原始最終規格為基準；保留容器／影格時間精度的可解釋差異，但**硬性總片長上限不得被放寬**。

### 十三.5｜驗證契約持久化、版本失效及背景任務安全

1. **驗證紀錄持久化保存**（SQLite 或安全的 JSON manifest）：`provider/service_id`、安全識別的 URL、model／schema／Server 版本或 hash、能力與合法範圍、驗證來源種類、測試的 requested/provider/observed 參數、倍率／後處理、時戳與時區、是否 Live、適用範圍、有效／部分有效／失效狀態、`validation_run_id`、遠端 job ID、FFprobe 摘要、錯誤與未驗證項目。使用 UTF-8、原子寫入或 transaction、跨工作隔離；不保存金鑰及秘密 URL token，不讓未授權使用者讀取診斷資料。
2. **建立失效條件**：API URL／service ID、模型或 Server 版本、schema、部署或後處理行為改變，或者輸出與契約不一致、驗證有效期過期時，標示 `expired` 並提供重新驗證操作。可沿用仍在適用範圍內且已驗證的契約，不必每次重啟重新產生測試影片。不要從單次未知錯誤自動永久覆寫倍率。
3. **相容性驗證與正式生成共享明確 GPU 佇列／併行上限**，同一部署和參數組合的驗證採併發去重／鎖，避免同時重複花費 GPU。已提交的工作只 poll／download 既有 `external_job_id`；poll、下載、FFprobe、授權的本地後處理失敗不得自動重新 generate。取消需在各高成本階段前檢查；若 Provider 無遠端取消 API，UI 須說明遠端仍可能執行。Flask 重啟要恢復既有 Job，而非自動建立新工作。
4. **錯誤訊息必須可處理**：前端顯示階段、原因、是否已提交／是否會再次耗資源、當前 `job_id`（權限允許時）、可用操作（例如「驗證影片服務」）、合法範圍及後續建議；追蹤詳情放既有收合診斷區，不把 traceback、秘密、token 或 Python 路徑公開。`provider_contract_unverified` 應伴隨初始化入口，不能作為無限期的死路。

### 十三.6｜強制回歸測試與交付驗收

- **全新安裝與 UI**：解壓新 ZIP、安裝相依、啟動 Flask；即使首次 `contract_version=unverified`，仍可進入檢查／驗證頁，不須編輯程式碼；health/schema 有效時能自動保存已知契約，資訊不足時可經授權啟動 Live smoke test。拒絕測試時 GPU Submit 次數必須為 0；驗證失敗、離線或過期時 UI 要提供可執行的恢復步驟。
- **Adapter 與尺寸**：輸出倍率 1、已證明倍率 2、非固定倍率、直式／橫式不對稱尺寸、不能整除、最小邊長與倍數不合、FPS／duration/frame-count 單位差、seed 被忽略等情況，皆需測試規格判定、合法性與真正的 requested→provider→observed 比對。`512×288 / 2 = 256×144` 在前述特定限制下應被拒絕或進入明示替代流程，不能先 submit。
- **後處理**：未獲授權不得自動 Resize、裁切或補邊；獲授權時保留 raw artifact、後處理方法、變更記錄及 FFprobe 最終驗證；不適用、品質不足與不符最終規格時不得標記成功。
- **遠端服務與故障注入**：HTTP HTML 偽裝 JSON／MP4、認證失敗、ngrok 失效、超時、模糊提交 `submission_unknown`、輪詢 500、下載中斷、缺少 FFmpeg、FFmpeg 非零 exit、並行重複點擊、Flask 重啟與取消，驗證沒有重複生成、沒有發佈不完整成品及不會卡死。
- **測試分級**：真實 Flask test client 與瀏覽器介面、mock Provider（真實本地 pipeline）、Windows／Linux（可執行時）、正式 Live Provider 與人工影音檢查分別報告 `mock passed`／`offline passed`／`live passed`／`manual verified`／`unverified`，不能以靜態檢查或 mock 成功冒稱遠端影片已生成。
- **交付物／驗收**：產出**實際可操作的完整 Flask ZIP**，內含真實前後端、可用的 Provider 初始化與驗證流程、所需設定及目錄初始化、`requirements.txt`、`.env.example`、README、`KNOWN_ISSUES.md`、`TEST_REPORT.md`、`CHANGELOG.md`、回歸測試及排錯方式；對新版本需更新實際原始碼和測試再打包，不能只將本節複製到 README。若環境限制導致 Live 未驗證，要寫明未驗證項目及使用者端可執行驗證步驟，但不得宣稱完成正式 Live 驗收。

**AG2 專屬要求**：模型服務的 health／schema／相容性測試是可驗證的 Python Function Tools／後端服務操作，不因其具有「驗證」一詞就新增裝飾用 Agent。若正式流程需要 Multimodal Director，Director 僅在契約於本次參數範圍內有效、上游口述稿與事實查核通過、使用者已核准必要後處理且工作未取消時，透過**真實 AG2 Handoff → Function Tool** 提交。Provider 驗證本身可由 Flask 設定頁直接觸發可管理的背景工作，不必額外模擬 Agent。所有事件對應 `run_id／validation_run_id／handoff_id／external_job_id`，Coordination Overview 顯示真實狀態，SSE 中斷不影響工作存活；不以 Agent 宣稱已驗證代替 FFprobe 或 Live 測試。

**最後執行要求**：依 Word 與所附模型 Server／Notebook／Client 直接開發、驗證、修正並交付 Flask 專案 ZIP；Provider 未驗證時保留安全性，同時提供可執行的初始化／相容性驗證及恢復流程，不可交付只能人工改碼才能使用的網站。


## 十四｜HTTP 中文網址編碼、網頁擷取容錯與可重現回歸測試

### 十四.1｜實際錯誤：HTTP request target 含非 ASCII 字元

使用者實際遇到的背景工作錯誤發生於 `retrieve() → fetch(url) → http.client.HTTPConnection.request()`，Python 標準函式庫在 `http.client._encode_request()` 執行 `request.encode('ascii')` 時失敗。由於方法為 ASCII 的 `GET`，**應優先檢查 request target（URL path／query）是否包含未編碼的中文、空白或其他非 ASCII 字元**；但所附 traceback 尚未包含最後一行完整例外訊息，開發時仍須記錄實際例外型別、失敗網址的安全摘要與已建構的 request target，才能最終確認根因。這是 HTTP request line 的 ASCII 編碼問題，**不是** Windows CP950 的 `read_text()`／UTF-8 檔案讀寫問題，也不是 DDGS 額度耗盡、BM25 或 LTX 服務異常。不要透過 `chcp 65001`、改 Python 原始碼檔案編碼或 `errors="ignore"` 掩蓋。

### 十四.2｜正確建構可發送的 URL 與 HTTP request target

1. **外部 URL 與實際送出的 HTTP request target 是不同表示形式。** 對 `https://example.org/人物/劉備?關鍵字=三國&lang=zh-TW`，網頁顯示或來源紀錄可保留可讀中文；但真正的 path/query 應依 UTF-8 **percent-encoding** 轉換成只含 ASCII 的請求目標（例如路徑 `/人物/劉備` 對應 `/%E4%BA%BA%E7%89%A9/%E5%8A%89%E5%82%99`）。URL 的 scheme、host、port、path、query、fragment 必須分開處理；fragment (`#...`) **不應出現在 HTTP request target**。含國際化網域名稱的 host 應經正確 IDNA 處理，不能將整個 URL 一次粗暴 `quote()`。
2. **優先使用現有的 `requests` 等能正確準備 URL 的 HTTP client**，以已驗證的 `PreparedRequest`／送出結果檢查 path/query 編碼；若必須使用底層 `http.client`，先以 `urllib.parse.urlsplit` 分離元件，對 path/query 按其語意進行 UTF-8 percent-encoding，確認組成的 request target 可用 ASCII 編碼，再呼叫 `request()`。使用自訂 query 時優先用 `params`／`urlencode` 等正確介面；**不可把整個 URL 當 path、把中文直接串進 GET request line，或將 HTTP header 的編碼問題誤當 path 問題**。
3. **避免雙重編碼與語意破壞。** 對已包含 `%E5%8A%89...` 的合法編碼 URL 不得再把 `%` 編成 `%25`；必須明確處理不合法的 `%` escape，保留 `?`、`&`、`=`、`+`、`%20`、重複 query key 與必要的保留字元語意。URL 正規化不可無故刪除有意義的 query 參數、解碼 `%2F` 成路徑分隔符，或將不同網址錯誤合併為同一快取鍵。對含空白、引號、`#`、Emoji、Unicode 網域的網址都要有明確的有效／拒絕處理方式。
4. **重新導向每一跳都要做相同處理與安全檢查。** `Location` 可能是相對路徑、含中文的 URL 或改變 host；必須先依 RFC 語意解析及正規化，再檢查 scheme、host、port、IP/DNS 解析、內網／metadata 禁止清單與存取政策，限制最大跳數。僅對初始 URL 進行 SSRF 檢查後讓 HTTP client 自動跟隨任意 redirect 並不安全；還需考量 DNS rebinding、代理及實際連線目的地的控管。不要為了修正中文網址而放寬原有 SSRF 防護。
5. **區分原始網址、請求網址及快取鍵**：可安全保留 `source_url`、正規化後的 `request_url`、經遮罩的 `request_target`、`redirect_chain`、`response_url`、HTTP status 與 `elapsed_ms`，用於逐頁進度與排查；URL 可能含 token、session、私人查詢參數，日誌與前端必須遮罩敏感資訊。正規化規則與快取鍵需可重現，不能把因編碼失敗的 URL 當成已成功擷取或永久的「無結果」快取。

### 十四.3｜網頁擷取要有 URL-level 失敗邊界，而非直接讓 Job crash

1. **每個候選網頁獨立處理可預期的外部與輸入錯誤**，包括 `UnicodeEncodeError`／URL 百分比編碼不合法、`InvalidURL`、HTTP timeout／connection error、403／404／429／5xx、超多 redirect、文字編碼與正文解析失敗。先視類型修正 URL 或有限次重試暫時錯誤；永久無效 URL 可直接 `skipped`。**單一網址失敗不得直接中斷整個 retrieval 或已完成的其他候選**；必要時補抓其他來源或啟用既有的查詢擴展機制。
2. **明確區分故障層級**：`ddgs_query_failed` 是搜尋候選階段、`url_encoding_invalid`／`http_request_target_invalid` 是發送 URL 階段、`fetch_failed` 是正文擷取階段、`page_rejected` 是擷取成功但無有效正文／不可信內容、`insufficient_evidence` 是最終相關性與證據覆蓋不足。不能把「沒有抓到資料」一律說成「DDGS No results found」，也不能把成功的 GET `/jobs/<id>` HTTP 200 當作工作成功。
3. **捕捉範圍只涵蓋可預期失敗**：在每筆 URL／HTTP 請求邊界捕捉對應例外，記錄 `run_id`、`source_id`、`stage`、`error_code`、例外型別、嘗試次數與安全錯誤摘要；程式變數未定義、錯誤的函式簽名、資料結構不符等 programming bug 不得以 `except Exception: pass` 吞掉。修正 URL 編碼邏輯要用回歸測試證明，不是靠忽略例外。對同一候選的重試需遵守 timeout、rate limit、取消及總任務 deadline。
4. **快取不得擴大暫時故障影響**：URL request 建構失敗、網路故障、403／429、解析錯誤等不應被寫成「已成功抓取的空正文」並在 TTL 期間反覆重用；可保留帶類型與時間的診斷／短期負面狀態以節流，但不得冒充已驗證的正常空結果。已驗證的有效正文快取仍可重用，且每個新查詢都必須重新計算 BM25／Dense／Coverage，快取命中不代表本次相關。
5. **顯示人類可讀的階段資訊**：在原本的 Scroll＋可展開檢索區顯示各候選 `queued → fetching → fetched|cache_hit|failed|skipped`、HTTP status、URL 編碼錯誤／導向原因、每頁耗時與總成功筆數；大量重試只更新該候選的 `attempt` 與摘要，避免洗版。所有可重試 URL 全失敗時顯示「網頁擷取服務異常／無法取得正文」並提供重新檢索與檢查網路的操作，與「資料經評分後不足」分開；已有充足其他合格來源時可正常進入下游。

### 十四.4｜強制回歸測試與交付門檻

- **中文 URL 正常可抓取**：本地 HTTP mock server 使用含中文 path 和 query 的候選 URL，檢查實際收到的 request target 為合法 ASCII percent-encoded 形式，收到 UTF-8 解碼後仍是原本中文；包括中文姓名、繁體中文、罕見漢字、Emoji、空白及國際化網域名稱。
- **編碼完整性**：已編碼 `%E5...` URL 不得雙重編碼；`%20`、`+`、`&`、`=`、重複 query key、`#fragment`、相對 redirect、`%2F` 保留字元與不合法 `%` escape 均有可預期且測試過的行為，URL 去重與快取鍵不誤合併來源。
- **故障隔離**：模擬其中一筆 URL 因編碼、403、429、timeout、redirect 或 HTML 錯誤頁擷取失敗，其餘候選仍能完成正文擷取、相關性與 evidence coverage；若全部 URL 失敗，應回報 `fetch_failed`／`retrieval_unavailable` 而不是假稱「沒有相關資料」。
- **安全與平台**：每次 redirect 都受 SSRF 與 URL policy 檢查；測試 Windows 與 Linux（確實有環境時）、不同預設系統編碼、Excel／SQLite 快取讀寫、日誌 URL token 遮罩。HTTP 請求中的非 ASCII URL 問題不應依賴終端 code page 修正。
- **端對端與防副作用**：由 Flask `/jobs` 建立含中文問題與候選網址的任務，完成真正的擷取與下游資料處理（外部服務可 mock）；確認 retrieval 的單頁失敗不會無故觸發重新 LTX submit，已提交遠端工作不因 retrieval／下載錯誤被重複建立，取消後停止新呼叫。將本次 `http.client._encode_request` 問題列為 Regression 測試，不可只測沒有中文的 ASCII URL 或只測 `GET /`。

**AG2 專屬整合要求**：網頁擷取中的 URL 正規化與請求建構應由實際的檢索 Function Tool／後端服務完成；對每筆 URL 回傳結構化成功／錯誤狀態，再交給 Researcher／Reviewer 作證據判斷與必要的條件交接。**外部網頁 URL 失敗不能被偽裝成 Agent handoff 失敗，也不能讓 Coordination Overview 以假事件顯示成功**。完整的 Agent／Tool／SSE 追蹤仍須以真實 `run_id`、`tool_call_id`、`source_id` 關聯。
