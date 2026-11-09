# 05｜大型語言模型應用（12 頁 CMD 實作版）

本單元以約 12 歲的學生為對象，先在 **Windows CMD 執行兩支單輪問答程式**，再把兩支 `.py` 上傳 ChatGPT，請 AI 依照 `Flask_專案產生Prompt.md` **自動產生 Gemini 與 Ollama 兩個獨立的 Flask 多輪聊天網站**。重點是動手操作和測試，不需要先學會 Flask 或語言模型的數學理論。

## 檔案

- `05_大型語言模型應用.html`：12 頁互動投影片；每節 5 頁教學 + 1 頁三題練習。
- `gemini_single_turn.py`：Gemini 單輪問答；API Key 放 `.env`。
- `ollama_single_turn.py`：Ollama 單輪問答；可使用本機或老師的遠端服務。
- `Flask_專案產生Prompt.md`：上傳兩支 `.py` 後，貼給 ChatGPT 的**完整產生專案指令**；附三種後續修改 Prompt 範例。
- `.env.example`、`requirements.txt`、`.gitignore`：Python 執行環境所需的簡單設定。
- `ollama-ngrok.yaml`：原本的 ngrok 設定範例，老師如有遠端模型才需要。

**沒有 Notebook，也沒有預先幫學生生成 Flask 成品。** 第二節的目標就是讓學生上傳程式，體驗用 Prompt 產出專案。

## 第一節｜CMD 執行單輪程式（第 1–6 頁）

1. 把教材解壓縮，在 `05` 資料夾的檔案總管網址列輸入 `cmd`，按 Enter 開啟 CMD。
2. 安裝需要的套件：

   ```bat
   python -m pip install -r requirements.txt
   ```

3. **Gemini：**把 `.env.example` 複製成 `.env`，在 `GEMINI_API_KEY=` 後面填入自己的金鑰，接著執行：

   ```bat
   python gemini_single_turn.py
   ```

4. **Ollama：**先確認 Ollama 服務正在運作。如果使用本機模型，先下載來源程式所用模型；若使用老師的遠端 Ollama，先將程式 `host` 修改成提供的 HTTPS API 根網址。接著執行：

   ```bat
   ollama pull gemma4:e2b
   python ollama_single_turn.py
   ```

   使用**遠端**模型且老師已準備好模型時，不需要在自己的電腦執行 `ollama pull`。網址不要加 `/v1` 或 `/api/chat`。

5. 找到來源程式裡的問題文字，修改成自己想問的問題，再次執行。Gemini 與 Ollama 可以擇一實作，不必兩個都成功才可進入下一節。

若 CMD 顯示找不到 `python`，請確認 Python 已安裝並設定 PATH；若 Gemini 顯示配額、金鑰或網路錯誤，請先檢查對應設定。不要將 `.env` 上傳 ChatGPT。

## 第二節｜上傳兩支 .py，產生兩個多輪網站（第 7–12 頁）

1. 開啟 ChatGPT 新對話，同時上傳 `gemini_single_turn.py`、`ollama_single_turn.py`。
2. 開啟 `Flask_專案產生Prompt.md`，複製「開始複製」到「結束複製」之間的完整 Prompt 並送出。
3. ChatGPT 應產生一個可下載 ZIP，解壓縮後直接有 `gemini_flask/`、`ollama_flask/` **兩個獨立資料夾**，各自都有 `app.py`、`templates/index.html`、`requirements.txt`、`README.md`。
4. 依產生專案中的 `README.md`，在 CMD 分別安裝並啟動。Gemini 使用 `http://127.0.0.1:5000`；Ollama 使用 `http://127.0.0.1:5001`。
5. **實際驗證**第二輪是否記得前一句、重新整理是否還有聊天紀錄、清除是否有效、斷線時是否有清楚提示。
6. 再選擇 `.md` 後面的「改外觀、改文字、增加簡單功能」Prompt，練習如何在**維持原有功能**的前提下修改網站。

### 投影片說明

HTML 投影片離線可開啟。使用 `←`／`→` 換頁，`G` 跳頁；互動範例與網頁畫面均為**離線示意**，不會真的呼叫 Gemini 或 Ollama。第 6、12 頁各有 3 題，直接在投影片選答案。

### 教師備註

`example.zip` 裡的 Gemini Flask 範例可作為設計參考，但本教材的 Prompt **以學生上傳的兩支來源 `.py` 為準**。不直接沿用 `example.zip` 的模型名稱、API Key 變數、原始較窄的聊天版面。學生只需要理解「這次問什麼、歷史有沒有帶上、網站能不能正常運作」，其他細節可以放到後續課程。
