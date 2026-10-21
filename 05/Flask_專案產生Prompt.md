# 05｜用單輪 Python 範例產生 Flask 多輪聊天網站

請先閱讀我提供的 `ollama/single_turn.py`、`gemini/single_turn.py`（Gemini 另附 `.env.example`），將它們改成**兩個互相獨立**、可在本機執行的 Flask 多輪聊天室，最後打包為 `05_Flask_多輪聊天_教學套件.zip`，提供下載連結。

**請以目前的 `.py` 為準**，不要依照舊 README 虛構設定變數；這是高中生教材，請維持原本簡單、直觀的寫法。

## 1. 保留現有模型呼叫方式

- **Ollama：**沿用 `Client(host="http://localhost:11434", timeout=120)`、`gemma4:e2b`、原本的 system 訊息、`keep_alive="1h"`、`think=False`、`options`（`temperature=1.0`、`top_k=64`、`top_p=0.95`）。教師直接修改 `app.py` 內的 `host` 即可改用 Colab ngrok HTTPS **API 根網址**，不要附加 `/v1` 或 `/api/chat`。**不需要 Ollama `.env`。**
- **Gemini：**沿用 `google-genai`、`genai.Client`、`types.GenerateContentConfig`、`gemini-3.5-flash-lite`、原本的 system instruction 與三項生成參數。**只有 `GEMINI_API_KEY` 從 `.env` 讀取**（附安全的 `.env.example`）。模型或參數不支援時，顯示易懂的錯誤，不要默默換模型。
- **不要另外建立** `config.py`、`settings.py`、JSON／YAML 設定檔或複雜封裝；網址、模型、提示詞及生成參數直接寫在各自 `app.py` 上方，方便修改。

## 2. 網頁需要的功能

1. **真正的多輪對話：**每次提問都包含先前的問答。Ollama 使用 `messages`；Gemini 正確使用 `user`／`model` 角色及 `system_instruction`。
2. **歷史紀錄：**每個專案各有 `chat_history.json`，使用 UTF-8；重整網頁或重啟程式仍能延續對話。只有完整成功的回覆才儲存，失敗或中斷不存半截內容。
3. **聊天介面：**臺灣繁體中文、雙方訊息泡泡、Enter 送出／Shift+Enter 換行、生成中提示、**串流逐段顯示**、複製回答、清除聊天與歷史、重新開啟恢復紀錄，適合手機瀏覽。
4. **錯誤處理：**清楚提示 Ollama／ngrok 連不上、Gemini 金鑰錯誤、模型不可用等情況。不得在網頁顯示 API 金鑰；模型輸出以純文字安全呈現。

## 3. 專案保持精簡

請建立 `ollama_flask/` 和 `gemini_flask/`。每個專案只需要 `app.py`、`requirements.txt`、`templates/index.html`、`.gitignore`；CSS／JavaScript 可寫在同一個 HTML。Gemini 額外附 `.env.example`。ZIP 根目錄附簡短 `README.md`，說明安裝、啟動、修改 Ollama 網址與設定 Gemini 金鑰，以及歷史檔位置。

後端提供發送訊息、串流回覆、讀取歷史與清除歷史的 Flask 路由，前端必須真的可以操作。只使用 Flask、原本 SDK 和原生 HTML／CSS／JavaScript；**不要**資料庫、Docker、React、登入、額外設定檔或進階非同步框架。`app.py` 僅監聽 `127.0.0.1`，`debug=False`；`.gitignore` 排除 `.env`、`chat_history.json`。Python 盡量短、容易讀，重要段落使用「英文註解 → 臺灣繁體中文註解」。

## 4. 檢查與交付

實際建立所有檔案，檢查 Python 語法、前後端串接及安裝方式；以模擬回覆測試兩輪對話、串流中文、歷史恢復、清除與錯誤處理。沒有真實 API／Ollama 伺服器時，不可聲稱已完成連線測試。**交付可下載 ZIP，不要只有程式碼片段。**
