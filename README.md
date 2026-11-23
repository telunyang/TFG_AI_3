# 人工智慧技術應用實作班

本課程以高中生為對象，從**機器學習、模型評估及 BERT 文字分類**出發，延伸至**網頁資料擷取、對話式 AI、圖片／影片／音樂生成**，最後透過 **AI Agent 專題**練習需求分析、工作流程設計與 Flask 網站開發。

教材依 `01`～`07` 分為七個主題，包含互動式 HTML 教材、Jupyter Notebook、Python 範例、提示詞與專題規劃工具。各單元的教材形式不同，**不是每個資料夾都有 HTML 投影片或可直接執行的完整專案**。

## 課程目標

- 理解資料前處理、模型訓練、分類、評估與模型微調的基本流程。
- 學習使用 Python 擷取網頁資料、整理資料表並輸出 Excel。
- 體驗 Gemini／Ollama 對話 API、多輪記憶與 Excel BM25 檢索增強。
- 操作圖片、影片、音樂生成模型，理解 GPU 環境與選用的遠端 API 串接。
- 從自然語言需求規劃 AI Agent，確認 JSON 工作流程後，再使用 AI 輔助開發 Flask 專題。

## 課程大綱

| 單元 | 教學主題 | 主要教材 |
| --- | --- | --- |
| [01](01/) | 機器學習與模型訓練 | HTML 投影片、2 份 Notebook、500 筆練習資料 |
| [02](02/) | 資料預測與模型實作 | HTML 投影片、2 份 Notebook、500 筆校園郵件資料 |
| [03](03/) | AI 分類模型應用 | HTML 投影片、2 份 BERT Notebook、評論語料 |
| [04](04/) | 網頁爬蟲與資料擷取 | HTML 教學投影片、LINE 貼圖／YouTube Notebook |
| [05](05/) | 對話式 AI 與 Excel BM25 檢索增強 | Gemini／Ollama 單輪程式、兩階段開發 Prompt |
| [06](06/) | 多模態生成式 AI | 7 組模型 Notebook 與對應 Python Client |
| [07](07/) | AI Agent 專題規劃與開發 | 需求表、流程規劃 Prompt、HTML 預覽器、Flask 開發 Prompt |

### 01｜機器學習與模型訓練

使用模擬小考與學習紀錄資料，從資料清理開始，學習訓練集／測試集、迴歸預測、MSE、R²，以及二元分類、Accuracy、正則化與 K-means 等概念。

- **第 1 節**：資料前處理與線性迴歸，預測小考分數。
- **第 2 節**：預測是否及格，並選做非監督式分群。
- **教材**：`01_機器學習與模型訓練.html`、`01_第1節_資料前處理與迴歸.ipynb`、`01_第2節_分類正則化與非監督學習.ipynb`、`01_機器學習_學生練習資料_500筆.csv`。

### 02｜資料預測與模型實作

以 500 封模擬校園郵件為例，練習建立分類模型，判讀混淆矩陣、Precision、Recall 與 F1-score，並認識資料洩漏、決策樹、隨機森林、SVM、交叉驗證和 Grid Search。

- **第 1 節**：分類指標、決策樹與資料洩漏。
- **第 2 節**：隨機森林、SVM、交叉驗證與超參數搜尋。
- **教材**：`02_資料預測與模型實作.html`、`02_第1節_分類指標與決策樹.ipynb`、`02_第2節_隨機森林SVM與GridSearch.ipynb`、`02_校園郵件分類_500筆.csv`。

### 03｜AI 分類模型應用

以中文文字為素材，認識 Tokenizer、Transformer 與 BERT。第一節使用既有模型進行遮罩填空及情緒分類；第二節使用臺灣繁體中文評論語料進行 BERT 正負評二元分類微調，觀察訓練、驗證、Checkpoint 與最佳模型。

- **第 1 節**：BERT 遮罩填空與現成情緒分類模型推論。
- **第 2 節**：`reviews.txt` 資料切分、BERT 微調、評估與模型儲存。
- **教材**：`03_AI分類模型應用.html`、`03_第1節_BERT遮罩填空與情緒分類.ipynb`、`03_第2節_BERT二元分類微調.ipynb`、`reviews.txt`。
- **注意**：微調 Notebook 需要額外安裝其指定套件，並依 Notebook 說明準備語料與 GPU 環境。

### 04｜網頁爬蟲與資料擷取

從 HTML 元素階層與 CSS Selector 開始，學習 `requests`、`BeautifulSoup`、`Selenium`、動態網頁等待及資料擷取。透過兩份 Notebook 觀察實際網頁資料的取得與整理方式。

- **互動投影片**：HTML 標籤／屬性、CSS Selector、HTTP、靜態與動態網頁擷取。
- **LINE 貼圖範例**：`line-stickers.ipynb`，解析貼圖頁面並下載圖片。
- **YouTube 範例**：`youtube.ipynb`，使用 Selenium 搜尋及擷取影片資訊，輸出 `youtube.xlsx`；另有選用的影片下載示範。
- **教材**：`教學投影片.html`、`line-stickers.ipynb`、`youtube.ipynb`。
- **注意**：外部網站的頁面結構可能改變，實作時須遵守網站規範、著作權與合理存取頻率。

### 05｜對話式 AI 與 Excel BM25 檢索增強

可選擇 `gemini/` 或 `ollama/` 教材，先體驗單輪對話，再透過 AI 平台分兩階段產生 Flask 聊天網站。**ZIP 提供的是 Python 範例與生成專案的 Prompt，不是已建置完成的 Flask 網站。**

1. **第一階段｜多輪對話**：將 `Flask_專案產生Prompt.md` 和所選模型的 `*_single_turn.py` 一起上傳至 AI 平台，產生支援 `history.json` 對話記憶的 Flask 專案。
2. **第二階段｜檢索增強**：回到同一個 AI 對話，上傳 `Excel_BM25_檢索增強Prompt.md` 與自己的 `.xlsx`，產生可使用 Excel BM25 檢索的更新版 Flask 專案。

- **Gemini 教材**：`gemini_single_turn.py`、兩份 Prompt、`requirements.txt`、`.env.example`、`check_models.py`；需自行設定 `GEMINI_API_KEY`。
- **Ollama 教材**：`ollama_single_turn.py`、兩份 Prompt、`requirements.txt`；需準備可連線的本機或遠端 Ollama 模型服務。
- **操作說明**：請先閱讀 [`05/流程.txt`](05/流程.txt)。產生後的 Flask 專案，依其自己的 `requirements.txt` 與 README 安裝、執行。

### 06｜多模態生成式 AI

提供七組生成模型教材。**每一組都有 `.ipynb`（模型安裝、載入、生成、預覽）與對應的 `_client.py`（選用的遠端 API 呼叫範例）**。Notebook 內含 GPU／模型參數設定，部分模型使用 ComfyUI 或其他推論環境；另提供選用的 ngrok 與 FIFO 遠端 API 操作。

| 類型 | 模型 | Notebook 主要任務 |
| --- | --- | --- |
| 圖片 | Z-Image-Turbo | 文字生成圖片 |
| 圖片 | Qwen Image 2.1 | 文字生圖、單圖編輯、多圖參考 |
| 影片 | LTX-2.5 | T2V、I2V、FLF2V |
| 影片 | MiniMax H3 | T2V、I2V、L2VA、FLF2V、R2V |
| 影片 | HyperFlow H3 Flash | T2V、I2V、L2VA、FLF2V、R2V |
| 音樂 | HeartMuLa | 音樂生成、試聽與下載 |
| 音樂 | YuE2 | 音樂生成、試聽、樂譜與下載 |

請進入對應模型資料夾，先執行 Notebook 的環境安裝與模型載入，再設定生成參數；需要由其他程式呼叫時，才使用選用的遠端 API 與 Python Client。模型權重及部分套件須在執行時另外下載，生成速度與可用模式取決於 GPU 資源及 Notebook 設定。

### 07｜AI Agent 專題規劃與 Flask 開發

這個單元採用「**需求表 → AI 產生流程 JSON → HTML 預覽與修改 → AI 輔助產生 Flask 專題**」的方式進行。資料夾內有四份教材：

1. **`01_專案需求表.docx`**：填寫專題需求與預期功能。
2. **`02_AI流程規劃與修改.md`**：與需求表一起交給 AI，產生 `AI_Agent_流程設計.json`；後續也可提供最新 JSON 與修改需求，調整既有流程。
3. **`03_AI工作流程預覽.html`**：在瀏覽器匯入 JSON，檢視 Agent、Function Tool 和彼此的工作關係；可拖曳節點、調整視覺布局並下載更新的 JSON。**此 HTML 是離線流程預覽工具，不會實際執行 Agent 或網頁爬蟲。**
4. **`04_Flask專案開發.md`**：流程確認後，將最終 JSON 與此 Prompt 一起提供給有程式開發能力的 AI 平台，生成實際的 Flask 專題程式與使用介面。

專題可依需求選用 Excel BM25、即時網頁檢索（`ddgs` 搜尋列表 → `requests`／`Playwright` 擷取正文）、`web_cache.xlsx` 快取，以及第 06 單元的多模態遠端 API。**這些是第 07 單元的規劃與開發規格；是否能運作，仍取決於後續生成的 Flask 程式、模型／API 連線及實際測試。**

## 環境與執行方式

### Python 環境

建議先安裝 [Anaconda／Miniconda](https://www.anaconda.com/download/success)，在專案根目錄執行：

```bash
conda create -n ai python=3.13 ipykernel -y
conda activate ai
python -m pip install -r requirements.txt
```

根目錄 `requirements.txt` 收錄本專案共用的資料分析、網頁擷取、對話 API 與 Agent 開發套件。個別 Notebook 若有額外的安裝 Cell 或模型相依套件，仍需依該教材執行；第 05 單元 AI 生成的 Flask 專案，也應使用其專屬 `requirements.txt`。

### 教材使用建議

- **HTML 教材**：直接用瀏覽器開啟相應 `.html`；第 07 單元需先取得流程 JSON 才能匯入預覽。
- **Jupyter Notebook**：使用 VS Code／Jupyter 或教材適用的 GPU 執行環境，依序執行 Cell；有些練習需要先填入範例程式。
- **CSV／TXT 資料**：依 Notebook 指示放在指定資料夾或上傳至執行環境。
- **API 金鑰**：使用本機 `.env` 或安全的環境變數管理；不要把真正的金鑰寫入 Prompt、JSON 或公開的版本控制儲存庫。

### Colab 與遠端 Ollama（選用）

`colab/` 提供相關補充工具：

- `Colab_Ollama_ngrok.ipynb`：在 Colab 安裝／啟動 Ollama、下載與載入指定模型、設定 ngrok 並測試遠端 API。
- `ollama-ngrok.yaml`：供 ngrok 使用的 Traffic Policy 設定範例。
- `Hermes_Desktop_Windows.md`：Windows 上 Hermes Desktop／Gateway 相關命令備忘。

以上工具可協助遠端模型連線，**不是第 07 單元 AI Agent 專題規劃的必要步驟**。對外公開 Ollama 或生成 API 時，應留意端點存取權限，不要將私人端點或金鑰直接放入公開文件。

## 其他檔案

- `機器學習_參考筆記.pdf`：機器學習參考資料。
- `.gitignore`：版本控制排除規則。

> **提醒：** `.ipynb`、Prompt、HTML 流程預覽器及 Python Client 各有不同用途；有些檔案提供教學示範或專案生成指令，不表示模型、遠端 API 或 Flask 網站已在 ZIP 中部署完成。
