# 05｜大型語言模型應用：Python 單輪／多輪對話

這份教材只在**本機執行 Python**；Ollama 模型可在 Colab／遠端伺服器上，Gemini 則由 Google API 執行。**本機只需安裝 Python SDK，不必安裝 Ollama 模型或 GPU。**

## 1. 安裝 Miniconda 與 Python 套件

先從 [conda 官方下載頁](https://docs.conda.io/en/latest/) 安裝對應作業系統的 Miniconda：Windows 使用 Miniconda Prompt；macOS 與 Ubuntu 使用終端機。安裝後進入解壓縮的套件根目錄，執行：

```bash
conda create -n llm05 python=3.11 -y
conda activate llm05
python -m pip install -r requirements.txt
```

SDK：`ollama`、`google-genai`、`python-dotenv`；`pip install ollama` **不是**安裝 Ollama 伺服器。

## 2. Ollama + ngrok

已假設教師在遠端啟動 Ollama 並取得可連線的 ngrok HTTPS URL。**請先確認遠端 Ollama 已下載與執行指定模型。**

1. 將 `ollama/.env.example` 複製成同資料夾的 `ollama/.env`。
2. 將 `OLLAMA_HOST` 改成你的完整 ngrok 網址，例如 `https://xxxx.ngrok-free.app`（不要加入 `/api/chat`，也不要填寫 Colab 內的 `localhost`）。
3. `OLLAMA_MODEL` 要與遠端 Ollama 已安裝模型的 ID 相同，例如 `gemma4:e2b`。
4. 執行：

```bash
python ollama/single_turn.py
python ollama/multi_turn.py
```

如使用本機 Ollama 伺服器，可將 `OLLAMA_HOST=http://localhost:11434`。所附 ngrok Traffic Policy 會改寫 `Host` 標頭為 `localhost`；如果教師已設定認證，還須依該端點的要求補上身分驗證。**不要公開分享沒有保護的 Ollama ngrok URL。**

## 3. Gemini API

1. 在 [Google AI Studio](https://aistudio.google.com/apikey) 取得 Gemini API 金鑰。
2. 將 `gemini/.env.example` 複製成 `gemini/.env`。
3. 設定 `GEMINI_API_KEY`；預設模型為 `gemini-3.5-flash-lite`，也可修改 `GEMINI_MODEL`。能否存取視帳戶權限及配額而定。
4. 執行：

```bash
python gemini/single_turn.py
python gemini/multi_turn.py
```

## 4. 多輪對話操作

在兩支多輪程式中，輸入問題後按 Enter：

- `exit`：結束程式（歷史仍保留）。
- `clear`：清空目前對話與 `chat_history.json`。
- 每輪成功取得模型回答後，自動儲存成 **各自資料夾內的** `chat_history.json`；再次執行時會讀取舊紀錄。

Ollama 的角色是 `system/user/assistant`；Gemini 的歷史使用 `user/model`，並以 `parts` 保存文字。**兩種 JSON 格式不同，請勿混用。**System Prompt 不會寫入 JSON，而是每次建立請求時由程式提供。**模型會收到重新送出的歷史，但不會因此重新訓練。**

## 5. 學生建議實驗

1. 將單輪的問題改成：「請幫我規劃三天，每天 30 分鐘的英文複習。」
2. 多輪先問「我想去臺南玩一天，搭大眾運輸」，再問「改成雨天備案」，觀察前後文是否保留。
3. 在多輪程式輸入 `clear`，再單獨輸入「改成雨天備案」，比較回答。
4. 修改 `SYSTEM_PROMPT`、`MODEL_ID`／`.env` 內的模型名稱，比較風格與回覆差異。

## 6. 課堂注意事項

- 對話儲存在本機純文字 JSON，請勿輸入真實個資、證件號碼或機密內容；不要將 `.env` 或 `chat_history.json` 上傳至公開 GitHub。
- Gemini API 可能產生費用或受到配額限制；ngrok 連線也可能中斷。
- Python API 連線和模型正確性要分開檢查；模型回答必須自行查證。
- 四支程式刻意使用**非串流**回覆，避免初學者需要處理非同步程式；之後可使用 `Flask_專案產生Prompt.md` 讓 AI 建立具串流介面的完整網頁專案。

## 7. 對照已核對的官方文件

- [Ollama Python SDK](https://github.com/ollama/ollama-python)
- [Google GenAI SDK](https://googleapis.github.io/python-genai/)
- [Gemini 多輪聊天文件](https://ai.google.dev/gemini-api/docs/generate-content/text-generation)
- [Gemini 官方模型 ID](https://ai.google.dev/gemini-api/docs/models)
- [Miniconda 安裝](https://docs.conda.io/projects/conda/en/stable/user-guide/install/)
