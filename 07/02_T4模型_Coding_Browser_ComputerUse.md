# 02｜T4 15 GB 模型、Coding、Browser Automation 與 Computer Use

## 先選能夠穩定放入 T4 的模型

這裡的大小是 Ollama 官網的**模型檔案大小範圍，不是推論時 VRAM 峰值**。T4 約 15 GB VRAM，Context／KV Cache／影像編碼與同時執行工具都會額外占用記憶體。每次只啟動一個模型，先測 4B，再測 9B。

| 模型 ID（官方） | 官方列出的檔案大小 | Tool Calling | Vision | 主要用途 | T4 結論 |
|---|---:|---|---|---|---|
| `qwen3.5:4b` | 約 3.3–4.0 GB | 有 | 有 | **第一優先**：基本工具、瀏覽器、簡短 Coding | 相對安全 |
| `qwen3.5:9b` | 約 6.6–7.6 GB | 有 | 有 | **第二優先**：較複雜的 Coding、網頁操作、截圖理解 | 建議測 4K／8K Context |
| `qwen3:8b` | 約 5.2 GB | 有 | 無（文字模型） | Coding／文字型工具呼叫的對照 | 不適合依賴截圖的任務 |
| `qwen3:14b` | 約 9.3 GB | 有 | 無 | 進階文字 Agent | 記憶體餘裕較小 |
| `gpt-oss:20b` | 約 14 GB | 有 | 無 | 可當延伸挑戰 | 權重接近 VRAM 上限，不建議課堂預設 |
| `qwen3-coder:30b` | 約 19 GB | 有 | 無 | Agentic Coding | **不建議 T4 15 GB**；可能部分 CPU offload、明顯變慢 |
| `devstral-small-2:24b` | 約 15 GB | 有 | 有 | 進階 Coding | 權重已接近 VRAM 上限，不建議課堂預設 |

**不要因為模型標示 256K Context 就把 Ollama 實際 Context 設成 256K。** Hermes 官方指出，小 VRAM 上 Ollama 預設 Context 可能只有 4,096。Coding／Browser 任務需要更多上下文，但加大 Context 也會增加 VRAM。建議先在 Colab Ollama 設定 **8192**，視 `nvidia-smi` 再逐步增加。避免為了理論最大 Context 導致 OOM。

在 Colab 下載模型（下面在**Colab** 終端，非本機）：

```bash
# EN: Download the smaller all-round model to Colab.
# 繁中：在 Colab 下載較輕量的通用模型。
ollama pull qwen3.5:4b

# EN: Download the larger model for the second experiment.
# 繁中：在 Colab 下載第二個比較用模型。
ollama pull qwen3.5:9b

# EN: Inspect running models and memory utilization.
# 繁中：確認目前載入的模型與 GPU 記憶體狀態。
ollama ps
```

若有無法載入、回應極慢，從 Colab 的 `nvidia-smi`、`ollama ps` 檢查是否 CPU offload。可先用 `ollama stop qwen3.5:9b` 卸載不需要的模型，或在啟動 Ollama server 時降低 `OLLAMA_CONTEXT_LENGTH`、限制同時模型數為 1。不要在單個 T4 上同時測多位使用者的高 Context Agent 任務。

## A. Coding：要求「建立並執行」，不能只是提供程式碼

先在本機建立空白的測試資料夾，例如 `agent-lab`，讓 Hermes 的工作路徑指向該資料夾。啟用 **Terminal / File / Coding** 工具，避免授權整個家目錄。先不要使用系統管理員權限。

**Prompt 1｜最基礎的 Coding**

> 請只在目前的 `agent-lab` 工作目錄內建立 `hello.py`。程式接受使用者輸入的名字，輸出「你好，名字」。建立完成後，請真的執行 `python hello.py`（可用適當方式提供測試輸入），回報終端執行結果與檔案位置。不要只貼程式碼，也不要修改其他檔案。

**Prompt 2｜資料分析與驗證**

> 在 `agent-lab` 內建立 10 筆模擬銷售紀錄 CSV（日期、品項、金額），再產生折線圖 PNG。請實際執行程式並檢查兩個成品檔案是否存在。只回報檔名、執行結果、是否通過檢查；若失敗，先修正一次再說明。

**檢核：**必須看見工具執行紀錄、真實檔案，以及執行成功訊息。若只回傳「我已完成」，卻沒有檔案，是未完成。可以從 `qwen3.5:4b` 切換成 9B，使用完全相同 Prompt 比較成功率。

## B. Browser Automation：建議先測，不必先安裝 Playwright

Hermes 官方 Browser Automation 的預設路線是 **Browser Use CLI / 本機管理的 Chromium**；官方表示這個 Python browser driver 隨 Hermes 安裝，瀏覽器本體可由工具設定安裝。**不是每次都必須額外 `pip install playwright`**。Playwright 是其他 Skill（例如 Pixel2Motion）的依賴時才另裝。

設定流程：

1. Hermes Desktop → **Settings → Tools** → 開啟 **Browser Automation**。若提示下載 Chromium／Browser driver，照 UI 提示完成。
2. 若使用 Hermes CLI，可執行 `hermes tools`，在 Browser Automation 選**本機**，不要選 Browser Use Cloud、Browserbase、Firecrawl 等會要求帳號／API Key 的雲端服務。
3. 先測不需要登入、可公開瀏覽的網頁。若文字型 accessibility tree 足夠，不必先開 Vision screenshot。

**Prompt 3｜網頁操作**

> 使用 Browser Automation 開啟 https://example.com，讀取頁面標題與第一段文字，回報你實際使用的工具及讀到的內容。不要只依模型記憶回答。完成後請顯示該網頁的可核對結果。

**Prompt 4｜表單輸入（只限本機測試網頁）**

> 請在我指定的本機測試頁面進行表單填寫，使用假姓名及假電子郵件。填寫完先截圖或回報欄位，不要按最後的 Submit，直到我確認。

### 想使用電腦上已安裝的 Google Chrome

Hermes CLI 支援 `/browser connect`，會**嘗試自動尋找／啟動** Chrome、Brave、Chromium、Edge 的 CDP 連線；這是互動 **CLI 指令，不是 Hermes Desktop 聊天框的文字命令**。

```text
/browser connect
/browser status
/browser disconnect
```

若想明確指定使用自己的 Chrome，需要允許獨立的遠端除錯 Profile。Chrome 136+ 不允許把遠端除錯直接掛在一般預設個人 Profile，因此不要讓學生為了測試去開自己的主要瀏覽器登入 Profile。先用 Hermes 自帶 Chromium 是最小、較安全的作法。Chrome 操作可能需要使用者操作許可與本機瀏覽器安裝版本支援。

## C. Computer Use：不是 Browser Automation 的另一個名字

Computer Use 操作**本機桌面應用程式**（如文字編輯器、檔案管理員）。官方整合 `cua-driver`，支援 macOS、Windows、Linux；工具是 Hermes 本機執行，**不會操控 Colab T4 的圖形桌面**。

可先在 Desktop → Tools 啟用 **Computer Use**；若工具缺失，使用 CLI：

```bash
# EN: Install the Hermes built-in desktop-control driver.
# 繁中：安裝 Hermes 內建的桌面操作驅動程式。
hermes computer-use install

# EN: Verify driver readiness and permissions.
# 繁中：確認驅動程式與權限是否正常。
hermes computer-use doctor
```

- Windows：安裝時一般不需要額外授權，但需在有桌面工作階段的本機操作。
- macOS：需在系統設定授予所需的**輔助使用與螢幕錄製**權限，授權實際顯示的 `CuaDriver` 身分。
- Ubuntu：需可使用圖形顯示伺服器，X11 `DISPLAY` 或 Wayland／XWayland 條件須滿足；純 SSH headless 環境通常不適合此課。

**Prompt 5｜Computer Use**

> 只使用已啟用的 Computer Use 工具，在本機開啟系統的文字編輯器，輸入「這是 AI Agent 的桌面操作練習」，儲存到 `agent-lab/computer-use-test.txt`。請先回報可用的工具與偵測到的應用程式；如果無法操作，明確說明是哪個權限或驅動有問題，不要宣稱已完成。不要切換到瀏覽器自動化假裝完成。

**需要看截圖的操作**選 `qwen3.5:9b` 這類 Vision 模型較合理；若 accessibility tree 文字可讀，4B 也可以測，但模型有 Vision 標籤不等於 Computer Use 一定成功。

## D. 比較表與公平測試方式

同一任務、相同工具授權及相同時間限制，分別使用 `qwen3.5:4b` 與 `qwen3.5:9b`。每次實際檢查：

| 項目 | 成功判準 |
|---|---|
| Tool Calling | 有具體工具呼叫與回傳，不只是敘述 |
| Coding | 生成檔案且實際執行成功 |
| Browser | 讀到指定網址的即時內容 |
| Computer Use | 桌面上可核對操作結果，位置正確 |
| 安全 | 沒越權、沒有無限制重試或洩漏隱私 |
| 資源 | 沒 OOM，延遲符合課堂需求 |

### 參考
- [Ollama Qwen 3.5](https://ollama.com/library/qwen3.5)
- [Ollama Qwen 3](https://ollama.com/library/qwen3)
- [Ollama GPT-OSS](https://ollama.com/library/gpt-oss)
- [Ollama Qwen3-Coder](https://ollama.com/library/qwen3-coder)
- [Hermes Browser Automation](https://hermes-agent.nousresearch.com/docs/user-guide/features/browser)
- [Hermes Computer Use](https://hermes-agent.nousresearch.com/docs/user-guide/features/computer-use)
