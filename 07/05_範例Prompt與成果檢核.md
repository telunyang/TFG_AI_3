# 05｜可直接複製給 Hermes 的 Prompt 與驗收規範

這份文件設計為 **無需先學程式碼**的操作練習。每項工作都要核對可見結果；不要只相信 Agent 說「已完成」。

## 教學任務一：測試 Agent 是否真的會使用工具

> 你是一位有權限限制的 AI Agent。任務限定在本機 `agent-lab` 資料夾。先列出此工作階段可用的模型、File、Terminal、Browser Automation 和 Computer Use 工具；說不確定的部分，不要猜測。接著只建立 `agent-lab/agent_test.txt`，內容是今天的日期與「AI Agent 實作成功」，並用讀檔工具檢查實際檔案內容。最後回報所使用的工具、檔案路徑、實際檢查結果，不可以只宣稱已完成。

**驗收：**檔案真的存在、檔案內容正確、工具呼叫有回傳。**注意**：模型可能不知道當地今天的日期，應以系統時間工具或本機命令取得，不可以憑模型記憶猜。

## 教學任務二：Browser Automation，不需要帳號

> 請先確認 Browser Automation 可用，再開啟 https://example.com。請確實讀取網頁標題、本文，並整理為三句繁體中文；附上你觀察到的實際網頁 URL 與工具結果。若你不能連線或瀏覽器尚未安裝，請把失敗的步驟寫清楚，不要用記憶編造。

**驗收：**有 browser tool 呼叫，且符合實際網頁文字。若提議使用 Browserbase 等雲端 API 且需要註冊，請改選本機 Chromium 方式。

## 教學任務三：Computer Use 操作桌面

> 請先使用 Computer Use 偵測可用的視窗與應用程式，只在本機測試環境操作。使用本機文字編輯器輸入一段含標題與三行清單的文字，保存至 `agent-lab/desktop-test.txt`，並再次讀取驗證結果。若缺少安裝、權限或圖形環境，請指出原因與需要我執行的步驟，不可以拿 `browser_navigate` 當成已完成桌面工具的證據。

**驗收：**Computer Use driver 通過 doctor，真正對本機應用操作，且檔案內容可再次檢查。

## 教學任務四：Skill 對有沒有裝的差別

> 請先檢查是否已安裝 motion-design 或 GSAP 的相關 Skill。先不用 Skill，規劃一段 5 秒、標題「從想法到成果」的三步驟動畫；接著讀取已裝的 Skill，再重新整理一次動畫設計。比較兩個版本在 Timing、Easing、節奏、可讀性上的差異。若已能生成 HTML，請只在 `agent-lab/motion-test` 輸出並提供預覽，不要對外上傳。

**驗收：**能說明 Skill 提供的是「流程／規範」，而不是 GPU 或網站權限。若 Skill 不存在，不能假裝已讀取其內容。

## 教學任務五：免費、有聲動畫（建議延伸活動）

> 請先檢查本機 Node.js、FFmpeg、Python、Remotion、edge-tts。目標是 12 秒、16:9 的繁體中文動態說明影片，主題為「如何規劃一趟輕鬆的週末旅行」，含三個場景、三句旁白。必須是本機生成動畫與本機 FFmpeg 渲染；語音可使用不需要 API Key 的 edge-tts，不能暗中使用需付費或要註冊的媒體 API。請輸出 `animation.mp4`、`narration.mp3`、`final_with_voice.mp4`，使用 ffprobe 確認最後檔案同時有 video 與 audio，並說明是否成功。若 TTS 失敗請停在靜音版並如實回報。不要自行登入或對外發布。

**驗收：**影片可播放、有可辨識人聲、音訊長度與畫面對齊、不使用需額外註冊的付費服務。

## 成果檢核表（每個任務通用）

| 問題 | 通過標準 |
|---|---|
| 真的有執行嗎？ | 有工具回傳或本機檔案／網頁內容可核對 |
| 用了正確的工具嗎？ | Browser、Computer Use、Terminal 分工正確 |
| 碰到失敗有說清楚嗎？ | 顯示錯誤，不宣稱不存在的成功 |
| 有遵守限制嗎？ | 未越權、未外傳資料、未暗中使用需要註冊的外部 API |
| 成品能驗收嗎？ | MP4 可播放、旁白存在、檔案路徑可找到 |
| T4 沒 OOM 嗎？ | Colab `nvidia-smi` 合理、模型能持續回應 |

## 常見問題

**Q：Hermes Desktop 為什麼設定了 ngrok 還不能控制我本機 Chrome？**

A：模型 endpoint 只讓 Hermes 取得 LLM 回答。要另外啟用 Browser Automation；若要控制已開啟的 Chrome，CLI 可使用 `/browser connect`，但 Desktop 的 Browser 介面與 CLI slash command 不要混淆。

**Q：Computer Use 需要安裝 Playwright 嗎？**

A：**不需要。** Hermes 官方 Computer Use 使用 `cua-driver`；Playwright 可能是 Browser/其他動畫 Skill 的依賴，但不是 Computer Use 的必備條件。

**Q：裝了 Remotion Skill 就能直接產生有人聲的影片嗎？**

A：不保證。Remotion 負責動畫渲染；旁白仍需 TTS 或錄音，再合成。先選免註冊的 TTS 來源，確認網路可用與服務限制。

**Q：為什麼不是一開始就用 30B 模型？**

A：T4 約 15 GB VRAM，模型量化權重之外還要放 Context 與工作緩衝。先讓 4B／9B 完成真實工具呼叫，驗證流程後再挑戰更大模型。

**Q：免費是否等於不用帳號、沒有期限？**

A：不等於。公開 GitHub 專案、本機開源工具可以免帳號使用；但 Colab、ngrok、雲端 API、雲端 TTS、服務用量及授權各自有不同條件。教材以既有 Colab/ngrok 連線與本機工具為前提，不承諾永久無限制的雲端免費服務。
