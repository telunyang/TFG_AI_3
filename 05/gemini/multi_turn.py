# Read configuration values.
# 讀取設定值。
import os

# Save multiple turns of conversation in JSON.
# 將多輪對話存成 JSON。
import json

# Locate local project files.
# 尋找專案中的本機檔案。
from pathlib import Path

# Load the Gemini API key from .env.
# 從 .env 載入 Gemini API 金鑰。
from dotenv import load_dotenv

# Connect to Google's Gemini API.
# 連接 Google Gemini API。
from google import genai

# Configure the Gemini system instruction.
# 設定 Gemini 的系統指令。
from google.genai import types

# Read configuration from this script's folder.
# 讀取程式所在資料夾中的設定。
load_dotenv(Path(__file__).with_name(".env"))

# Select a Gemini model supported by the API key.
# 選擇 API 金鑰可以使用的 Gemini 模型。
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Read the API key.
# 讀取 API 金鑰。
API_KEY = os.getenv("GEMINI_API_KEY")

# Keep the assistant's behavior consistent.
# 讓助理維持一致的回答規則。
SYSTEM_PROMPT = "請用臺灣繁體中文，簡短回答。"

# Save history beside the Python script.
# 將歷史對話儲存在 Python 程式旁。
HISTORY_FILE = Path(__file__).with_name("chat_history.json")

# Stop early if the API key has not been set.
# 尚未設定 API 金鑰時，提早停止程式。
if not API_KEY:
    # Describe the required environment value.
    # 說明需要設定的環境變數。
    raise ValueError("請先在 gemini/.env 設定 GEMINI_API_KEY。")

# Initialize Google's API client.
# 初始化 Google API 用戶端。
client = genai.Client(api_key=API_KEY)

# Start with an empty conversation history.
# 建立空白對話歷史。
history = []

# Restore previously saved messages when available.
# 如果有舊紀錄，就先還原。
if HISTORY_FILE.exists():
    # Read the history in Gemini's role-and-parts format.
    # 使用 Gemini 的 role 和 parts 格式讀取歷史。
    history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))

# Keep the system instruction separate from chat history.
# 將系統指令與聊天歷史分開。
config = types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)

# Resume the chat using earlier user/model messages.
# 使用之前的 user/model 訊息繼續聊天。
chat = client.chats.create(model=MODEL_ID, history=history, config=config)

# Explain the available student commands.
# 說明學生可以使用的操作指令。
print("輸入 exit 結束，輸入 clear 清除歷史。")

# Keep asking questions until the student exits.
# 持續接收問題，直到學生結束對話。
while True:
    # Read the next question.
    # 讀取下一個問題。
    question = input("你：").strip()

    # Stop when the student requests it.
    # 學生要求結束時停止。
    if question == "exit":
        # Leave the loop.
        # 離開對話迴圈。
        break

    # Clear stored messages when requested.
    # 收到清除指令時，刪除儲存的訊息。
    if question == "clear":
        # Reset the history list.
        # 重設歷史清單。
        history = []

        # Update the saved JSON file.
        # 更新儲存的 JSON 檔案。
        HISTORY_FILE.write_text("[]", encoding="utf-8")

        # Create a fresh chat without earlier context.
        # 建立沒有舊上下文的新對話。
        chat = client.chats.create(model=MODEL_ID, history=history, config=config)

        # Let the student know the history was cleared.
        # 告知學生歷史已清除。
        print("已清除對話紀錄。")

        # Wait for the next question.
        # 繼續等待下一個問題。
        continue

    # Skip empty questions.
    # 跳過空白問題。
    if not question:
        # Return to the input prompt.
        # 回到問題輸入處。
        continue

    # Handle a failed API call without saving a partial turn.
    # API 呼叫失敗時，不儲存不完整的對話。
    try:
        # Send the new message, reusing the chat's context.
        # 傳送新問題，沿用已有的聊天上下文。
        response = chat.send_message(question)

        # Read the assistant's answer.
        # 讀取助理的回答。
        answer = response.text
    # Catch request failures without printing the API key.
    # 捕捉請求錯誤，避免輸出 API 金鑰。
    except Exception as error:
        # Show a short error type for troubleshooting.
        # 顯示簡短錯誤類型，方便排查。
        print("API 執行失敗：", type(error).__name__)

        # Let the student retry their question.
        # 讓學生重新嘗試提問。
        continue

    # Save the user message in Gemini's native chat format.
    # 使用 Gemini 原生格式儲存使用者訊息。
    history.append({"role": "user", "parts": [{"text": question}]})

    # Save the model's corresponding answer.
    # 儲存模型對應的回答。
    history.append({"role": "model", "parts": [{"text": answer}]})

    # Persist the completed turn as readable JSON.
    # 將這一輪完成的對話寫成易讀的 JSON。
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

    # Display the answer in the terminal.
    # 在終端機顯示回答。
    print("AI：", answer)
