# Import tools for reading settings.
# 匯入讀取設定需要的套件。
import os
from pathlib import Path
from dotenv import load_dotenv
from ollama import Client

# Load settings from ollama/.env.
# 讀取 ollama/.env 的連線設定。
load_dotenv(Path(__file__).with_name(".env"))

# Connect to the local or remote Ollama server.
# 連線至本機或遠端 Ollama 伺服器。
client = Client(
    host="http://localhost:11434", # 或整合 ngrok，取得 URL: https://ngrok給你的子網域名稱.ngrok-free.app
    timeout=120
)

# Send one question with a system instruction and generation options.
# 傳送一個問題，並套用系統指令和生成參數。
response = client.chat(
    model="gemma4:e2b",
    messages=[
        {"role": "system", "content": "你是一個知識淵博且樂於助人的 AI 助理。"},
        {"role": "user", "content": "幸福的定義是什麼？"},
    ],
    keep_alive="1h",
    think=False,
    options={
        "temperature": 1.0,
        "top_k": 64,
        "top_p": 0.95
    },
)

# Print the model's reply.
# 顯示模型的回答。
print(response.message.content)
