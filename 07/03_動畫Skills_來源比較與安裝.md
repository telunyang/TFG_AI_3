# 03｜SKILL.md、動畫技能庫與實作選擇

## 先理解：Skill ≠ 生成模型 ≠ 操作權限

- **SKILL.md**：說明何時使用某套工作流程、如何操作、如何驗收。
- **Tool／依賴**：例如 Node.js、FFmpeg、Chromium、Playwright、Remotion、GSAP。
- **模型**：Colab T4 上 Ollama 生成程式與工具呼叫；模型本身不是影片編碼器。
- **聲音**：通常需要獨立 TTS 生成 MP3，再和動畫合併（見下一份文件）。

## 七項工具逐一核對

| 工具 / Skill | 官方或公開來源 | 實際用途 | 可純本機、免帳號？ | 單獨支援中文配音？ | 入門優先度 |
|---|---|---|---|---|---|
| **HyperFrames** | [heygen-com/hyperframes](https://github.com/heygen-com/hyperframes) | HTML 動畫、時間軸、渲染 MP4；也有音訊混合 | **本機渲染可以**；雲端與特定資產來源可能要帳號 | **否**，需附加 TTS 音訊 | 高 |
| **GSAP AI Skills** | [greensock/gsap-skills](https://github.com/greensock/gsap-skills) | 網頁動畫、Timeline、ScrollTrigger | 核心流程可以 | 否 | 高（網頁動效） |
| **Pixel2Motion** | [nolangz/pixel2motion](https://github.com/nolangz/pixel2motion) | Logo PNG/JPG → SVG → Logo 動畫 HTML／預覽 | 開源版本可；需 Python、Chromium、Playwright 等 | 否 | 中 |
| **Remotion Skills** | [remotion-dev/skills](https://github.com/remotion-dev/skills) | 用 React 實作影片、字幕、動畫、MP4 | 本機渲染可以；需 Node、瀏覽器、FFmpeg | 否，需 TTS | **最高**（有聲 MP4） |
| **video-shotcraft** | [Vincentwei1021/video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft) | 網頁或產品畫面 → 運鏡、鏡頭節奏、宣傳影片 | 基本 Remotion／程式素材可本機；特殊來源需另查 | 否；可有音效 | 中／進階 |
| **story-to-handdrawn-video** | [gnipbao/story-to-handdrawn-video](https://github.com/gnipbao/story-to-handdrawn-video) | 中文故事或既有圖片 → 手繪風格影片 | **輸入現成圖片**可避免另用付費圖片 API；文字生新圖片可能依賴額外服務 | **明確輸出靜音影片** | 中 |
| **motion-design-skill** | [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill) | 動態設計原則、Timing、Easing、轉場 | 是（知識型 Skill） | 否 | 高（品質輔助） |

**注意：**這七個不都是獨立「文字生影片 AI 模型」，也都不能保證只裝 SKILL.md 就產生有聲作品。以**Remotion／HyperFrames + 無 API Key 的 TTS + FFmpeg**最符合「可下載有聲 MP4」的要求。Story-to-handdrawn-video 官方就明確寫預設是靜音 H.264，要後製配音。

## 安裝 Hermes Skills 的基本方式

在本機 CLI（不是 Colab）操作：

```bash
# EN: Inspect a public skill and its instructions before installation.
# 繁中：安裝前先查看公開 Skill 與其操作說明。
hermes skills inspect heygen-com/hyperframes/skills/hyperframes

# EN: Install a reviewed skill from its GitHub directory.
# 繁中：從 GitHub 專案的指定目錄安裝已檢查的 Skill。
hermes skills install heygen-com/hyperframes/skills/hyperframes

# EN: List the skills currently available to Hermes.
# 繁中：列出 Hermes 已安裝的 Skills。
hermes skills list

# EN: Re-check installed skills for potentially unsafe instructions.
# 繁中：再次掃描已安裝 Skills 的安全風險。
hermes skills audit
```

> 路徑型安裝是 Hermes 支援的來源格式；**每個 GitHub 專案的實際檔案布局不同，安裝前用 `hermes skills inspect` 測試解析是否成功**。若某 Skill 在 GitHub 根目錄、含大量 `scripts/`、依賴外部 renderer 或無法經 Hermes Hub 安裝，請先複製 GitHub repository 到本機、讀取 README 再設定 Skill 路徑，不要只抓單一 `SKILL.md` 而漏掉執行腳本。

可以選擇測試以下候選（每次只安裝一個並檢查）：

```text
heygen-com/hyperframes/skills/hyperframes
greensock/gsap-skills/skills/gsap-core
remotion-dev/agent-plugin/skills/remotion-best-practices
LottieFiles/motion-design-skill/skills/motion-design
gnipbao/story-to-handdrawn-video/skill-package/story-to-handdrawn-video
```

`nolangz/pixel2motion` 和 `Vincentwei1021/video-shotcraft` 的 Skill 位於 repository 根目錄，且可能需要整個 repository 的 scripts/references。**先 clone 專案按 README 安裝**，比只下載 SKILL.md 可靠。這些不是我在 Hermes / Windows/macOS/Ubuntu 實機驗證過的 Hub 指令。

## 選擇最適合的第一次動手案例

| 目標 | 先用哪個 | 第一個成果 |
|---|---|---|
| 最快看見動畫結果 | GSAP Skills | `index.html` 可播放動畫 |
| 需要本機 MP4 | **Remotion** | `animation.mp4` |
| 影片不想寫 React、偏好 HTML | **HyperFrames** | `animation.mp4` |
| 一張 Logo 變動態標誌 | Pixel2Motion | `logo_motion.html` |
| 已有 3 張圖片、想變故事 | story-to-handdrawn-video | 靜音 `picture_silent.mp4`，後製配音 |
| 現有網頁轉宣傳短片 | video-shotcraft | 產品／網頁影片 |
| 希望所有動畫更順、更有節奏 | motion-design-skill | 協助修改動作與時間軸 |

## 一個實際可交給 Hermes 的測試 Prompt

> 請先列出已安裝的 Skills，確認是否有 `remotion-best-practices`。如果沒有，告訴我還需要安裝什麼，不要自行下載不明腳本。請只在 `agent-lab/animation-demo` 內，建立一段 8 秒、16:9 的繁體中文動態資訊圖影片，主題是「一杯咖啡從原豆到沖煮的三個步驟」。要求文字清楚、平滑轉場、附簡單標題；先給我預覽，經我確認後才輸出 MP4。若需要 TTS、FFmpeg 或 Node，先檢查既有安裝，再告訴我缺哪些依賴。

學習驗收：**能看見真的生成的 HTML／MP4**、知道依賴來源、沒有無提示的額外付費 API、沒有在錯誤發生時假稱成功。

## 安全檢查（必做）

Skill 可以含命令或對外服務說明；安裝前檢查 Repository、`SKILL.md`、`scripts`、其相依套件及授權。避免來源不明、要求上傳私人資料、下載執行未經確認腳本、要求開啟敏感憑證。`hermes skills inspect`、`hermes skills audit` 可協助，但**不能取代人工審查**。先在空白工作目錄操作，切勿讓 Skill 預設修改已有正式專案。

## 參考
- [Hermes Skills System](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md)
- [HyperFrames](https://github.com/heygen-com/hyperframes)
- [GSAP 官方 Skills](https://github.com/greensock/gsap-skills)
- [Remotion Agent Skills](https://github.com/remotion-dev/skills)
- [Pixel2Motion](https://github.com/nolangz/pixel2motion)
- [video-shotcraft](https://github.com/Vincentwei1021/video-shotcraft)
- [story-to-handdrawn-video](https://github.com/gnipbao/story-to-handdrawn-video)
- [LottieFiles motion-design-skill](https://github.com/LottieFiles/motion-design-skill)
