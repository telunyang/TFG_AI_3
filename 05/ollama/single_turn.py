# Import environment-variable support.
# 匯入環境變數功能。
import os

# Locate the configuration file beside this script.
# 找出與程式放在同一資料夾的設定檔。
from pathlib import Path

# Load settings from the .env file.
# 讀取 .env 中的設定。
from dotenv import load_dotenv

# Connect to the Ollama server through its API.
# 透過 API 連接 Ollama 伺服器。
from ollama import Client

# Read the local configuration file.
# 讀取本機設定檔。
load_dotenv(Path(__file__).with_name(".env"))

# Set the remote ngrok URL or local Ollama endpoint.
# 設定遠端 ngrok 網址或本機 Ollama 端點。
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Choose a model already installed on the Ollama server.
# 選擇 Ollama 伺服器上已安裝的模型。
MODEL_ID = os.getenv("OLLAMA_MODEL", "gemma4:e2b")

# Give the assistant its overall response rule.
# 設定助理整體回答規則。
SYSTEM_PROMPT = "請用臺灣繁體中文，簡短回答。"

# Create the API client once.
# 建立一次 API 用戶端即可。
client = Client(host=OLLAMA_HOST, timeout=120, headers={"ngrok-skip-browser-warning": "true"})

# Prepare the message list.
# 準備對話訊息清單。
messages = []

# Add the assistant's instructions.
# 加入助理的指令。
messages.append({"role": "system", "content": SYSTEM_PROMPT})

# Add one question from the user.
# 加入一個使用者問題。
messages.append({"role": "user", "content": "幸福的定義是什麼？"})

# Send the single-turn request.
# 發送單輪對話請求。
response = client.chat(model=MODEL_ID, messages=messages)

# Display the model's answer.
# 顯示模型的回答。
print(response.message.content)
