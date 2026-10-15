# 05｜請 AI 將 Ollama 與 Gemini 多輪聊天改成 Flask：完整提示詞

> 使用方式：將本提示詞**整份貼給支援建立／匯出檔案的 AI**，並一併附上 `ollama/multi_turn.py`、`gemini/multi_turn.py`、兩份 `.env.example`、`05_大型語言模型應用.html`。請不要上傳真實的 API 金鑰、ngrok authtoken 或對話歷史。

---

你是一名 Python／Flask 開發者，也是一名高中電腦課的老師。請**直接建立並提供可下載的 ZIP 專案**，將我提供的兩支**本機終端機多輪聊天程式**分別改成 Flask 網頁版，讓學生在本機以 `python app.py` 執行。

## A. 專案產物（必須完成，不只貼程式碼）

請輸出一個 `05_Flask_多輪聊天_教學套件.zip`，解壓縮後為以下結構：

```text
05_Flask_多輪聊天_教學套件/
├── ollama_flask/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   ├── templates/index.html
│   └── static/style.css
│   └── static/app.js
├── gemini_flask/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   ├── templates/index.html
│   └── static/style.css
│   └── static/app.js
└── README.md
```

如有檔案結構的簡化方式可採用，但**兩個 Flask 專案必須完全獨立**，可以在各自資料夾執行 `python app.py`，都能正常開啟 `http://127.0.0.1:5000`。請不要加入資料庫、前端框架、Docker、LangChain、登入系統或其他非必要依賴。**ZIP 不要放入真實金鑰或預先建立的私人對話歷史**。

## B. 模型 API 與對話歷史

**Ollama 版**

- 使用 `ollama.Client(host=OLLAMA_HOST, timeout=120)`，主機網址從 `.env` 讀取，預設 `http://localhost:11434`。教師會自行填入 Colab Ollama 的 ngrok HTTPS 網址；這是 **API 根網址**，不要自己附加 `/api/chat`。若 ngrok 需要繞過瀏覽器提醒，可在 Client 的 `headers` 設定 `ngrok-skip-browser-warning: true`。
- 在初始化 `Client` 時指定 `host` 即可，**不要在 `client.chat()` 再傳入 `host` 參數**。
- 預設 `OLLAMA_MODEL=gemma4:e2b`，但必須可由 `.env` 修改；模型必須已經存在遠端 Ollama 伺服器。
- 呼叫 `client.chat(model=..., messages=..., stream=True)`；每次傳送最新問題前，加入 System Prompt 和相關歷史（Ollama：`system`、`user`、`assistant`）。

**Gemini 版**

- 使用目前官方 `google-genai` SDK（`from google import genai`）；不要使用舊的 `google-generativeai` SDK。
- 從 `.env` 讀取 `GEMINI_API_KEY`，預設 `GEMINI_MODEL=gemini-3.5-flash-lite`，必須可自行修改。
- 使用 `client.chats.create(model=..., history=..., config=...)` 恢復歷史；使用 `send_message_stream()` 產生串流。Gemini 對話角色為 `user`、`model`；System Prompt 使用 `GenerateContentConfig(system_instruction=...)`。

**兩者共同要求**

- 各自在專案資料夾的 `chat_history.json` 儲存歷史，UTF-8、`ensure_ascii=False`、`indent=2`；重新開啟網頁或 Flask 程式時能接續。使用兩份原始程式的格式也可以，但前端 API 回傳格式須統一。
- 每次成功完成模型回答後才保存一組完整 `user`＋`assistant/model` 訊息；呼叫失敗或中途斷線時不能把不完整內容當成成功紀錄。
- `clear` 必須**同時清空 JSON 檔及接下來會送給模型的上下文**；不能只清除畫面而保留模型記憶。
- System Prompt 固定寫在 `app.py` 頂部或 `.env`，並在每次送出模型請求時套用；不要將 API 金鑰、伺服器網址或 System Prompt 暴露於網頁 HTML/JS。
- 僅供**單人本機教學**，JSON 不需要支援多人同時寫入；請避免 Flask debug/reloader 導致不必要的重複執行。只監聽 `127.0.0.1:5000`，預設 `debug=False`。

## C. 網頁功能（兩版外觀、互動一致）

1. 網頁上方顯示「LLM 多輪對話練習」，並標示目前服務 Ollama 或 Gemini（模型 ID 可以顯示）。
2. 左右或不同底色明確區分「使用者」與「AI」的訊息；支援長內容換行、行動裝置窄版排列、可捲動並自動捲至新訊息。
3. 頁面載入後向後端取得歷史並顯示；聊天紀錄要從後端取得，不靠瀏覽器 localStorage 當作唯一來源。
4. 有多行輸入框與「送出」按鈕；Enter 送出、Shift＋Enter 換行，空白問題不可送出。
5. 送出後立即在畫面顯示使用者訊息及「回應中…」狀態；模型串流文字時逐段顯示。處理中停用送出按鈕，避免連點；成功後恢復。
6. 有「清除對話／重新開始」按鈕，先確認再清除，畫面與 JSON 都要同步更新。
7. 每個 AI 回覆有「複製」操作，複製純文字即可；可以用瀏覽器原生 API。
8. 網路中斷、ngrok 逾時、模型 ID 錯誤、配額耗盡或 API 金鑰未設定時，必須顯示容易理解的錯誤訊息。失敗後仍可重試，不能錯誤地顯示「已完成」。
9. 介面不要用外部 CDN，HTML／CSS／原生 JavaScript 就好。文字要使用**臺灣繁體中文**，不要有簡體中文或中國用語。
10. 提供簡短提示：不要輸入個資；AI 答案可能錯誤，應自行查證。勿將歷史直接顯示給未授權者。

## D. Flask API 約定與串流

請在兩個專案實作相同路由與資料格式：

- `GET /`：回傳 `templates/index.html`。
- `GET /api/history`：回傳 JSON 陣列，元素包含 `role`（前端只需 `user`／`assistant`）與 `text`（訊息文字）。
- `POST /api/chat/stream`：接收 JSON `{"message":"..."}`，經過基本空字串驗證後呼叫對應模型，以 **Server-Sent Events（SSE）** 或另一種簡單且完整的 `fetch` 串流協定回傳增量文字；需用一致的 `delta`、`done`、`error` 事件格式區分狀態。
- `POST /api/clear`：清空歷史並回傳 JSON `{"status":"ok"}`。

前端必須正確解碼 UTF-8 串流，避免繁體中文被拆成亂碼；AI 回覆只能用 `textContent` 或安全等效方式顯示，不可把模型文字直接設成不受控的 `innerHTML`。HTTP 錯誤、串流錯誤都要讓前端顯示原因。路由命名與請求格式在兩版完全一致。

## E. 可讀的程式風格

- 盡可能少的程式碼；不要 class、list/dict comprehension、抽象工廠、複雜 wrapper、大量函式或不必要的 dependency。
- 相同性質的邏輯可放在一起；重要可編輯設定（MODEL_ID、SYSTEM_PROMPT、API URL）集中在上方。
- Python **每一行可執行程式的上方**，依序附簡短的英文註解、臺灣繁體中文註解，解釋意圖而不是重述語法。不同程式動作之間保留空白行；套件安裝指令與 import 不要混在同一個 Code Cell（若最後做成 Notebook）。
- 不要為了展示技巧改成 asyncio、背景任務佇列或新框架；保留目前 `ollama` 與 `google-genai` 官方 SDK 用法。
- CSS 可簡潔好看但不浮誇，應有足夠對比、文字區域不能溢出；HTML 及 JS 請使用清楚的語意命名。

## F. 生成、驗證、交付（必要）

請先閱讀全部附件；如果附件有程式錯誤，應修正並在說明中列出（例如 Ollama `client.chat()` 不接受額外 `host`）。不要原封不動複製錯誤程式。

建立所有程式檔後：

1. 檢查 Python 語法、Flask 路由、HTML／CSS／JS 靜態檔案與路徑。
2. 若可用測試環境，請以 mock 模型回覆檢查首頁、歷史恢復、連續兩輪聊天、清除、串流、錯誤顯示、重載瀏覽器後歷史仍保留。
3. 如果沒有實際 Ollama ngrok URL 或 Gemini API 金鑰，**不可虛稱已完成真實 API 連線測試**；清楚區分 mock 測試與真實 API 測試。
4. ZIP 裡附一份 `README.md`，包含：Miniconda 建立環境、每個專案 `pip install -r requirements.txt`、`.env.example` 改名 `.env`、ngrok／Gemini API 金鑰設定、`python app.py`、瀏覽器網址、`chat_history.json` 儲存位置、`clear` 與常見錯誤。
5. 最後**直接給我 ZIP 的下載連結**；若產物建立失敗，請如實說明，不要給假的下載連結。

請開始建立專案，不要只給架構或程式片段，不要要求我自行拼接檔案。必須保留兩個完全獨立、可在各自資料夾啟動的 Flask 專案。
