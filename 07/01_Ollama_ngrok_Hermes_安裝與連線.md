# 01｜本機 Ollama + ngrok 遠端模型 + Hermes Desktop

## A. 一次確認三種網址，避免設定錯誤

| 服務 | 正確的 URL 用途 | 例如 |
|---|---|---|
| Ollama 原生 API | `GET /api/tags`、`POST /api/chat` | `https://YOUR-NGROK.ngrok-free.app/api/tags` |
| Ollama OpenAI 相容 API | Hermes **Custom Endpoints** | `https://YOUR-NGROK.ngrok-free.app/v1` |
| Hermes Gateway | Hermes Desktop 連到另一台 Hermes 後端 | **本課不用，也不要填 Ollama URL** |

**先將 `https://YOUR-NGROK.ngrok-free.app` 換成實際的 URL。** 建議以瀏覽器以外的 HTTP 工具測試，不要因 ngrok 網頁提示就以為 Ollama API 正常。

## B. 測試 Colab Ollama 服務（在本機執行）

macOS / Ubuntu / Windows PowerShell（新版 Windows 通常有 `curl.exe`；Windows 請用 `curl.exe` 避免 PowerShell 舊版別名）：

```bash
# EN: Check the remote Ollama model list without sending any file.
# 繁中：測試遠端 Ollama 是否可列出已安裝模型，不上傳檔案。
curl -i -H "ngrok-skip-browser-warning: 1" "https://YOUR-NGROK.ngrok-free.app/api/tags"
```

Windows PowerShell 如果 `curl` 指向 `Invoke-WebRequest`，改用 `curl.exe`。應該看到 JSON 與 `models`；如果回傳 HTML，通常是 ngrok 提示頁、身份驗證或隧道設定問題。**Hermes 自訂模型端點不一定能加入 `ngrok-skip-browser-warning` 標頭**；若只有加了該標頭才可使用，請先調整 ngrok 受控入口，使標準 JSON API 客戶端可以正常呼叫，勿把 ngrok 提示頁誤當模型回答。

再測試 OpenAI 相容的 `/v1/models`：

```bash
# EN: Verify that the OpenAI-compatible Ollama API is reachable.
# 繁中：確認 Hermes 將使用的 OpenAI 相容 API 可以存取。
curl -H "ngrok-skip-browser-warning: 1" "https://YOUR-NGROK.ngrok-free.app/v1/models"
```

> `/v1/models` 成功並不足以驗證 Tool Calling；還要在 Hermes 真正完成工具呼叫測試。Ollama 的 OpenAI 相容層只支援 OpenAI API 的一部分。

## C. 本機是否需要安裝 Ollama？

**只想用 Hermes Desktop 連 Colab：不需要安裝本機 Ollama。** Hermes 可以直接將請求送到遠端模型端點。

**另外想在本機使用 `ollama list`、`ollama run`：**到 [Ollama 官方下載](https://ollama.com/download) 安裝。不要在本機另開一份大模型；把 **Ollama CLI 的 `OLLAMA_HOST` 設成遠端 URL**。

macOS / Ubuntu 的單次終端工作階段：

```bash
# EN: Point the local Ollama CLI at the remote Colab API endpoint.
# 繁中：讓本機 Ollama CLI 連線到 Colab 遠端 API。
export OLLAMA_HOST="https://YOUR-NGROK.ngrok-free.app"

# EN: List models held by the remote Ollama server.
# 繁中：列出遠端伺服器已安裝的模型。
ollama list

# EN: Chat with a model that already exists on the remote server.
# 繁中：使用遠端已下載的模型對話。
ollama run qwen3.5:4b
```

Windows PowerShell 單次工作階段：

```powershell
# EN: Redirect Ollama CLI calls to the Colab tunnel for this shell only.
# 繁中：只在目前 PowerShell 工作階段連到 Colab 隧道。
$env:OLLAMA_HOST = "https://YOUR-NGROK.ngrok-free.app"

# EN: Confirm the remote model inventory.
# 繁中：確認遠端模型清單。
ollama list

# EN: Start a conversation using the remote model.
# 繁中：使用遠端模型開始對話。
ollama run qwen3.5:4b
```

使用者若同時啟動本機 Ollama 背景服務，不會自動讓它變成遠端推論代理。`OLLAMA_HOST` 是**指定 Ollama CLI/API 連線位址**的常見用法；設定是否被 Ollama 桌面 UI 沿用，取決於當前版本，請以 `ollama list` 的實際結果為準。若有問題可直接略過本機 Ollama、改從 Hermes 連線。

## D. 安裝 Hermes Desktop

- Windows／macOS：從 [官方下載頁](https://hermes-agent.nousresearch.com/docs/) 下載 Hermes Desktop Installer；首次開啟依指示安裝或更新 Hermes Agent runtime。
- Ubuntu：先依 [官方安裝指南](https://hermes-agent.nousresearch.com/docs/) 安裝 Hermes CLI。Linux 桌面包的可用性與包裝方式依發行版本而定；若沒有對應 Desktop 安裝器，先用 `hermes` CLI 操作即可。
- 有 CLI 時，可執行 `hermes --version`、`hermes tools --summary` 檢查。
- **這個情境不需要 `hermes setup --portal`，因為模型不是透過 Nous Portal。** 某些線上工具若需要 Portal 或第三方帳號則不在本課範圍。

## E. Hermes Desktop 中設定遠端模型

1. 開啟 **Settings → Providers → Custom Endpoints**（版本介面可能微調）。
2. 新增自訂端點，Base URL 輸入 `https://YOUR-NGROK.ngrok-free.app/v1`。
3. API Mode 設為 **Chat Completions**；API Key 依版本需求可留空，若 UI 強制填值，可用 `ollama` 佔位字串。**若你的 ngrok 入口已設保護驗證，不能使用假金鑰來取代真正的驗證機制。**
4. 模型名稱填 Colab 的 `ollama list` 實際輸出的名稱，例如 `qwen3.5:4b`。
5. 執行 UI 的 **Test**，再將模型設為目前使用的模型。
6. 問：「請用一句話回答你目前正在使用哪個模型；如果不知道，請說不知道。」**模型自報名稱不一定可靠，應以 Hermes 設定與 Ollama 日誌驗證。**

也可在 Hermes CLI 用互動命令 `hermes model` → `Custom endpoint` 填入同樣的 base URL／模型 ID。不要把 `https://.../v1` 設成 ngrok 對外的反向代理 URL（ngrok 入口仍應指向 Colab Ollama HTTP port，而不是變更 Ollama server 的路由）。

## F. ngrok 安全與故障排查

| 現象 | 優先檢查 |
|---|---|
| 404 | 是否多加 `/api`、`/v1` 或代理路徑錯誤 |
| 502 / 連不上 | Colab 已中斷、Ollama 未啟動、ngrok 隧道過期 |
| 401 / 403 | ngrok 入口驗證、權限、額外要求的標頭 |
| JSON 解析失敗 | 實際回傳的是 ngrok 提示頁 HTML |
| Hermes 有回答但不會用工具 | 模型沒有正確 Tool Calling、工具沒啟用、Context 太小 |
| 推論極慢／OOM | T4 VRAM、Context、同時載入模型數量與 CPU offload |

**安全提醒：**Ollama 的原生 API 預設不是具備完整使用者身份驗證的多租戶服務；直接將 ngrok URL 分享給全班可能讓任何持有網址的人使用你的 GPU，甚至存取 API 其他功能。應使用 ngrok 的受控存取機制、限制流量，或只由授課電腦統一代理；避免把公開 URL 當成安全憑證。

### 參考
- [Hermes Custom / Ollama endpoints](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/integrations/providers.md)
- [Hermes Desktop providers UI](https://hermes-agent.nousresearch.com/docs/user-guide/desktop)
- [Ollama OpenAI compatibility](https://github.com/ollama/ollama/blob/main/docs/api/openai-compatibility.mdx)
