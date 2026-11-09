# 05｜上傳兩支 Python 程式，產生兩個 Flask 多輪聊天網站

本檔提供可以直接貼給 ChatGPT 的 **完整 Prompt**。教學重點是：學生先在 Windows CMD 執行原本的單輪 Python 程式，再讓 ChatGPT 將它們改造成多輪聊天網頁。

## 學生怎麼使用

1. 開啟 ChatGPT 對話，**同時上傳** `gemini_single_turn.py` 與 `ollama_single_turn.py`。
2. 把下方「**開始複製：產生兩個 Flask 專案**」到「**結束複製**」的內容貼到同一段對話，送出即可。也可以將本 `.md` 一併上傳並要求完整執行該區塊。
3. 下載 ChatGPT 產生的 ZIP 並解壓縮，應直接看到 `gemini_flask/` 和 `ollama_flask/` **兩個獨立資料夾**。
4. 依各自的 `README.md` 使用 CMD 安裝、啟動，並在瀏覽器測試。

不要上傳 `.env`、真正的 API Key，或任何包含金鑰的檔案。`example.zip` 是教師參考範例；**學生不必上傳 `example.zip`**，上傳兩支 `.py` 就夠了。

---

## 開始複製：產生兩個 Flask 專案

我上傳了兩支已用於**單輪問答**的 Python 程式：

- `gemini_single_turn.py`
- `ollama_single_turn.py`

**請直接讀取兩個上傳檔案並完成整個工作，不要只給程式片段、資料夾示意圖或操作建議。** 你要真的建立兩個 Flask 專案資料夾，寫出所有實體檔案，測試可以檢查的功能，再打包成可下載的 ZIP。

### 1. 目標與原則

把 `gemini_single_turn.py` 改造成 Gemini 的多輪聊天網站，把 `ollama_single_turn.py` 改造成 Ollama 的多輪聊天網站。兩者**各自獨立**：不可把模型做成一個網站裡的切換選單，也不要共用聊天歷史或設定檔。

- 使用上傳的兩支 `.py` 作為**模型名稱、SDK、system instruction、生成參數、Ollama host／timeout／keep_alive／think** 的真正依據。不要猜測模型版本，不要將任何模型默默改成另一個。
- 保留原本的模型與設定；如果當前服務回報模型不支援某參數，要顯示清楚錯誤，不要擅自移除設定。
- 對象約 12 歲，程式要簡單、可閱讀、容易修改，以 **能正常執行** 為首要目標。
- 不需要 Docker、React、Vue、資料庫、登入系統、WebSocket、ORM、前端編譯、額外設定模組，或不必要的檔案與套件。
- 網頁全部使用**臺灣繁體中文**。

### 2. 一定要產生這兩個資料夾

請交付 **`05_Flask_多輪聊天網站.zip`**，解壓縮後的頂層直接有這兩個資料夾，不要只交一個 Python 檔：

```text
05_Flask_多輪聊天網站.zip
├── gemini_flask/
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   ├── README.md
│   └── templates/
│       └── index.html
└── ollama_flask/
    ├── app.py
    ├── requirements.txt
    ├── .gitignore
    ├── README.md
    └── templates/
        └── index.html
```

產生的 ZIP **不得**包含 `.env`、API Key、真實聊天紀錄、`.venv`、`__pycache__`、安裝後的套件或無關圖片。`chat_history.json` 由網站**第一次成功對話後**自動建立，放在各自的專案資料夾，必須加入 `.gitignore`。

### 3. 後端：沿用來源程式，實作真正多輪對話

**Gemini (`gemini_flask/app.py`)**

- 使用來源檔案相同的 `google-genai` SDK：`from google import genai`、`from google.genai import types`、`genai.Client(...)`。
- 保留來源的模型名稱（目前來源是 `gemini-3.5-flash-lite`）、system instruction、`temperature=1.0`、`top_k=64`、`top_p=0.95`；由 `types.GenerateContentConfig` 傳入。
- 從專案旁邊 `.env` 取得來源使用的 `GEMINI_API_KEY`，以 `python-dotenv` 載入；如果缺少金鑰，顯示友善錯誤，**絕對不能**寫死金鑰、傳給前端或輸出到網頁。
- 真正使用 `client.models.generate_content_stream(...)` 或 SDK 的等效**原生串流**方法。
- 多輪 `contents` 依序含舊的 `user` 與 `model` 訊息，再加上這次的 `user` 問題；system instruction 仍放在 `GenerateContentConfig`，不要每輪重複塞入歷史。**Gemini 的回答角色是 `model`，不是 `assistant`。**

**Ollama (`ollama_flask/app.py`)**

- 使用來源相同的 `ollama.Client` 與 `client.chat(...)`，保留 `host`、`timeout`、模型 `gemma4:e2b`、system 訊息、`keep_alive="1h"`、`think=False` 與 `options` 參數，並開啟 `stream=True`。
- `host` 預設來源值是 `http://localhost:11434`。老師要使用 Colab + ngrok 時，只需修改 `app.py` 最上方的 `OLLAMA_HOST`，使用 `https://...ngrok-free.app` 這種 **API 根網址**，**不要**加 `/v1`、`/api/chat`。
- 多輪 `messages` 包含一筆 `system`，再依序放歷史中的 `user`、`assistant`，最後加上新 `user` 問題。不要在每次請求重複多筆 system。
- Ollama **不需要 Gemini 金鑰**，不要加上 `.env` 或 API Key 表單（除非來源檔案確實要求額外認證）。

**兩個網站共同遵守**

- 只供**本機單人教學**，每個專案自己的 `chat_history.json`（UTF-8，`ensure_ascii=False`）可在重新整理、重啟後恢復歷史；不要實作多人帳號。
- 聊天歷史由 Flask 後端讀寫；瀏覽器只傳送這次輸入的文字，不能讓前端自己決定要提交哪份舊歷史。
- 模型**完整回答成功**後才儲存本輪的 user 與 assistant（Gemini 可在儲存時用 `model` 角色）。如果請求失敗、串流中斷、回覆為空，**不可把這輪對話寫進歷史**。
- 使用一個簡單的 `threading.Lock` 保護本機歷史檔案的讀寫及同一時間的對話／清除操作；不要引入外部資料庫。清除後要真正刪除後端歷史。
- 請把模型名稱、system instruction、生成參數與 Ollama host 集中在 `app.py` 上方，讓學生容易找到並透過 Prompt 修改。
- `app.py` 只監聽 `127.0.0.1`、`debug=False`；Gemini 使用 `5000`，Ollama 使用 `5001`，兩個網站可同時啟動。

### 4. 網站外觀：參考簡單聊天介面，但改成「大畫面、大字體」

風格以簡潔、明亮、好閱讀為主，**不要為了炫技犧牲操作**。

- 桌面版聊天主容器寬度約 `min(1200px, 94vw)`（**不要限制在原本範例的 800px**），聊天記錄區高度約 `65vh`，讓畫面真正寬大；手機上能自動縮成單欄。
- 主要對話文字至少 **18px**，輸入框至少 **18px**，標題約 **26–30px**，按鈕至少 **16px**；足夠大的點擊區域。
- 頁面最上方用大字顯示 `Gemini 聊天室` 或 `Ollama 聊天室`，下方只需「對話內容、輸入區、送出、清除聊天」四個主要部分。
- 使用者與 AI 訊息用兩種顏色的泡泡區分；文字長時可換行，不要出現橫向捲動。
- `Enter` 送出、`Shift+Enter` 換行；使用 `<textarea>`；送出後等候 AI 時停用送出按鈕，並顯示「正在回答…」。
- **真正逐段顯示** SDK 串流產生的文字，不可先等完整回覆再用計時器假裝逐字出現。
- `重新整理` 後從 `/api/history` 恢復舊對話；`清除聊天` 要先確認，再呼叫後端清除；具備複製 AI 回答按鈕即可，不需要其他花俏功能。
- 後端錯誤以易懂文字告訴學生，例如「API Key 未設定」「模型未下載」「無法連到 Ollama」「API 額度不足」；不要把敏感金鑰或原始 traceback 顯示給使用者。
- 用 DOM `textContent` 顯示模型文字，**不要把模型回覆直接當 HTML 執行**。
- CSS 和 JavaScript **直接放進**各自的 `templates/index.html`，不要再新增 CSS/JS 套件或子資料夾。

### 5. API 與串流通訊（請確保前後端一致）

兩個專案都使用相同、易懂的路由：

| 方法 | 路由 | 用途 |
|---|---|---|
| GET | `/` | 開啟聊天室 |
| GET | `/api/history` | 讀取舊對話 JSON |
| POST | `/api/chat/stream` | 接收 `{"message":"..."}`，逐段傳回 AI 回答 |
| POST | `/api/clear` | 清除後端歷史 |

為了讓錯誤也能在串流中正確顯示，建議 `/api/chat/stream` 回傳 **NDJSON**（每行獨立 JSON），分別是：

```text
{"type":"chunk","text":"你好"}
{"type":"chunk","text":"！"}
{"type":"done"}
```

若失敗則回傳 `{"type":"error","message":"..."}`，而且不寫入該輪歷史。前端用 `fetch`、`ReadableStream` 和 `TextDecoder` 讀取，**必須保留尚未接收完整的一行作為緩衝**，不可假設網路 chunk 剛好等於一行 JSON。當收到 `done` 時才視為成功；如果讀取中止或沒有 `done`，顯示錯誤並重新載入後端歷史，避免畫面與硬碟不同步。

### 6. CMD 使用說明（寫在兩份 README 裡）

每個專案都用非常簡單的 Windows CMD 指令說明：

```bat
cd gemini_flask
python -m pip install -r requirements.txt
python app.py
```

Gemini 要先將 `.env.example` 複製成 `.env`，並填入 `GEMINI_API_KEY`。Ollama 的 README 要說明如何先啟動 Ollama、`ollama pull gemma4:e2b`，及如何將 `OLLAMA_HOST` 改為老師提供的 ngrok 根網址。

啟動後 Gemini 網址為 `http://127.0.0.1:5000`，Ollama 網址為 `http://127.0.0.1:5001`。寫明按 `Ctrl+C` 可以停止服務。每份 README 都用 5–8 個操作步驟，讓初學者可以照著做。

### 7. 驗證後才交付

- 確認 ZIP 中**真的存在**兩個完整資料夾、各自的 `app.py`、`templates/index.html`、`requirements.txt`、`README.md`。
- 檢查兩份 `app.py` 的 Python 語法、Flask 路由與 HTML 的 fetch 路徑。
- 不依賴真實 API 的情況下，用模擬模型回覆測試：連續問兩輪是否帶歷史、串流中途失敗是否不存半段內容、重整後是否保留、清除後是否刪除、錯誤是否可見。
- **如果你實際可以使用 API Key 或 Ollama 服務，再測試真實連線；若沒有，必須明確告知尚未實測真實模型，不能把模擬測試寫成真實測試。**
- 交付 ZIP 下載連結，簡短說明每個資料夾如何啟動及檢查結果，**不要要求我先補充資訊，也不要只交程式碼文字**。

### 8. 程式碼易讀性

- Python 程式盡量少用抽象類別或層層包裝，只保留真正必要的函式。
- **每一行可執行的 Python 程式碼上方**，依序附上簡短英文用途註解與臺灣繁體中文用途註解；複雜邏輯才使用多行說明。CSS 和 JavaScript 使用少量有意義的註解即可，避免大量重複說明。
- 不要為了達成範例功能而額外設計使用者系統、聊天機器人平台或複雜樣板架構。

**現在直接開始產生、檢查並打包所有實體檔案。**

## 結束複製

---

## 第二次修改：學生可直接使用的 Prompt 範例

網站能正常聊天後，可以**把 ChatGPT 產生的 ZIP 再上傳至原對話**，選一個要求修改。每次只改一件事，改完再測試多輪與歷史。

**範例 A：改外觀**

> 請保留兩個 Flask 網站的所有聊天功能、模型、歷史紀錄、API 路由與檔案結構，只把兩個網站改成深色風格，文字放大為 20px，訊息泡泡更圓一點。重新打包 ZIP 供我下載。

**範例 B：改網站文字**

> 請只把 Gemini 的網站標題改成「我的學習小助手」、輸入框提示改成「想問什麼？請在這裡輸入」，Ollama 網站不要修改。維持所有連線和多輪功能，更新 ZIP。

**範例 C：增加簡單功能**

> 請幫兩個聊天網站增加「清空輸入框」按鈕，位置在送出按鈕旁邊。原有的「清除聊天紀錄」要保留且兩者功能不同。不要增加任何 Python 套件，修改後重新測試並提供 ZIP。

**教師提醒：**先測試聊天能用，再讓學生透過 Prompt 修改文字、顏色、排版或一項小功能；切勿一開始就加入太多複雜需求。
