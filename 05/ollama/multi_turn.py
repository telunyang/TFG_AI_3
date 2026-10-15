# Read configuration values.
# 讀取設定值。
import os

# Save conversation history as JSON.
# 以 JSON 儲存對話歷史。
import json

# Find files relative to this Python script.
# 以目前的 Python 程式位置尋找檔案。
from pathlib import Path

# Read configuration from .env.
# 讀取 .env 設定。
from dotenv import load_dotenv

# Connect to Ollama's chat API.
# 連接 Ollama 聊天 API。
from ollama import Client

# Load the connection settings.
# 載入連線設定。
load_dotenv(Path(__file__).with_name(".env"))

# Read the Ollama endpoint.
# 讀取 Ollama 端點。
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# Read the model identifier.
# 讀取模型 ID。
MODEL_ID = os.getenv("OLLAMA_MODEL", "gemma4:e2b")

# Set the assistant's overall behavior.
# 設定助理整體行為。
SYSTEM_PROMPT = "請用臺灣繁體中文，簡短回答。"

# Save chat history next to this script.
# 將對話歷史存放於程式所在資料夾。
HISTORY_FILE = Path(__file__).with_name("chat_history.json")

# Create a reusable Ollama client.
# 建立可重複使用的 Ollama 用戶端。
client = Client(host=OLLAMA_HOST, timeout=120, headers={"ngrok-skip-browser-warning": "true"})

# Start with an empty history.
# 先建立空白歷史紀錄。
history = []

# Resume an existing conversation when available.
# 有舊紀錄時，接續之前的對話。
if HISTORY_FILE.exists():
    # Decode the saved JSON messages.
    # 將 JSON 紀錄讀回訊息清單。
    history = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))

# Explain how to control the conversation.
# 提示對話的操作指令。
print("輸入 exit 結束，輸入 clear 清除歷史。")

# Repeat until the student chooses to exit.
# 持續對話，直到學生選擇結束。
while True:
    # Read one message from the student.
    # 讀取學生輸入的一則訊息。
    question = input("你：").strip()

    # Stop the chat on request.
    # 收到結束指令時離開。
    if question == "exit":
        # End the conversation loop.
        # 結束對話迴圈。
        break

    # Remove old messages when requested.
    # 收到清除指令時刪除舊紀錄。
    if question == "clear":
        # Reset the in-memory conversation.
        # 清空記憶體中的對話。
        history = []

        # Persist the empty history immediately.
        # 立即將空紀錄寫入檔案。
        HISTORY_FILE.write_text("[]", encoding="utf-8")

        # Confirm that the conversation was cleared.
        # 提示對話紀錄已清除。
        print("已清除對話紀錄。")

        # Wait for the next student message.
        # 等待下一則學生訊息。
        continue

    # Ignore empty input.
    # 忽略空白輸入。
    if not question:
        # Ask for another message.
        # 重新等待輸入。
        continue

    # Give the model its overall instructions.
    # 提供模型整體回答規則。
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Include all earlier turns for context.
    # 附上先前對話，保留上下文。
    messages.extend(history)

    # Include the latest student question.
    # 加入學生最新的問題。
    messages.append({"role": "user", "content": question})

    # Handle temporary API failures without saving a broken turn.
    # API 暫時失敗時，不儲存不完整的對話。
    try:
        # Generate the assistant's next answer.
        # 產生助理這一輪的回答。
        response = client.chat(model=MODEL_ID, messages=messages)

        # Keep only the assistant's answer text.
        # 只保留助理的回答文字。
        answer = response.message.content
        
    # Catch connection or server errors for this request.
    # 捕捉本輪的連線或伺服器錯誤。
    except Exception as error:
        # Report the error without exposing configuration secrets.
        # 顯示錯誤，但不輸出設定中的機密資訊。
        print("連線或模型執行失敗：", type(error).__name__)

        # Retry with the next input.
        # 等待下一次輸入再重試。
        continue

    # Add the successful user message to the history.
    # 將成功完成的使用者訊息加入歷史。
    history.append({"role": "user", "content": question})

    # Save the matching assistant answer.
    # 儲存對應的助理回答。
    history.append({"role": "assistant", "content": answer})

    # Write the full history to JSON after each turn.
    # 每輪結束後，將完整歷史寫入 JSON。
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

    # Show the answer to the student.
    # 向學生顯示回答。
    print("AI：", answer)
