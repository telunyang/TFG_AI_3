# Read the API key from environment variables.
# 從環境變數讀取 API 金鑰。
import os

# Locate configuration files next to this script.
# 尋找放在程式旁的設定檔。
from pathlib import Path

# Read the local .env configuration.
# 讀取本機 .env 設定。
from dotenv import load_dotenv

# Use Google's official generative AI SDK.
# 使用 Google 官方生成式 AI SDK。
from google import genai

# Set the system instruction for this request.
# 設定本次請求的系統指令。
from google.genai import types

# Load the API key and model name from .env.
# 從 .env 載入 API 金鑰及模型名稱。
load_dotenv(Path(__file__).with_name(".env"))

# Select a supported Gemini API model.
# 選擇可用的 Gemini API 模型。
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Read the student's API key.
# 讀取學生的 API 金鑰。
API_KEY = os.getenv("GEMINI_API_KEY")

# Check that the API key is configured.
# 確認已經設定 API 金鑰。
if not API_KEY:
    # Explain which configuration is missing.
    # 說明缺少哪一項設定。
    raise ValueError("請先在 gemini/.env 設定 GEMINI_API_KEY。")

# Create the Gemini API client.
# 建立 Gemini API 用戶端。
client = genai.Client(api_key=API_KEY)

# Send one question with a system instruction.
# 連同系統指令，發送一個問題。
response = client.models.generate_content(
    # Pick the model to use.
    # 指定要使用的模型。
    model=MODEL_ID,
    # Set the student's question.
    # 設定學生的問題。
    contents="幸福的定義是什麼？",
    # Request a concise answer in Taiwan Traditional Chinese.
    # 要求使用臺灣繁體中文簡短回答。
    config=types.GenerateContentConfig(system_instruction="請用臺灣繁體中文，簡短回答。"),
)

# Display the answer returned by Gemini.
# 顯示 Gemini 回傳的回答。
print(response.text)
