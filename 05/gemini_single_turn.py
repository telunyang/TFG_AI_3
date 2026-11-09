# Import tools for reading settings.
# 匯入讀取設定需要的套件。
import os
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load settings from gemini/.env.
# 讀取 gemini/.env 的 API 設定。
load_dotenv(Path(__file__).with_name(".env"))

# ===== Configuration =====
# ===== 設定區 =====
API_KEY = os.getenv("GEMINI_API_KEY")

# Create the Gemini API client.
# 建立 Gemini API 用戶端。
client = genai.Client(api_key=API_KEY)

# Build the configuration for one reply.
# 設定這一次回答的系統指令及生成參數。
config = types.GenerateContentConfig(
    system_instruction="你是一個知識淵博且樂於助人的 AI 助理。",
    temperature=1.0,
    top_k=64,
    top_p=0.95
)

# Send one question to Gemini.
# 傳送單輪問題給 Gemini。
response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="幸福的定義是什麼？",
    config=config,
)

# Print the response text.
# 顯示回覆文字。
print(response.text)
