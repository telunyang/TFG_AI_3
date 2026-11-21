# 第一階段｜Ollama 單輪對話改造成 Flask 多輪聊天網站

**這份 Markdown 的全部內容就是本輪要執行的正式 Prompt。使用者會同時附上本檔與 `ollama_single_turn.py`，可能不會另外輸入任何文字。請直接讀取兩份附件並開始製作專案；不要把本檔當成只需摘要的參考資料，也不要要求使用者重新貼上本文或再說「請開始」。** 若無法讀取任一必要附件，請明確指出缺少哪份；可以讀取時請直接完成程式、必要檢查與可下載的 ZIP。

這是 **Ollama Flask 教材的第一階段**。我已在這次對話中一起提供 `ollama_single_turn.py` 與 `Flask_專案產生Prompt.md`。請將單輪對話程式改造成可直接運作的 **Ollama Flask 多輪對話網站**，完成所有實體檔案、檢查與打包，並提供可下載的 `ollama_flask.zip`。**不要只回答設計概念、檔案示意或零散程式碼**。本次只處理 Ollama，不要建立其他模型網站，也不要提前加入 Excel/BM25。後續我會**在同一個 AI 對話中**，一起提交 `Excel_BM25_檢索增強Prompt.md` 與我的 `.xlsx`；如果學生漏傳 Excel，請下一則回覆先提醒補傳，收到後先分析工作表、欄位、值域與前 10～20 筆資料，再沿用這一階段產出的完整 Flask 專案繼續修改，而不是從零重寫。

## 一、技術及資料夾

- 後端使用 Python + Flask，前端使用單一 `templates/index.html`（HTML、CSS、原生 JavaScript、`fetch()`），**不使用** React、Vue、WebSocket、外部資料庫、登入、Docker、前端編譯工具或不必要的抽象層。
- 成品解壓縮後應有下列**單一獨立專案**：

```text
ollama_flask/
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
└── templates/
    └── index.html
```

- 以原始 `.py` 為模型設定的依據，不要猜測或替換模型。若指定模型或設定無法使用，**回報實際錯誤**，不得在未告知下切換其他模型、忽略參數或改用假資料。
- **唯一啟動入口是 `ollama_flask/app.py`**：在 Windows CMD 進入專案資料夾後執行 `python app.py` 就能啟動 Flask，不得要求另外執行 `flask run`、設定 `FLASK_APP`、執行 `run.py`、啟動前端開發伺服器、先執行初始化腳本或手動建立 `history.json`。請在 `app.py` 使用 `if __name__ == "__main__":` 啟動 Flask，並停用 debug/reloader 以避免重複啟動。
- 僅供本機單人教學。`app.py` 使用 `127.0.0.1:5001`、`debug=False`；自訂設定集中在 `app.py` 前面，易於讓高中生修改。

## 二、Ollama 模型的原始行為必須保留

- 以 `ollama_single_turn.py` 的 `ollama.Client`、`host`、`timeout`、模型名稱、system 內容、`keep_alive`、`think`、`options` 為唯一依據，不要換成另一種 SDK 或擅自更換模型。
- 使用原本的 `client.chat(..., stream=True)` **原生串流**，逐段傳給瀏覽器。多輪 `messages` 應只有一筆原來的 `system`，接著依序是舊的 `user`、`assistant`，最後是這次的 `user`，不能重複多筆 system。
- 將 `OLLAMA_HOST` 放在 `app.py` 最上方，預設保留來源的 `http://localhost:11434`，方便老師改成 `https://...ngrok-free.app` 這種 API **根網址**。不得在根網址後自行加 `/v1` 或 `/api/chat`。
- 本範例使用 Ollama 服務，不需要另加 API Key 表單。模型未下載、連線失敗或遠端 ngrok 無法使用時，要回傳清楚錯誤。

## 三、history.json：真正能記住前面的對話

- 每個網站使用自己的 `history.json`，路徑固定在專案根目錄；以 UTF-8、`ensure_ascii=False` 儲存。**只有第一次完整成功回答後才新增檔案**，不預先加入虛構的聊天紀錄。
- 後端讀取並維護每輪歷史，依序儲存使用者問題及模型完整回答；刷新網頁或重啟 Flask 後仍能繼續多輪聊天；下次傳送問題時，應重新讀取並依序傳入已儲存的歷史，而不是只在前端顯示舊訊息。瀏覽器不得自行傳入任意舊歷史，僅送交本輪問題。
- `Ollama` 送進模型的歷史角色為 `user` 與 `assistant`；只有必要的 `role`／`content` 內容參與模型請求，讓 `history.json` 可讀、可查。
- 若模型失敗、回覆空白、串流中斷、使用者中途離線，**不得保存那一輪的半成品**；完整成功後才一次寫入。使用簡單 `threading.Lock` 保護讀寫及「清除聊天」與對話的衝突，必要時用暫存檔 + 原子替換避免 JSON 被寫壞。
- 清除聊天必須清掉後端的 `history.json`（或寫成 `[]`），不能只是清畫面；目前對話仍在生成時應阻止或延後清除，避免互相覆寫。`.gitignore` 忽略 `history.json`、`.env`、虛擬環境及快取。

## 四、介面要大、簡單、真正串流

- 臺灣繁體中文、大字體，桌面聊天區寬約 `min(1200px, 94vw)`，訊息與輸入框字體至少 18px，標題 26–30px、按鈕至少 16px；手機自動縮排，不要出現橫向捲軸。
- 頁首是「Ollama 聊天室」，有清楚區分的使用者／AI 泡泡、`textarea` 輸入區、送出與清除聊天按鈕。`Enter` 送出、`Shift+Enter` 換行；送出時顯示「正在回答…」，避免重複送出。
- 畫面必須隨模型回傳的**真實文字片段**逐步更新，而非收到整篇回答後用計時器模擬；支援複製 AI 回覆。刷新頁面向後端取回歷史。
- 模型文字只能使用 DOM `textContent` 顯示，不能當作任意 HTML 執行；不要加入會載入第三方套件的 CDN。

## 五、Flask API 與前後端通訊

| 方法 | 路由 | 功能 |
| --- | --- | --- |
| GET | `/` | 聊天首頁 |
| GET | `/api/history` | 回傳後端 `history.json` 的對話 |
| POST | `/api/chat/stream` | 接收 `{"message":"問題"}` 並逐段回覆 |
| POST | `/api/clear` | 清除後端與前端歷史 |

- 串流用 **NDJSON**（每行一個 JSON）格式，請依序傳送 `{"type":"chunk","text":"..."}`，成功保存完整歷史後傳 `{"type":"done"}`；失敗傳 `{"type":"error","message":"易懂的原因"}`，不得寫入歷史。
- JavaScript 使用 `fetch()` + `ReadableStream` + `TextDecoder`，維護**跨 chunk 的逐行緩衝**，避免將半行 JSON 當完整訊息；只有收到 `done` 才算成功。串流中斷或沒有 `done` 時顯示錯誤並從後端重新載入歷史。
- 錯誤訊息不得顯示 API Key、環境變數、敏感內文或完整 traceback；要能區分常見的設定、網路、模型或額度問題。

## 六、Windows CMD：安裝一次，之後只用 `python app.py`

請把以下指令**原樣放進產出專案的 README，並在最後回覆中再顯示一次**；所有指令都在 Windows CMD 執行，不使用 Linux 指令，且不用 `python -m flask run`。第一次的 `pip` 安裝為必要前置步驟，並非每次啟動都要重做。

第一次在 Windows CMD 安裝套件（在解壓縮後的專案資料夾執行）：

```bat
cd ollama_flask
python -m pip install -r requirements.txt
python app.py
```

本機使用 Ollama 時，需先讓 Ollama 服務運作並備妥來源程式指定的模型；如果老師已提供 ngrok 遠端 Ollama，學生只需修改 `app.py` 上方 `OLLAMA_HOST`，不需在本機下載模型。下次開啟 CMD 並進入 `ollama_flask` 目錄後，**只要**：

```bat
python app.py
```

開啟 `http://127.0.0.1:5001`；按 `Ctrl+C` 停止。無法連線到 Ollama 或模型未下載時，Flask 仍應能啟動並顯示首頁，送出問題時提示清楚錯誤。

## 七、交付與檢查

- `requirements.txt` 只列實際需要的依賴；`README.md` 用簡單的 Windows CMD 指令，說明如何安裝、設定、啟動、測試、停止及排除錯誤。
- README 需包含：Windows CMD 安裝方式、確認 Ollama 服務已啟動、本機所需 `ollama pull` 指令（模型名稱從上傳程式讀取）、老師提供 ngrok API 根網址時如何修改 `OLLAMA_HOST`、`python app.py`、瀏覽 `http://127.0.0.1:5001`、以 Ctrl+C 結束，以及本機／遠端排錯。遠端已有模型時不要求學生在本機 pull。
- 在可以執行的環境中，檢查 Python 語法、Flask 路由與 HTML `fetch()` 路徑，並以模擬模型測試：兩輪上下文、成功後儲存、刷新恢復、清除、空回覆／失敗不儲存、NDJSON 正確斷行。
- 沒有可使用的真實 Ollama 模型服務時**不得假稱已實測真實模型**；請明列哪些為模擬測試、哪些未驗證。不要把 `.env`、金鑰、`history.json`、`.venv`、`__pycache__` 放進 ZIP。
- Python 原始碼以精簡、可讀、少依賴為原則。**每一行可執行的 Python 程式碼上方**都要用獨立的三個單引號註解區塊：先英文、後臺灣繁體中文，兩句簡明描述目的；註解區塊與上一段程式碼保持空行，不要為縮短行數寫複雜巢狀推導式。HTML／CSS／JavaScript 只需適量、真正有用的註解。

收到這兩份附件後，不需等待額外文字訊息或請使用者確認；請完成必要測試並輸出可下載的 `ollama_flask.zip`。

交付時，請在你的最後回覆明確列出：ZIP 下載連結、Windows CMD 的首次安裝／設定指令、`python app.py` 啟動指令與瀏覽網址、測試結果，以及**下一階段需在這段對話同時提供 `Excel_BM25_檢索增強Prompt.md` 與 `.xlsx`；如果漏傳 Excel，先提醒學生上傳後再進行第二階段**，不必重新上傳本階段的 Python 單輪程式。
