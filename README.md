# 人工智慧技術應用實作班

從 `機器學習` 的資料處理與模型訓練出發，逐步探索 `文字分類、電腦視覺、大型語言模型、生成式 AI 與 AI Agent`，透過生活情境、互動圖解與實作流程，理解 AI 如何從資料中學習、產生結果，進一步協助完成任務。

本專案共有 7 個教學主題，每個主題均提供互動式 HTML 投影片，並安排概念操作與課堂檢核，協助建立從原理到應用、從結果到驗證的完整觀念。

## 課程目標

- 理解 AI 的基本流程：認識資料、特徵、模型訓練、推論與評估之間的關係。
- 掌握不同 AI 任務：區分預測、分類、分群、影像辨識及生成式應用。
- 理解現代 AI 技術：認識 BERT、LLM、影像生成與 AI Agent 的核心概念及使用情境。
- 培養實作與驗證能力：透過互動操作、案例分析與課堂檢核，學習判讀結果、發現限制並注意安全與責任。

## 課程大綱與教學主題

### 01｜機器學習與模型訓練

從一份資料表開始，理解模型如何學習並進行預測：

先認識樣本、特徵與標籤，以及缺漏值處理、標準化、One-Hot Encoding、訓練集與測試集；再透過迴歸、邏輯斯迴歸、正則化、PCA 與 K-means，了解模型訓練、效能評估和過度擬合等概念。

### 02｜資料預測與模型實作

不只要做出預測，還要知道模型何時會判斷錯誤：

從校園信箱分類案例理解混淆矩陣、Accuracy、Precision、Recall 與 F1-score，並比較 SVM、Kernel 與決策樹；接著學習資料切分、交叉驗證、Grid Search，以及 Bagging、Boosting 和隨機森林，練習公平比較與選擇模型。

### 03｜AI 分類模型應用

讓電腦理解文字，並將文字分到適當的類別：

以班群留言及園遊會資料為例，認識 Tokenizer、Embedding、Self-Attention、Transformer Encoder 與 BERT；進一步了解文字標註、模型微調、Batch、Epoch、Learning Rate、Loss，以及如何避免資料洩漏並評估文字分類成果。

### 04｜電腦視覺與影像辨識

從像素與色彩出發，探索 AI 如何看懂照片與影片：

先操作 RGB、灰階、解析度、亮度、對比、模糊與邊緣偵測等影像處理概念；再以 YOLO 介紹物件偵測、Bounding Box、正規化座標、IoU、NMS、資料標註、模型微調及影片追蹤。

### 05｜大型語言模型應用

理解聊天型 AI 如何產生文字，以及如何提出更清楚的需求：

介紹 Token、Context Window、提示詞設計、訊息角色、輸出格式與 Temperature 等生成參數；接著探討雲端與本機模型、API、多輪對話、對話記憶、聊天介面設計、Vibe Coding，以及提示詞注入與回答驗證。

### 06｜生成式 AI 實務應用

從文字描述出發，規劃圖片、音樂與影片作品：

先以校園海報認識文字生圖、雜訊逐步生成、Prompt、構圖、Seed、推論步數與 CFG；再透過活動配樂及短片規劃，理解節奏、音色、鏡頭運動、影格連續性與分鏡，並學習檢查作品品質及公開使用的注意事項。

### 07｜AI Agent

從遠端模型連線到實際操作，快速建置能使用工具的 AI Agent：

透過 VS Code 連接 Google Colab，在 Colab 安裝 Ollama、設定 Context Length，並使用 ngrok 建立模型 API 連線；接著從官方網站安裝 Windows／macOS 版 Hermes Desktop，透過自訂端點連接遠端模型，不需在本機啟動 Ollama。完成連線後，實作 Coding、Browser Automation 與 Computer Use，驗證程式執行、網頁操作及桌面控制成果；並延伸認識 Skills、動畫與有聲影片製作，以及常見錯誤排除。

## Conda 環境安裝

Anaconda 或 Minicoda

[https://www.anaconda.com/download/success](https://www.anaconda.com/download/success)

```bash
# 安裝環境
conda create -n ai python=3.13 ipykernel -y

# 啟用環境
conda activate ai

# 安裝套件
pip install -r requirements.txt
# 或
python -m pip install -r requirements.txt

# 取消啟用環境（回到上一個環境，或是 base 環境）
conda deactivate
```

未來若是要刪除 conda 環境

```bash
# 先回到上一個環境
conda deactivate

# 刪除 conda 環境
conda remove -n ai --all
```

## Colab + Ollama + ngrok 快速指令
```bash
# 安裝 Ollama
sudo apt-get install zstd
curl -fsSL https://ollama.com/install.sh | sh

# 設定環境變數
export OLLAMA_CONTEXT_LENGTH=65536
export OLLAMA_KEEP_ALIVE=-1
export OLLAMA_ORIGINS="*"

# 執行程式 (執行後，先等 3 秒左右，等待服務完全啟動)
nohup ollama serve > /tmp/ollama.log 2>&1 &

# 下載模型
ollama pull nemotron-3.5-bolt:e4b

# 測試模型
ollama run nemotron-3.5-bolt:e4b "(繁體中文) 你好~~~"

# 安裝 ngrok
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
  && echo "deb https://ngrok-agent.s3.amazonaws.com bookworm main" \
  | tee /etc/apt/sources.list.d/ngrok.list \
  && apt update \
  && apt install -y ngrok
  
# 設定 auth token (顯示輸入文字方塊，讓學生填寫)
ngrok config add-authtoken "<YOUR_NGROK_AUTHTOKEN>"

# (Optional) 建立 Traffic Policy 檔案 (可以寫入到 /content/ollama-ngrok.yaml 當中)
on_http_request:
  - actions:
      - type: add-headers
        config:
          headers:
            host: localhost
			
# 執行 ngrok，取得公開對外的 URL
ngrok http 11434 --traffic-policy-file /content/ollama-ngrok.yaml

# (Optional) 刪除 ngrok 服務
pkill ngrok

# 停止 ollama
ollama stop nemotron-3.5-bolt:e4b
pkill ollama
```